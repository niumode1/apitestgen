"""Test Execution endpoints — run tests and view results."""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_execution_or_404, get_project_or_404, get_session
from app.events import EventBus, EventType, ExecutionEvent
from app.models.execution import TestExecution, TestResult
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.execution import (
    ExecutionBrief,
    ExecutionRequest,
    ExecutionResponse,
    TestResultResponse,
)
from app.services.executor_service import run_test_execution
from app.utils.logger import logger

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ExecutionBrief])
async def list_executions(
    project_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_session),
):
    """List test executions for a project."""
    _ = await get_project_or_404(project_id, db)

    query = select(TestExecution).where(TestExecution.project_id == project_id)
    count_q = select(func.count(TestExecution.id)).where(TestExecution.project_id == project_id)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(TestExecution.created_at)).offset(offset).limit(page_size)
    )
    executions = result.scalars().all()

    items = [
        ExecutionBrief(
            id=e.id, name=e.name, status=e.status.value,
            trigger=e.trigger.value, total_tests=e.total_tests,
            passed=e.passed, failed=e.failed, errors=e.errors,
            pass_rate=e.pass_rate, duration_ms=e.duration_ms,
            started_at=e.started_at, completed_at=e.completed_at,
        )
        for e in executions
    ]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


class StartExecutionBody(BaseModel):
    spec_id: str | None = Field(default=None)
    testcase_ids: list[str] | None = Field(default=None)
    name: str | None = Field(default=None)
    environment: dict = Field(default_factory=dict)


@router.post("", status_code=201)
async def start_execution(
    project_id: str,
    request: Request,
    body: StartExecutionBody | None = None,
    db: AsyncSession = Depends(get_session),
    background_tasks: BackgroundTasks = None,
):
    """Start a test execution run."""
    _ = await get_project_or_404(project_id, db)

    if body is None:
        body = StartExecutionBody()

    event_bus: EventBus | None = getattr(request.app.state, "event_bus", None)

    # Run in background
    background_tasks.add_task(
        run_test_execution,
        project_id=project_id,
        event_bus=event_bus,
        spec_id=body.spec_id,
        environment=body.environment,
        name=body.name,
    )

    return {"message": "Execution started", "status": "running"}


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    project_id: str,
    execution_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Cancel a running execution."""
    from app.models.execution import ExecutionStatus
    e = await get_execution_or_404(execution_id, db)
    if e.status == ExecutionStatus.RUNNING:
        e.status = ExecutionStatus.CANCELLED
        e.completed_at = datetime.utcnow()
        await db.commit()
    return {"message": "Cancelled", "status": e.status.value}


@router.post("/{execution_id}/reports")
async def create_report_for_execution(
    project_id: str,
    execution_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Generate a defect report from this execution."""
    from app.services.report_service import generate_report
    from app.schemas.report import ReportResponse

    _ = await get_execution_or_404(execution_id, db)

    try:
        report = await generate_report(db=db, execution_id=execution_id, format="markdown")
        return ReportResponse(
            id=report.id, execution_id=report.execution_id,
            project_id=report.project_id, title=report.title,
            summary=report.summary, format=report.format.value,
            content=report.content, file_path=report.file_path,
            failed_count=report.failed_count, error_count=report.error_count,
            total_count=report.total_count, pass_rate=report.pass_rate,
            created_at=report.created_at, updated_at=report.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    project_id: str,
    execution_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get execution detail."""
    e = await get_execution_or_404(execution_id, db)
    return ExecutionResponse(
        id=e.id, project_id=e.project_id, spec_id=e.spec_id, name=e.name,
        status=e.status.value, trigger=e.trigger.value,
        total_tests=e.total_tests, passed=e.passed, failed=e.failed,
        errors=e.errors, skipped=e.skipped, pass_rate=e.pass_rate,
        duration_ms=e.duration_ms, environment=e.environment or {},
        started_at=e.started_at, completed_at=e.completed_at,
        created_at=e.created_at, updated_at=e.updated_at,
    )


@router.get("/{execution_id}/results", response_model=PaginatedResponse[TestResultResponse])
async def get_execution_results(
    project_id: str,
    execution_id: str,
    status: str = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    """Get test results for an execution."""
    _ = await get_execution_or_404(execution_id, db)

    query = select(TestResult).where(TestResult.execution_id == execution_id)
    count_q = select(func.count(TestResult.id)).where(TestResult.execution_id == execution_id)

    if status:
        query = query.where(TestResult.status == status)
        count_q = count_q.where(TestResult.status == status)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(TestResult.recorded_at.desc()).offset(offset).limit(page_size)
    )
    results = result.scalars().all()

    items = [
        TestResultResponse(
            id=r.id, execution_id=r.execution_id, testcase_id=r.testcase_id,
            test_name=r.test_name, status=r.status.value, duration_ms=r.duration_ms,
            error_message=r.error_message, traceback=r.traceback,
            captured_stdout=r.captured_stdout, captured_stderr=r.captured_stderr,
            recorded_at=r.recorded_at,
        )
        for r in results
    ]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


# ── WebSocket for live log streaming ──

router_ws = APIRouter()


@router_ws.websocket("/execution/{execution_id}")
async def stream_execution(websocket: WebSocket, execution_id: str):
    """WebSocket endpoint for real-time execution log streaming."""
    await websocket.accept()

    # Access the app's event bus
    app = websocket.scope.get("app")
    event_bus: EventBus | None = getattr(app.state, "event_bus", None) if app else None

    if not event_bus:
        await websocket.send_json({"error": "Event bus not available"})
        await websocket.close()
        return

    queue = await event_bus.subscribe(execution_id)

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
                continue

            if event is None:  # End signal
                break

            await websocket.send_json({
                "type": event.event_type.value,
                "payload": event.payload,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            })
    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected for execution {execution_id}")
    finally:
        await event_bus.unsubscribe(execution_id, queue)
