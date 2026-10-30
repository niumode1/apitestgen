"""TestCase model — LLM-generated pytest test cases."""

import enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.endpoint import APIEndpoint
    from app.models.project import Project
    from app.models.spec import OpenAPISpec
    from app.models.execution import TestResult


class TestCategory(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    SECURITY = "security"
    SCHEMA = "schema"


class TestSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestCaseStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    DISABLED = "disabled"


class TestCase(Base, UUIDMixin, TimestampMixin):
    """A generated pytest test case."""

    __tablename__ = "testcases"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    endpoint_id: Mapped[str] = mapped_column(
        ForeignKey("endpoints.id", ondelete="CASCADE"), nullable=False
    )
    spec_id: Mapped[str] = mapped_column(
        ForeignKey("specs.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[TestCategory] = mapped_column(
        Enum(TestCategory, name="test_category_enum"), nullable=False
    )
    severity: Mapped[TestSeverity] = mapped_column(
        Enum(TestSeverity, name="test_severity_enum"),
        default=TestSeverity.LOW,
        nullable=False,
    )
    test_code: Mapped[str] = mapped_column(Text, nullable=False)
    input_params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    expected_status: Mapped[int] = mapped_column(Integer, nullable=True)
    expected_response: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # LLM metadata
    llm_model: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    llm_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    llm_completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Review state
    status: Mapped[TestCaseStatus] = mapped_column(
        Enum(TestCaseStatus, name="testcase_status_enum"),
        default=TestCaseStatus.DRAFT,
        nullable=False,
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="testcases")
    endpoint: Mapped["APIEndpoint"] = relationship("APIEndpoint", back_populates="testcases")
    spec: Mapped["OpenAPISpec"] = relationship("OpenAPISpec")
    results: Mapped[list["TestResult"]] = relationship(
        "TestResult", back_populates="testcase", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TestCase id={self.id!r} name={self.name!r} category={self.category.value}>"
