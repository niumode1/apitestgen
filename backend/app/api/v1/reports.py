"""Defect Report endpoints — generate, list, download."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_execution_or_404, get_project_or_404, get_report_or_404, get_session
from app.models.report import DefectReport
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.report import ReportBrief, ReportGenerateRequest, ReportResponse
from app.services.report_service import generate_report
from app.utils.logger import logger

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ReportBrief])
async def list_reports(
    project_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_session),
):
    """List reports for a project."""
    _ = await get_project_or_404(project_id, db)

    query = select(DefectReport).where(DefectReport.project_id == project_id)
    count_q = select(func.count(DefectReport.id)).where(DefectReport.project_id == project_id)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(DefectReport.created_at)).offset(offset).limit(page_size)
    )
    reports = result.scalars().all()

    items = [
        ReportBrief(
            id=r.id, title=r.title, format=r.format.value,
            failed_count=r.failed_count, error_count=r.error_count,
            total_count=r.total_count, pass_rate=r.pass_rate,
            created_at=r.created_at,
        )
        for r in reports
    ]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    project_id: str,
    report_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get report detail (includes full markdown content)."""
    r = await get_report_or_404(report_id, db)
    return ReportResponse(
        id=r.id, execution_id=r.execution_id, project_id=r.project_id,
        title=r.title, summary=r.summary, format=r.format.value,
        content=r.content, file_path=r.file_path,
        failed_count=r.failed_count, error_count=r.error_count,
        total_count=r.total_count, pass_rate=r.pass_rate,
        created_at=r.created_at, updated_at=r.updated_at,
    )


@router.get("/{report_id}/download")
async def download_report(
    project_id: str,
    report_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Download report file."""
    r = await get_report_or_404(report_id, db)

    if not r.file_path or not Path(r.file_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    media_types = {
        "markdown": "text/markdown",
        "html": "text/html",
        "pdf": "application/pdf",
    }

    return FileResponse(
        path=r.file_path,
        media_type=media_types.get(r.format.value, "text/plain"),
        filename=f"report.{r.format.value}",
    )


@router.delete("/{report_id}", response_model=MessageResponse)
async def delete_report(
    project_id: str,
    report_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a report."""
    r = await get_report_or_404(report_id, db)
    await db.delete(r)
    await db.commit()
    return MessageResponse(message=f"Report '{r.title}' deleted")
