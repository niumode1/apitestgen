"""Postman import/export API endpoints."""

import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.deps import get_project_or_404, get_session
from app.schemas.postman import PostmanExportResponse, PostmanImportResponse
from app.services.postman_service import export_as_postman, import_postman_collection
from app.models.postman import PostmanCollection
from sqlalchemy import select, desc

router = APIRouter()


@router.post("/import", response_model=PostmanImportResponse)
async def import_collection(
    file: UploadFile = File(...),
    project_id: str = None,
    db: AsyncSession = Depends(get_session),
):
    """Import a Postman v2.1 collection JSON file."""
    # Read file
    content = await file.read()
    try:
        collection = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    # Basic Postman validation
    if "info" not in collection:
        raise HTTPException(status_code=400, detail="Not a valid Postman collection")

    # Auto-create or use specified project
    if not project_id:
        # Create a new project
        from app.models.project import Project
        project = Project(
            name=collection.get("info", {}).get("name", "Postman Import"),
            description="Auto-created from Postman import",
        )
        db.add(project)
        await db.flush()
        project_id = project.id
    else:
        await get_project_or_404(project_id, db)

    result = await import_postman_collection(db, project_id, collection)
    return PostmanImportResponse(**result)


class ExportRequest(BaseModel):
    spec_id: Optional[str] = Field(default=None)
    endpoint_ids: Optional[list[str]] = Field(default=None)
    include_testcases: bool = Field(default=True)


@router.post("/export", response_model=PostmanExportResponse)
async def export_collection(
    project_id: str,
    body: ExportRequest | None = None,
    db: AsyncSession = Depends(get_session),
):
    """Export endpoints as a Postman v2.1 collection."""
    await get_project_or_404(project_id, db)

    if body is None:
        body = ExportRequest()

    collection = await export_as_postman(
        db=db,
        project_id=project_id,
        spec_id=body.spec_id,
        endpoint_ids=body.endpoint_ids,
        include_testcases=body.include_testcases,
    )

    return PostmanExportResponse(collection=collection)


@router.get("/collections")
async def list_collections(
    project_id: str = None,
    db: AsyncSession = Depends(get_session),
):
    """List imported Postman collections."""
    query = select(PostmanCollection)
    if project_id:
        query = query.where(PostmanCollection.project_id == project_id)
    result = await db.execute(query.order_by(desc(PostmanCollection.imported_at)))
    collections = result.scalars().all()
    return {
        "items": [
            {
                "id": c.id, "name": c.name, "project_id": c.project_id,
                "item_count": c.item_count, "imported_at": c.created_at.isoformat(),
            }
            for c in collections
        ]
    }
