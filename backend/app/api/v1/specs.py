"""OpenAPI Spec endpoints — upload, parse, list, delete."""

import json
from datetime import datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_project_or_404, get_session, get_spec_or_404
from app.models.spec import OpenAPISpec, ParseStatus, SpecFormat
from app.models.endpoint import APIEndpoint, HTTPMethod
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.spec import SpecListResponse, SpecResponse, SpecUploadResponse
from app.config import settings

router = APIRouter()


@router.get("", response_model=PaginatedResponse[SpecListResponse])
async def list_specs(
    project_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    """List specs for a project."""
    _ = await get_project_or_404(project_id, db)

    query = select(OpenAPISpec).where(OpenAPISpec.project_id == project_id)
    count_q = select(func.count(OpenAPISpec.id)).where(OpenAPISpec.project_id == project_id)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(OpenAPISpec.imported_at.desc()).offset(offset).limit(page_size))
    specs = result.scalars().all()

    items = []
    for s in specs:
        ep_count = (await db.execute(
            select(func.count(APIEndpoint.id)).where(APIEndpoint.spec_id == s.id)
        )).scalar() or 0
        items.append(SpecListResponse(
            id=s.id,
            name=s.name,
            version=s.version,
            spec_format=s.spec_format.value,
            parse_status=s.parse_status.value,
            endpoint_count=ep_count,
            imported_at=s.imported_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


class URLImportRequest(BaseModel):
    url: str


@router.post("/import-url", response_model=SpecUploadResponse, status_code=201)
async def import_spec_from_url(
    project_id: str,
    body: URLImportRequest,
    db: AsyncSession = Depends(get_session),
):
    """Import an OpenAPI spec from a URL."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(body.url)
            resp.raise_for_status()
            raw_content = resp.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

    return await _parse_and_save_spec(project_id, raw_content, body.url.rsplit("/", 1)[-1], db)


@router.post("", response_model=SpecUploadResponse, status_code=201)
async def upload_spec(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
):
    """Upload an OpenAPI spec file."""
    content_bytes = await file.read()
    if len(content_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB")
    return await _parse_and_save_spec(project_id, content_bytes.decode("utf-8"), file.filename or "spec.json", db)


async def _parse_and_save_spec(project_id: str, raw_content: str, filename: str, db: AsyncSession):
    """Shared logic: parse raw OpenAPI content and save as spec + endpoints."""
    # Detect format
    if filename.endswith(".yaml") or filename.endswith(".yml"):
        spec_format = SpecFormat.YAML
        try:
            parsed = yaml.safe_load(raw_content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    else:
        spec_format = SpecFormat.JSON
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    if not isinstance(parsed, dict) or "openapi" not in parsed:
        raise HTTPException(status_code=400, detail="Not a valid OpenAPI 3.x spec")

    spec_version = parsed.get("info", {}).get("version", "unknown")
    spec_name = parsed.get("info", {}).get("title", filename)

    spec = OpenAPISpec(
        project_id=project_id, name=spec_name, version=spec_version,
        spec_format=spec_format, raw_content=raw_content, parsed_json=parsed,
        parse_status=ParseStatus.PENDING, imported_at=datetime.utcnow(),
    )
    db.add(spec)
    await db.flush()

    endpoint_count = 0
    paths = parsed.get("paths", {})
    for path, path_item in paths.items():
        if not isinstance(path_item, dict): continue
        for method_name in ["get", "post", "put", "delete", "patch", "head", "options", "trace"]:
            operation = path_item.get(method_name)
            if operation is None: continue
            try: http_method = HTTPMethod[method_name.upper()]
            except KeyError: continue

            parameters = list(operation.get("parameters", []))
            for pp in path_item.get("parameters", []):
                if pp not in parameters: parameters.append(pp)

            db.add(APIEndpoint(
                spec_id=spec.id, path=path, method=http_method,
                summary=operation.get("summary", ""), description=operation.get("description", ""),
                operation_id=operation.get("operationId", ""), tags=operation.get("tags", []),
                parameters=parameters, request_body=operation.get("requestBody"),
                responses=operation.get("responses", {}), security=operation.get("security"),
                deprecated=operation.get("deprecated", False),
            ))
            endpoint_count += 1

    spec.parse_status = ParseStatus.PARSED
    await db.commit()
    await db.refresh(spec)

    return SpecUploadResponse(
        id=spec.id, name=spec_name, version=spec_version,
        spec_format=spec_format.value, parse_status=spec.parse_status.value,
        endpoint_count=endpoint_count,
        message=f"Imported '{spec_name}' with {endpoint_count} endpoints",
    )


@router.post("", response_model=SpecUploadResponse, status_code=201)
async def upload_spec(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
):
    """Upload an OpenAPI spec file (JSON or YAML)."""
    content_bytes = await file.read()
    if len(content_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB")
    return await _parse_and_save_spec(project_id, content_bytes.decode("utf-8"), file.filename or "spec.json", db)


@router.get("/{spec_id}", response_model=SpecResponse)
async def get_spec(
    spec_id: str,
    project_id: str,  # from path, for URL consistency
    db: AsyncSession = Depends(get_session),
):
    """Get spec detail."""
    spec = await get_spec_or_404(spec_id, db)
    ep_count = (await db.execute(
        select(func.count(APIEndpoint.id)).where(APIEndpoint.spec_id == spec_id)
    )).scalar() or 0

    return SpecResponse(
        id=spec.id,
        project_id=spec.project_id,
        name=spec.name,
        version=spec.version,
        spec_format=spec.spec_format.value,
        parse_status=spec.parse_status.value,
        parse_error=spec.parse_error,
        endpoint_count=ep_count,
        imported_at=spec.imported_at,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
    )


@router.delete("/{spec_id}", response_model=MessageResponse)
async def delete_spec(
    spec_id: str,
    project_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a spec and all its endpoints/test cases."""
    spec = await get_spec_or_404(spec_id, db)
    name = spec.name
    await db.delete(spec)
    await db.commit()
    return MessageResponse(message=f"Spec '{name}' deleted successfully")
