"""Project CRUD endpoints."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_project_or_404, get_session, pagination
from app.models.project import Project
from app.models.spec import OpenAPISpec
from app.models.testcase import TestCase
from app.models.execution import TestExecution
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    search: str = Query(default="", description="Search by name"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    """List all projects with optional search."""
    query = select(Project)
    count_query = select(func.count(Project.id))

    if search:
        query = query.where(Project.name.ilike(f"%{search}%"))
        count_query = count_query.where(Project.name.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    query = query.order_by(Project.updated_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    projects = result.scalars().all()

    # Enrich with counts
    items = []
    for p in projects:
        spec_count = (await db.execute(
            select(func.count(OpenAPISpec.id)).where(OpenAPISpec.project_id == p.id)
        )).scalar() or 0
        tc_count = (await db.execute(
            select(func.count(TestCase.id)).where(TestCase.project_id == p.id)
        )).scalar() or 0
        ex_count = (await db.execute(
            select(func.count(TestExecution.id)).where(TestExecution.project_id == p.id)
        )).scalar() or 0
        items.append(ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            base_url=p.base_url,
            spec_count=spec_count,
            testcase_count=tc_count,
            execution_count=ex_count,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create a new project."""
    project = Project(**data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        base_url=project.base_url,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project: Project = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_session),
):
    """Get project detail."""
    spec_count = (await db.execute(
        select(func.count(OpenAPISpec.id)).where(OpenAPISpec.project_id == project.id)
    )).scalar() or 0
    tc_count = (await db.execute(
        select(func.count(TestCase.id)).where(TestCase.project_id == project.id)
    )).scalar() or 0
    ex_count = (await db.execute(
        select(func.count(TestExecution.id)).where(TestExecution.project_id == project.id)
    )).scalar() or 0
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        base_url=project.base_url,
        spec_count=spec_count,
        testcase_count=tc_count,
        execution_count=ex_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    data: ProjectUpdate,
    project: Project = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_session),
):
    """Update a project."""
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        base_url=project.base_url,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project: Project = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_session),
):
    """Delete a project and all related data."""
    await db.delete(project)
    await db.commit()
    return MessageResponse(message=f"Project '{project.name}' deleted successfully")


class BulkDeleteRequest(BaseModel):
    project_ids: list[str]


@router.post("/bulk-delete", response_model=MessageResponse)
async def bulk_delete_projects(
    data: BulkDeleteRequest,
    db: AsyncSession = Depends(get_session),
):
    """Bulk delete projects and all related data."""
    result = await db.execute(
        select(Project).where(Project.id.in_(data.project_ids))
    )
    projects = result.scalars().all()
    count = len(projects)
    for project in projects:
        await db.delete(project)
    await db.commit()
    return MessageResponse(message=f"Deleted {count} projects")
