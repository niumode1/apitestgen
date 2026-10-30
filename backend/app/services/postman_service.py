"""Postman Service — import/export Postman Collection v2.1 format."""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.endpoint import APIEndpoint, HTTPMethod
from app.models.postman import PostmanCollection
from app.models.project import Project
from app.models.spec import OpenAPISpec
from app.models.testcase import TestCase, TestCaseStatus
from app.utils.logger import logger


# ── Import ────────────────────────────────────────────────────

async def import_postman_collection(
    db: AsyncSession,
    project_id: str,
    collection_json: dict[str, Any],
) -> dict:
    """Import a Postman v2.1 collection, creating endpoints in a project.

    Returns summary dict with endpoint_count and collection_name.
    """
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    info = collection_json.get("info", {})
    collection_name = info.get("name", "Imported Collection")
    items = collection_json.get("item", [])

    # Create a spec to hold the imported endpoints
    spec = OpenAPISpec(
        project_id=project_id,
        name=f"Postman: {collection_name}",
        version="postman-import",
        spec_format="json",
        raw_content="Postman import",
        parse_status="parsed",
        imported_at=datetime.utcnow(),
    )
    db.add(spec)
    await db.flush()

    endpoint_count = 0

    def process_items(item_list: list, base_path: str = ""):
        nonlocal endpoint_count
        for item in item_list:
            # Check if it's a folder (has items) or a request
            if "item" in item:
                process_items(item["item"], base_path)
            elif "request" in item:
                req = item["request"]
                method_str = req.get("method", "GET").upper()
                # Build path from URL
                url_obj = req.get("url", {})
                path_parts = url_obj.get("path", [])
                path = "/" + "/".join(path_parts) if path_parts else req.get("name", "/")

                # Extract query params
                query_params = url_obj.get("query", [])
                parameters = []
                for qp in query_params:
                    parameters.append({
                        "name": qp.get("key", ""),
                        "in": "query",
                        "required": not qp.get("disabled", False),
                        "schema": {"type": "string"},
                        "description": qp.get("description", ""),
                    })

                # Extract headers
                headers = req.get("header", [])
                for h in headers:
                    if h.get("key", "").lower() not in ("content-type", "accept", "authorization"):
                        parameters.append({
                            "name": h.get("key", ""),
                            "in": "header",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": h.get("description", ""),
                        })

                # Request body
                request_body = None
                body = req.get("body", {})
                if body and body.get("mode") == "raw" and body.get("raw"):
                    request_body = {
                        "content": {"application/json": {"schema": {"type": "object"}}},
                        "description": "Request body",
                    }

                try:
                    http_method = HTTPMethod[method_str]
                except KeyError:
                    http_method = HTTPMethod.GET

                endpoint = APIEndpoint(
                    spec_id=spec.id,
                    path=path,
                    method=http_method,
                    summary=req.get("name", ""),
                    description=req.get("description", {}).get("content", "") if isinstance(req.get("description"), dict) else str(req.get("description", "")),
                    operation_id=req.get("name", "").replace(" ", ""),
                    tags=[],
                    parameters=parameters,
                    request_body=request_body,
                    responses={"200": {"description": "Success"}},
                )
                db.add(endpoint)
                endpoint_count += 1

    process_items(items)

    # Save the collection record
    collection = PostmanCollection(
        project_id=project_id,
        name=collection_name,
        collection_json=collection_json,
        item_count=endpoint_count,
    )
    db.add(collection)
    await db.commit()

    return {
        "project_id": project_id,
        "project_name": project.name,
        "collection_name": collection_name,
        "endpoint_count": endpoint_count,
        "message": f"Imported '{collection_name}' with {endpoint_count} endpoints",
    }


# ── Export ────────────────────────────────────────────────────

async def export_as_postman(
    db: AsyncSession,
    project_id: str,
    spec_id: Optional[str] = None,
    endpoint_ids: Optional[list[str]] = None,
    include_testcases: bool = False,
) -> dict[str, Any]:
    """Export project endpoints as a Postman v2.1 collection."""

    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Load endpoints
    query = select(APIEndpoint)
    if spec_id:
        query = query.where(APIEndpoint.spec_id == spec_id)
    elif endpoint_ids:
        query = query.where(APIEndpoint.id.in_(endpoint_ids))
    else:
        # Get all endpoints for the project via specs
        specs = (await db.execute(
            select(OpenAPISpec.id).where(OpenAPISpec.project_id == project_id)
        )).scalars().all()
        if specs:
            query = query.where(APIEndpoint.spec_id.in_(specs))

    endpoints = (await db.execute(query)).scalars().all()

    # Build Postman items
    items = []
    for ep in endpoints:
        # Build URL
        url_path = ep.path.strip("/").split("/")
        query_params = []
        for p in (ep.parameters or []):
            if p.get("in") == "query":
                query_params.append({
                    "key": p.get("name", ""),
                    "value": "",
                    "description": p.get("description", ""),
                })

        item: dict[str, Any] = {
            "name": f"{ep.method.value} {ep.path}",
            "request": {
                "method": ep.method.value,
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "url": {
                    "raw": f"{project.base_url or 'http://localhost'}{ep.path}",
                    "host": [project.base_url or "http://localhost"],
                    "path": url_path,
                    "query": query_params,
                },
                "description": ep.description or ep.summary,
            },
            "response": [],
        }

        # Add body for POST/PUT/PATCH
        if ep.method in (HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH) and ep.request_body:
            item["request"]["body"] = {
                "mode": "raw",
                "raw": "{}",
                "options": {"raw": {"language": "json"}},
            }

        # Include test cases as examples
        if include_testcases:
            tcs = (await db.execute(
                select(TestCase).where(
                    TestCase.endpoint_id == ep.id,
                    TestCase.status.in_([TestCaseStatus.DRAFT, TestCaseStatus.APPROVED]),
                )
            )).scalars().all()

            for tc in tcs:
                if "example" not in item:
                    item["example"] = []
                # Not natively supported in Postman format, just note it
                item.setdefault("description", "")
                item["description"] += f"\n\nTest: {tc.name}"

        items.append(item)

    collection = {
        "info": {
            "name": project.name,
            "description": project.description or "",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": items,
    }

    return collection
