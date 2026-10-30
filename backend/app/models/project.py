"""Project model — top-level container for API specs and tests."""

from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.spec import OpenAPISpec
    from app.models.testcase import TestCase
    from app.models.execution import TestExecution
    from app.models.report import DefectReport
    from app.models.postman import PostmanCollection


class Project(Base, UUIDMixin, TimestampMixin):
    """A project groups related API specs and test assets."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    base_url: Mapped[str] = mapped_column(String(1024), default="", nullable=False)

    # Relationships
    specs: Mapped[List["OpenAPISpec"]] = relationship(
        "OpenAPISpec", back_populates="project", cascade="all, delete-orphan"
    )
    testcases: Mapped[List["TestCase"]] = relationship(
        "TestCase", back_populates="project", cascade="all, delete-orphan"
    )
    executions: Mapped[List["TestExecution"]] = relationship(
        "TestExecution", back_populates="project", cascade="all, delete-orphan"
    )
    reports: Mapped[List["DefectReport"]] = relationship(
        "DefectReport", back_populates="project", cascade="all, delete-orphan"
    )
    postman_collections: Mapped[List["PostmanCollection"]] = relationship(
        "PostmanCollection", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id!r} name={self.name!r}>"
