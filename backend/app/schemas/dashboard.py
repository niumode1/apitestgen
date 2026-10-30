"""Dashboard schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    """Aggregate platform statistics."""
    total_projects: int = 0
    total_specs: int = 0
    total_endpoints: int = 0
    total_testcases: int = 0
    total_executions: int = 0
    overall_pass_rate: float = 0.0
    testcases_by_category: dict[str, int] = Field(default_factory=dict)
    executions_by_status: dict[str, int] = Field(default_factory=dict)


class TrendDataPoint(BaseModel):
    """A single data point in a trend chart."""
    date: str
    pass_rate: Optional[float] = None
    execution_count: int = 0
    testcase_count: int = 0


class DashboardTrends(BaseModel):
    """Trend data for charts."""
    pass_rate_trend: list[TrendDataPoint] = Field(default_factory=list)
    testcase_growth: list[TrendDataPoint] = Field(default_factory=list)
    flaky_endpoints: list[dict[str, Any]] = Field(default_factory=list)


class RecentActivity(BaseModel):
    """A recent activity entry."""
    activity_type: str  # execution_completed, spec_imported, generation_completed
    title: str
    description: str
    project_name: str
    timestamp: datetime


class DashboardRecent(BaseModel):
    """Recent activity feed."""
    activities: list[RecentActivity] = Field(default_factory=list)
