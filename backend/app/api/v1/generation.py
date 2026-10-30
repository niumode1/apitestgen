"""Test Generation endpoints — async background generation with polling."""

import asyncio
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_spec_or_404
from app.events import EventBus
from app.models.llm import LLMProvider as LLMProviderModel
from app.services.llm.agents.orchestrator import (
    AgentOrchestrator,
    write_endpoint_test_files,
)
from app.services.llm.provider import LLMProviderFactory
from app.utils.logger import logger

router = APIRouter()

# In-memory store for generation tasks (Phase 3: persist to DB)
_generation_store: dict[str, dict] = {}


class GenerationTriggerRequest(BaseModel):
    endpoint_ids: Optional[list[str]] = Field(default=None)
    strategy: str = Field(default="positive_only", pattern="^(all|positive_only|negative_only|boundary_only|security_only|schema_only)$")
    max_testcases_per_endpoint: int = Field(default=5, ge=1, le=20)
    review_enabled: bool = Field(default=False)
    llm_provider_id: Optional[str] = Field(default=None)


@router.post("/generate")
async def generate_tests(
    spec_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    body: Optional[GenerationTriggerRequest] = None,
    db: AsyncSession = Depends(get_session),
):
    """Trigger async test generation. Returns immediately with a task ID."""
    spec = await get_spec_or_404(spec_id, db)

    if body is None:
        body = GenerationTriggerRequest()

    # Resolve LLM provider
    if body.llm_provider_id:
        result = await db.execute(
            select(LLMProviderModel).where(LLMProviderModel.id == body.llm_provider_id)
        )
        provider_record = result.scalar_one_or_none()
        if not provider_record:
            raise HTTPException(status_code=404, detail="LLM provider not found")
        try:
            provider = LLMProviderFactory.create_from_model(provider_record)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to create LLM provider: {e}")
    else:
        # Try DB first, then env
        db_result = await db.execute(
            select(LLMProviderModel).where(LLMProviderModel.is_active == True)
        )
        provider_record = db_result.scalars().first()
        if provider_record:
            provider = LLMProviderFactory.create_from_model(provider_record)
        else:
            try:
                provider = LLMProviderFactory.create_default()
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail="No LLM provider configured. Add one in LLM Settings.",
                )

    generation_id = str(uuid4())
    event_bus: Optional[EventBus] = getattr(request.app.state, "event_bus", None)

    # Initialize task status
    _generation_store[generation_id] = {
        "generation_id": generation_id,
        "spec_id": spec_id,
        "status": "pending",
        "endpoints_processed": 0,
        "total_testcases_generated": 0,
        "by_category": {},
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "errors": [],
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
    }

    # Schedule background task
    background_tasks.add_task(
        _run_generation,
        generation_id=generation_id,
        spec_id=spec_id,
        project_id=spec.project_id,
        endpoint_ids=body.endpoint_ids,
        strategy=body.strategy,
        max_testcases_per_endpoint=body.max_testcases_per_endpoint,
        review_enabled=body.review_enabled,
        provider=provider,
        event_bus=event_bus,
    )

    return {
        "generation_id": generation_id,
        "status": "pending",
        "message": f"Generation started for spec {spec_id}",
    }


@router.get("/generations/{generation_id}/status")
async def get_generation_status(generation_id: str):
    """Poll generation progress."""
    task = _generation_store.get(generation_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Generation task not found")
    return task


async def _run_generation(
    generation_id: str,
    spec_id: str,
    project_id: str,
    endpoint_ids: Optional[list[str]],
    strategy: str,
    max_testcases_per_endpoint: int,
    review_enabled: bool,
    provider,
    event_bus: Optional[EventBus],
):
    """Background task: runs the orchestrator and updates the store."""
    from app.database import AsyncSessionLocal

    store = _generation_store[generation_id]
    store["status"] = "running"

    async with AsyncSessionLocal() as db:
        try:
            orchestrator = AgentOrchestrator(
                provider=provider,
                db=db,
                event_bus=event_bus,
            )

            async def progress_cb(status, endpoint, idx, total, tests):
                store["endpoints_processed"] = idx
                store["total_testcases_generated"] = tests

            summary = await orchestrator.generate_for_spec(
                spec_id=spec_id,
                endpoint_ids=endpoint_ids,
                strategy=strategy,
                max_testcases_per_endpoint=max_testcases_per_endpoint,
                review_enabled=review_enabled,
                progress_callback=progress_cb,
            )

            # Write test files
            await write_endpoint_test_files(db, project_id, spec_id)

            store.update({
                "status": "completed",
                "endpoints_processed": summary.get("endpoints_processed", 0),
                "total_testcases_generated": summary.get("total_testcases_generated", 0),
                "by_category": summary.get("by_category", {}),
                "total_prompt_tokens": summary.get("total_prompt_tokens", 0),
                "total_completion_tokens": summary.get("total_completion_tokens", 0),
                "errors": summary.get("errors", []),
                "completed_at": datetime.utcnow().isoformat(),
            })

        except Exception as e:
            logger.error(f"Generation {generation_id} failed: {e}")
            store["status"] = "failed"
            store["errors"].append(str(e))
