"""TestExecution and TestResult models."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.spec import OpenAPISpec
    from app.models.testcase import TestCase
    from app.models.report import DefectReport


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionTrigger(str, enum.Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    CI = "ci"


class TestOutcome(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class TestExecution(Base, UUIDMixin, TimestampMixin):
    """A test execution run."""

    __tablename__ = "executions"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    spec_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("specs.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus, name="execution_status_enum"),
        default=ExecutionStatus.PENDING,
        nullable=False,
    )
    trigger: Mapped[ExecutionTrigger] = mapped_column(
        Enum(ExecutionTrigger, name="execution_trigger_enum"),
        default=ExecutionTrigger.MANUAL,
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Aggregate counts
    total_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Environment snapshot
    environment: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="executions")
    spec: Mapped[Optional["OpenAPISpec"]] = relationship("OpenAPISpec")
    results: Mapped[List["TestResult"]] = relationship(
        "TestResult", back_populates="execution", cascade="all, delete-orphan"
    )
    reports: Mapped[List["DefectReport"]] = relationship(
        "DefectReport", back_populates="execution", cascade="all, delete-orphan"
    )

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return round((self.passed / self.total_tests) * 100, 2)

    def __repr__(self) -> str:
        return f"<TestExecution id={self.id!r} status={self.status.value}>"


class TestResult(Base, UUIDMixin):
    """Individual test result from an execution."""

    __tablename__ = "test_results"

    execution_id: Mapped[str] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"), nullable=False
    )
    testcase_id: Mapped[str] = mapped_column(
        ForeignKey("testcases.id", ondelete="CASCADE"), nullable=False
    )

    test_name: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[TestOutcome] = mapped_column(
        Enum(TestOutcome, name="test_outcome_enum"), nullable=False
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    captured_stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    captured_stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    # Relationships
    execution: Mapped["TestExecution"] = relationship("TestExecution", back_populates="results")
    testcase: Mapped["TestCase"] = relationship("TestCase", back_populates="results")

    def __repr__(self) -> str:
        return f"<TestResult {self.test_name} status={self.status.value}>"
