"""API v1 router — aggregates all v1 sub-routers."""

from fastapi import APIRouter

from app.api.v1 import (
    projects,
    specs,
    endpoints,
    testcases,
    executions,
    reports,
    postman,
    llm_providers,
    generation,
    dashboard,
)

api_v1_router = APIRouter()

# Health check
@api_v1_router.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.config import settings
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }

# ── Resource routers ─────────────────────────────────────────────
api_v1_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_v1_router.include_router(specs.router, prefix="/projects/{project_id}/specs", tags=["Specs"])
api_v1_router.include_router(endpoints.router, prefix="/specs/{spec_id}/endpoints", tags=["Endpoints"])
api_v1_router.include_router(generation.router, prefix="/specs/{spec_id}", tags=["Generation"])
api_v1_router.include_router(testcases.router, prefix="/projects/{project_id}/testcases", tags=["Test Cases"])
api_v1_router.include_router(executions.router, prefix="/projects/{project_id}/executions", tags=["Executions"])
api_v1_router.include_router(executions.router_ws, prefix="/ws", tags=["WebSocket"])
api_v1_router.include_router(reports.router, prefix="/projects/{project_id}/reports", tags=["Reports"])
api_v1_router.include_router(postman.router, prefix="/postman", tags=["Postman"])
api_v1_router.include_router(llm_providers.router, prefix="/llm/providers", tags=["LLM Providers"])
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
