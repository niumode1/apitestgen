"""Defect Report model."""

import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.execution import TestExecution
    from app.models.project import Project


class ReportFormat(str, enum.Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


class DefectReport(Base, UUIDMixin, TimestampMixin):
    """A generated defect report from a test execution."""

    __tablename__ = "defect_reports"

    execution_id: Mapped[str] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat, name="report_format_enum"), nullable=False
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Aggregate stats at report time
    failed_count: Mapped[int] = mapped_column(default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(default=0, nullable=False)
    total_count: Mapped[int] = mapped_column(default=0, nullable=False)
    pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    execution: Mapped["TestExecution"] = relationship("TestExecution", back_populates="reports")
    project: Mapped["Project"] = relationship("Project", back_populates="reports")

    def __repr__(self) -> str:
        return f"<DefectReport id={self.id!r} title={self.title!r}>"
