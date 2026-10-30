"""TestCase schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TestCaseResponse(BaseModel):
    """Full test case detail."""
    id: str
    project_id: str
    endpoint_id: str
    spec_id: str
    name: str
    description: str
    category: str
    severity: str
    test_code: str
    input_params: dict[str, Any]
    expected_status: Optional[int] = None
    expected_response: Optional[dict[str, Any]] = None
    llm_model: str
    llm_prompt_tokens: int
    llm_completion_tokens: int
    status: str
    review_notes: Optional[str] = None
    endpoint_path: str = ""
    endpoint_method: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestCaseBrief(BaseModel):
    """Brief test case for list view."""
    id: str
    name: str
    category: str
    severity: str
    status: str
    endpoint_path: str = ""
    endpoint_method: str = ""
    llm_model: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TestCaseUpdate(BaseModel):
    """Request to update a test case."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    test_code: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    review_notes: Optional[str] = None


class TestCaseBulkUpdate(BaseModel):
    """Bulk status update for test cases."""
    testcase_ids: list[str]
    status: str


class TestCaseFilter(BaseModel):
    """Filter options for test case listing."""
    category: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    endpoint_id: Optional[str] = None
    search: Optional[str] = Field(default=None, description="Search in name, description")
