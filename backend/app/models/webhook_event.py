"""Webhook event model for tracking external events."""
from datetime import datetime
from typing import Optional
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebhookEvent(Base):
    """
    Webhook event model for tracking incoming webhook events.

    Stores all webhook events from external banking providers
    for audit and retry purposes.
    """

    __tablename__ = "webhook_events"

    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Source information
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Source of the webhook (banking provider name)",
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of event (status_update, risk_score, etc.)",
    )

    # Payload and security
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Full webhook payload",
    )
    signature: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="HMAC signature for verification",
    )

    # Processing status
    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if processing failed",
    )

    # Related loan (if applicable)
    loan_id: Mapped[Optional[PyUUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loan_applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_webhook_unprocessed",
            "processed",
            "created_at",
            postgresql_where=(processed == False),  # noqa: E712
        ),
        Index(
            "idx_webhook_source_type",
            "source",
            "event_type",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<WebhookEvent(id={self.id}, source={self.source}, type={self.event_type}, processed={self.processed})>"
