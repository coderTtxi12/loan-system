"""Loan status history model for tracking status changes."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LoanStatusHistory(Base):
    """
    Tracks all status changes for loan applications.

    Used for audit trail and debugging status transitions.
    """

    __tablename__ = "loan_status_history"

    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Foreign key to loan application
    loan_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loan_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status change info
    previous_status: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Previous status (null for initial creation)",
    )
    new_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    # Who made the change
    changed_by: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who made the change (null for system)",
    )

    # Reason for change
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for status change",
    )

    # Additional data
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        comment="Additional context data for the status change",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship back to loan
    loan = relationship(
        "LoanApplication",
        back_populates="status_history",
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_status_history_loan_created",
            "loan_id",
            "created_at",
            postgresql_using="btree",
        ),
    )

    def __repr__(self) -> str:
        return f"<LoanStatusHistory(loan_id={self.loan_id}, {self.previous_status} -> {self.new_status})>"
