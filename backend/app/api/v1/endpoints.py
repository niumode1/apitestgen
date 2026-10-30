"""API Endpoint listing and detail."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_endpoint_or_404, get_session, get_spec_or_404
from app.models.endpoint import APIEndpoint, HTTPMethod
from app.models.testcase import TestCase
from app.schemas.common import PaginatedResponse
from app.schemas.endpoint import EndpointBrief, EndpointFilter, EndpointResponse, EndpointSummary

router = APIRouter()


@router.get("", response_model=PaginatedResponse[EndpointBrief])
async def list_endpoints(
    spec_id: str,
    method: str = Query(default=None, description="Filter by HTTP method"),
    tag: str = Query(default=None, description="Filter by tag"),
    search: str = Query(default=None, description="Search path/summary/operation_id"),
    deprecated: bool = Query(default=None, description="Filter deprecated"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
):
    """List endpoints for a spec with optional filters."""
    await get_spec_or_404(spec_id, db)

    query = select(APIEndpoint).where(APIEndpoint.spec_id == spec_id)
    count_q = select(func.count(APIEndpoint.id)).where(APIEndpoint.spec_id == spec_id)

    if method:
        query = query.where(APIEndpoint.method == method.upper())
        count_q = count_q.where(APIEndpoint.method == method.upper())
    if deprecated is not None:
        query = query.where(APIEndpoint.deprecated == deprecated)
        count_q = count_q.where(APIEndpoint.deprecated == deprecated)
    if search:
        search_filter = (
            APIEndpoint.path.ilike(f"%{search}%") |
            APIEndpoint.summary.ilike(f"%{search}%") |
            APIEndpoint.operation_id.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_q = count_q.where(search_filter)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(APIEndpoint.path, APIEndpoint.method).offset(offset).limit(page_size))
    endpoints = result.scalars().all()

    # Filter by tag in Python (SQLite JSON doesn't support array contains well)
    if tag:
        endpoints = [ep for ep in endpoints if tag in (ep.tags or [])]
        total = len(endpoints)

    items = []
    for ep in endpoints:
        tc_count = (await db.execute(
            select(func.count(TestCase.id)).where(TestCase.endpoint_id == ep.id)
        )).scalar() or 0
        items.append(EndpointBrief(
            id=ep.id,
            path=ep.path,
            method=ep.method.value,
            summary=ep.summary,
            tags=ep.tags or [],
            deprecated=ep.deprecated,
            analyzed_at=ep.analyzed_at,
            testcase_count=tc_count,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/summary", response_model=EndpointSummary)
async def get_endpoints_summary(
    spec_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get summary statistics for endpoints in a spec."""
    await get_spec_or_404(spec_id, db)

    result = await db.execute(
        select(APIEndpoint).where(APIEndpoint.spec_id == spec_id)
    )
    eps = result.scalars().all()

    by_method: dict[str, int] = {}
    by_tag: dict[str, int] = {}
    deprecated_count = 0

    for ep in eps:
        m = ep.method.value
        by_method[m] = by_method.get(m, 0) + 1
        for t in (ep.tags or []):
            by_tag[t] = by_tag.get(t, 0) + 1
        if ep.deprecated:
            deprecated_count += 1

    return EndpointSummary(
        total=len(eps),
        by_method=by_method,
        by_tag=by_tag,
        deprecated_count=deprecated_count,
    )


@router.get("/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(
    spec_id: str,
    endpoint_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get endpoint detail with analysis."""
    ep = await get_endpoint_or_404(endpoint_id, db)
    tc_count = (await db.execute(
        select(func.count(TestCase.id)).where(TestCase.endpoint_id == endpoint_id)
    )).scalar() or 0

    return EndpointResponse(
        id=ep.id,
        spec_id=ep.spec_id,
        path=ep.path,
        method=ep.method.value,
        summary=ep.summary,
        description=ep.description,
        operation_id=ep.operation_id,
        tags=ep.tags or [],
        parameters=ep.parameters or [],
        request_body=ep.request_body,
        responses=ep.responses or {},
        security=ep.security,
        deprecated=ep.deprecated,
        analyzed_at=ep.analyzed_at,
        analysis=ep.analysis,
        testcase_count=tc_count,
        created_at=ep.created_at,
        updated_at=ep.updated_at,
    )
