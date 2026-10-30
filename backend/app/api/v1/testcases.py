"""TestCase endpoints."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_project_or_404, get_session, get_testcase_or_404
from app.models.testcase import TestCase, TestCaseStatus
from app.models.endpoint import APIEndpoint
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.testcase import (
    TestCaseBrief, TestCaseBulkUpdate, TestCaseFilter,
    TestCaseResponse, TestCaseUpdate,
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TestCaseBrief])
async def list_testcases(
    project_id: str,
    category: str = Query(default=None),
    status: str = Query(default=None),
    endpoint_id: str = Query(default=None),
    search: str = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
):
    """List test cases with filters."""
    _ = await get_project_or_404(project_id, db)

    query = select(TestCase).where(TestCase.project_id == project_id)
    count_q = select(func.count(TestCase.id)).where(TestCase.project_id == project_id)

    if category:
        query = query.where(TestCase.category == category)
        count_q = count_q.where(TestCase.category == category)
    if status:
        query = query.where(TestCase.status == status)
        count_q = count_q.where(TestCase.status == status)
    if endpoint_id:
        query = query.where(TestCase.endpoint_id == endpoint_id)
        count_q = count_q.where(TestCase.endpoint_id == endpoint_id)
    if search:
        query = query.where(TestCase.name.ilike(f"%{search}%"))
        count_q = count_q.where(TestCase.name.ilike(f"%{search}%"))

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(TestCase.created_at.desc()).offset(offset).limit(page_size)
    )
    testcases = result.scalars().all()

    # Enrich with endpoint info
    items = []
    for tc in testcases:
        ep_result = await db.execute(
            select(APIEndpoint).where(APIEndpoint.id == tc.endpoint_id)
        )
        ep = ep_result.scalar_one_or_none()
        items.append(TestCaseBrief(
            id=tc.id,
            name=tc.name,
            category=tc.category.value if hasattr(tc.category, 'value') else str(tc.category),
            severity=tc.severity.value if hasattr(tc.severity, 'value') else str(tc.severity),
            status=tc.status.value if hasattr(tc.status, 'value') else str(tc.status),
            endpoint_path=ep.path if ep else "",
            endpoint_method=ep.method.value if ep else "",
            llm_model=tc.llm_model,
            created_at=tc.created_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/{testcase_id}", response_model=TestCaseResponse)
async def get_testcase(
    project_id: str,
    testcase_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get test case detail with full code."""
    tc = await get_testcase_or_404(testcase_id, db)

    ep_result = await db.execute(
        select(APIEndpoint).where(APIEndpoint.id == tc.endpoint_id)
    )
    ep = ep_result.scalar_one_or_none()

    return TestCaseResponse(
        id=tc.id,
        project_id=tc.project_id,
        endpoint_id=tc.endpoint_id,
        spec_id=tc.spec_id,
        name=tc.name,
        description=tc.description,
        category=tc.category.value if hasattr(tc.category, 'value') else str(tc.category),
        severity=tc.severity.value if hasattr(tc.severity, 'value') else str(tc.severity),
        test_code=tc.test_code,
        input_params=tc.input_params or {},
        expected_status=tc.expected_status,
        expected_response=tc.expected_response,
        llm_model=tc.llm_model,
        llm_prompt_tokens=tc.llm_prompt_tokens,
        llm_completion_tokens=tc.llm_completion_tokens,
        status=tc.status.value if hasattr(tc.status, 'value') else str(tc.status),
        review_notes=tc.review_notes,
        endpoint_path=ep.path if ep else "",
        endpoint_method=ep.method.value if ep else "",
        created_at=tc.created_at,
        updated_at=tc.updated_at,
    )


@router.put("/{testcase_id}", response_model=TestCaseResponse)
async def update_testcase(
    project_id: str,
    testcase_id: str,
    data: TestCaseUpdate,
    db: AsyncSession = Depends(get_session),
):
    """Update a test case (code, status, etc.)."""
    tc = await get_testcase_or_404(testcase_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None and hasattr(tc, key):
            setattr(tc, key, value)
    await db.commit()
    await db.refresh(tc)
    return TestCaseResponse(
        id=tc.id, project_id=tc.project_id, endpoint_id=tc.endpoint_id,
        spec_id=tc.spec_id, name=tc.name, description=tc.description,
        category=tc.category.value if hasattr(tc.category, 'value') else str(tc.category),
        severity=tc.severity.value if hasattr(tc.severity, 'value') else str(tc.severity),
        test_code=tc.test_code, input_params=tc.input_params or {},
        expected_status=tc.expected_status, expected_response=tc.expected_response,
        llm_model=tc.llm_model, llm_prompt_tokens=tc.llm_prompt_tokens,
        llm_completion_tokens=tc.llm_completion_tokens,
        status=tc.status.value if hasattr(tc.status, 'value') else str(tc.status),
        review_notes=tc.review_notes, endpoint_path="", endpoint_method="",
        created_at=tc.created_at, updated_at=tc.updated_at,
    )


@router.delete("/{testcase_id}", response_model=MessageResponse)
async def delete_testcase(
    project_id: str,
    testcase_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a test case."""
    tc = await get_testcase_or_404(testcase_id, db)
    await db.delete(tc)
    await db.commit()
    return MessageResponse(message=f"Test case '{tc.name}' deleted")


@router.post("/bulk", response_model=MessageResponse)
async def bulk_update_testcases(
    project_id: str,
    data: TestCaseBulkUpdate,
    db: AsyncSession = Depends(get_session),
):
    """Bulk update test case status."""
    result = await db.execute(
        select(TestCase).where(TestCase.id.in_(data.testcase_ids))
    )
    testcases = result.scalars().all()
    for tc in testcases:
        tc.status = data.status
    await db.commit()
    return MessageResponse(message=f"Updated {len(testcases)} test cases to {data.status}")


class BulkDeleteRequest(BaseModel):
    testcase_ids: list[str]


@router.post("/bulk-delete", response_model=MessageResponse)
async def bulk_delete_testcases(
    project_id: str,
    data: BulkDeleteRequest,
    db: AsyncSession = Depends(get_session),
):
    """Bulk delete test cases."""
    result = await db.execute(
        select(TestCase).where(TestCase.id.in_(data.testcase_ids))
    )
    testcases = result.scalars().all()
    count = len(testcases)
    for tc in testcases:
        await db.delete(tc)
    await db.commit()
    return MessageResponse(message=f"Deleted {count} test cases")
