"""Test Execution schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    """Request to start a test execution."""
    project_id: str
    spec_id: Optional[str] = Field(default=None, description="Run tests for a specific spec")
    testcase_ids: Optional[list[str]] = Field(default=None, description="Specific test cases to run")
    name: Optional[str] = Field(default=None, description="Execution run name")
    environment: dict[str, Any] = Field(
        default_factory=dict,
        description="Environment variables/overrides (e.g., BASE_URL)",
    )
    trigger: str = Field(default="manual", pattern="^(manual|scheduled|ci)$")


class ExecutionResponse(BaseModel):
    """Full execution detail."""
    id: str
    project_id: str
    spec_id: Optional[str] = None
    name: str
    status: str
    trigger: str
    total_tests: int
    passed: int
    failed: int
    errors: int
    skipped: int
    pass_rate: float
    duration_ms: Optional[int] = None
    environment: dict[str, Any]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExecutionBrief(BaseModel):
    """Brief execution info for list view."""
    id: str
    name: str
    status: str
    trigger: str
    total_tests: int
    passed: int
    failed: int
    errors: int
    pass_rate: float
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TestResultResponse(BaseModel):
    """Individual test result."""
    id: str
    execution_id: str
    testcase_id: str
    test_name: str
    status: str
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    captured_stdout: Optional[str] = None
    captured_stderr: Optional[str] = None
    recorded_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
