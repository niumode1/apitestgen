"""Dashboard API — aggregate platform statistics."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.project import Project
from app.models.spec import OpenAPISpec
from app.models.endpoint import APIEndpoint
from app.models.testcase import TestCase
from app.models.execution import TestExecution, ExecutionStatus
from app.schemas.dashboard import DashboardSummary, DashboardTrends, RecentActivity, TrendDataPoint

router = APIRouter()


@router.get("/summary")
async def dashboard_summary(db: AsyncSession = Depends(get_session)):
    """Get aggregate platform statistics."""
    total_projects = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    total_specs = (await db.execute(select(func.count(OpenAPISpec.id)))).scalar() or 0
    total_endpoints = (await db.execute(select(func.count(APIEndpoint.id)))).scalar() or 0
    total_testcases = (await db.execute(select(func.count(TestCase.id)))).scalar() or 0
    total_executions = (await db.execute(select(func.count(TestExecution.id)))).scalar() or 0

    # Overall pass rate
    pass_rate_result = await db.execute(
        select(
            func.sum(TestExecution.passed),
            func.sum(TestExecution.total_tests),
        ).where(TestExecution.total_tests > 0)
    )
    row = pass_rate_result.one_or_none()
    total_passed = row[0] or 0
    total_tests = row[1] or 0
    overall_pass_rate = round((total_passed / total_tests) * 100, 1) if total_tests > 0 else 0.0

    # Test cases by category
    cat_result = await db.execute(
        select(TestCase.category, func.count(TestCase.id)).group_by(TestCase.category)
    )
    testcases_by_category = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in cat_result}

    # Executions by status
    status_result = await db.execute(
        select(TestExecution.status, func.count(TestExecution.id)).group_by(TestExecution.status)
    )
    executions_by_status = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in status_result}

    return DashboardSummary(
        total_projects=total_projects,
        total_specs=total_specs,
        total_endpoints=total_endpoints,
        total_testcases=total_testcases,
        total_executions=total_executions,
        overall_pass_rate=overall_pass_rate,
        testcases_by_category=testcases_by_category,
        executions_by_status=executions_by_status,
    )


@router.get("/trends")
async def dashboard_trends(db: AsyncSession = Depends(get_session)):
    """Get trend data for charts."""
    # Recent executions (last 30)
    result = await db.execute(
        select(TestExecution).order_by(TestExecution.created_at.desc()).limit(30)
    )
    executions = result.scalars().all()

    pass_rate_trend = []
    for e in reversed(executions):
        pass_rate_trend.append(TrendDataPoint(
            date=e.created_at.strftime("%m-%d"),
            pass_rate=e.pass_rate,
            execution_count=1,
            testcase_count=e.total_tests,
        ))

    # Flaky endpoints (most failed)
    from app.models.execution import TestResult, TestOutcome
    flaky_result = await db.execute(
        select(TestResult.test_name, func.count(TestResult.id))
        .where(TestResult.status.in_([TestOutcome.FAILED, TestOutcome.ERROR]))
        .group_by(TestResult.test_name)
        .order_by(func.count(TestResult.id).desc())
        .limit(10)
    )
    flaky_endpoints = [{"name": row[0], "failures": row[1]} for row in flaky_result]

    return DashboardTrends(
        pass_rate_trend=pass_rate_trend,
        flaky_endpoints=flaky_endpoints,
    )


@router.get("/recent")
async def dashboard_recent(db: AsyncSession = Depends(get_session)):
    """Get recent activity feed."""
    from datetime import datetime
    activities = []

    # Recent executions
    execs = (await db.execute(
        select(TestExecution).order_by(TestExecution.created_at.desc()).limit(5)
    )).scalars().all()

    for e in execs:
        proj = (await db.execute(select(Project).where(Project.id == e.project_id))).scalar_one_or_none()
        activities.append(RecentActivity(
            activity_type="execution_completed",
            title=f"测试执行完成",
            description=f"{e.passed}/{e.total_tests} 通过 ({e.pass_rate}%)",
            project_name=proj.name if proj else "Unknown",
            timestamp=e.created_at,
        ))

    return {"activities": [a.model_dump() for a in activities]}
