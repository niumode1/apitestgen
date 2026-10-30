"""Shared API dependencies."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.models.spec import OpenAPISpec
from app.models.endpoint import APIEndpoint
from app.models.testcase import TestCase
from app.models.execution import TestExecution
from app.models.report import DefectReport
from app.models.llm import LLMProvider
from app.schemas.common import PaginationParams


# ── Database ────────────────────────────────────────────────────

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yields DB session."""
    async for session in get_db():
        yield session


# ── Pagination ───────────────────────────────────────────────────

async def pagination(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


# ── Resource existence checks ────────────────────────────────────

async def get_project_or_404(
    project_id: str,
    db: AsyncSession = Depends(get_session),
) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


async def get_spec_or_404(
    spec_id: str,
    db: AsyncSession = Depends(get_session),
) -> OpenAPISpec:
    result = await db.execute(select(OpenAPISpec).where(OpenAPISpec.id == spec_id))
    spec = result.scalar_one_or_none()
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Spec {spec_id} not found")
    return spec


async def get_endpoint_or_404(
    endpoint_id: str,
    db: AsyncSession = Depends(get_session),
) -> APIEndpoint:
    result = await db.execute(select(APIEndpoint).where(APIEndpoint.id == endpoint_id))
    ep = result.scalar_one_or_none()
    if ep is None:
        raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")
    return ep


async def get_testcase_or_404(
    testcase_id: str,
    db: AsyncSession = Depends(get_session),
) -> TestCase:
    result = await db.execute(select(TestCase).where(TestCase.id == testcase_id))
    tc = result.scalar_one_or_none()
    if tc is None:
        raise HTTPException(status_code=404, detail=f"TestCase {testcase_id} not found")
    return tc


async def get_execution_or_404(
    execution_id: str,
    db: AsyncSession = Depends(get_session),
) -> TestExecution:
    result = await db.execute(select(TestExecution).where(TestExecution.id == execution_id))
    ex = result.scalar_one_or_none()
    if ex is None:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    return ex


async def get_report_or_404(
    report_id: str,
    db: AsyncSession = Depends(get_session),
) -> DefectReport:
    result = await db.execute(select(DefectReport).where(DefectReport.id == report_id))
    rp = result.scalar_one_or_none()
    if rp is None:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return rp


async def get_llm_provider_or_404(
    provider_id: str,
    db: AsyncSession = Depends(get_session),
) -> LLMProvider:
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    prov = result.scalar_one_or_none()
    if prov is None:
        raise HTTPException(status_code=404, detail=f"LLM Provider {provider_id} not found")
    return prov
