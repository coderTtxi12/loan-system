"""Async job model for background task queue."""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobStatus(str, enum.Enum):
    """Job status enum."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AsyncJob(Base):
    """
    Async job queue stored in PostgreSQL.

    Used for background task processing with pg_notify for real-time updates.
    """

    __tablename__ = "async_jobs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # Queue and job info
    queue_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Queue name: risk_evaluation, audit, notifications, webhooks",
    )
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Job payload data",
    )

    # Status tracking
    status: Mapped[JobStatus] = mapped_column(
        String(20),
        nullable=False,
        default=JobStatus.PENDING,
        index=True,
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Higher priority = processed first",
    )

    # Retry handling
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )
    error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last error message if failed",
    )

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When the job should be processed",
    )

    # Processing timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Worker lock
    locked_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Worker ID that has locked this job",
    )
    locked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Indexes for efficient job processing
    __table_args__ = (
        # Index for fetching pending jobs by queue
        Index(
            "idx_jobs_pending_queue",
            "queue_name",
            "priority",
            "scheduled_at",
            postgresql_where=(status == JobStatus.PENDING.value),
        ),
        # Index for checking locked/running jobs
        Index(
            "idx_jobs_running",
            "locked_by",
            "locked_at",
            postgresql_where=(status == JobStatus.RUNNING.value),
        ),
        # Index for cleanup of old completed jobs
        Index(
            "idx_jobs_completed",
            "completed_at",
            postgresql_where=(status == JobStatus.COMPLETED.value),
        ),
    )

    def __repr__(self) -> str:
        return f"<AsyncJob(id={self.id}, queue={self.queue_name}, status={self.status})>"
