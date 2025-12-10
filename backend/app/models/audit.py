"""Audit log model for tracking all entity changes."""
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID as PyUUID

from sqlalchemy import BigInteger, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditAction(str, enum.Enum):
    """Audit action types."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"


class ActorType(str, enum.Enum):
    """Actor type for audit logs."""

    USER = "USER"
    SYSTEM = "SYSTEM"
    WORKER = "WORKER"
    WEBHOOK = "WEBHOOK"


class AuditLog(Base):
    """
    Audit log for tracking all entity changes.

    Partitioned by created_at (monthly) for scalability.
    """

    __tablename__ = "audit_logs"

    # Use BigInteger for high-volume audit logs
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # Entity being audited
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of entity: loan_application, user, etc.",
    )
    entity_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Action performed
    action: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    # Who performed the action
    actor_id: Mapped[Optional[PyUUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User or system ID that performed the action",
    )
    actor_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="USER, SYSTEM, WORKER, WEBHOOK",
    )

    # What changed
    changes: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON object with field changes: {field: {old: x, new: y}}",
    )

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Indexes for common queries
    __table_args__ = (
        Index(
            "idx_audit_entity_created",
            "entity_type",
            "entity_id",
            "created_at",
            postgresql_using="btree",
        ),
        Index(
            "idx_audit_actor_created",
            "actor_id",
            "created_at",
            postgresql_using="btree",
        ),
        {
            "comment": "Audit logs - consider partitioning by month for production",
        },
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, entity={self.entity_type}:{self.entity_id}, action={self.action})>"
