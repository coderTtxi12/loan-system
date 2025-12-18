"""Loan Application model with status enum."""
import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.pii_encryption import decrypt_pii
from app.db.base import Base


class LoanStatus(str, enum.Enum):
    """Loan application status enum."""

    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    DISBURSED = "DISBURSED"
    COMPLETED = "COMPLETED"


class LoanApplication(Base):
    """
    Loan application model.

    Represents a loan request from a customer in a specific country.
    Partitioned by country_code for scalability.
    """

    __tablename__ = "loan_applications"

    # Primary key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Country and document info
    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        index=True,
        comment="ISO 2-letter country code: ES, MX, CO, BR",
    )
    document_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Document type: DNI, CURP, CC, CPF",
    )
    document_number: Mapped[str] = mapped_column(
        String(255),  # Increased for encrypted PII (Fernet tokens can be ~88+ chars)
        nullable=False,
        comment="Encrypted document number (PII)",
    )
    document_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA256 hash for lookup without decryption",
    )

    # Applicant info
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Encrypted full name (PII)",
    )

    # Financial info
    amount_requested: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    monthly_income: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="EUR",
    )

    # Status and risk
    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus, name="loan_status"),
        nullable=False,
        default=LoanStatus.PENDING,
        index=True,
    )
    risk_score: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Risk score 0-1000",
    )
    requires_review: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Banking and extra data
    banking_info: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Banking provider response (encrypted sensitive fields)",
    )
    extra_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Additional metadata and validation warnings",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    status_history = relationship(
        "LoanStatusHistory",
        back_populates="loan",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Table configuration
    __table_args__ = (
        # Composite indexes for common queries
        Index("idx_loans_country_status", "country_code", "status"),
        Index("idx_loans_created_at", "created_at", postgresql_using="btree"),
        # Partial index for pending/in_review loans (most queried)
        Index(
            "idx_loans_pending_review",
            "status",
            "created_at",
            postgresql_where=(status.in_([LoanStatus.PENDING, LoanStatus.IN_REVIEW])),
        ),
        # Check constraints
        {
            "comment": "Loan applications partitioned by country_code",
        },
    )

    @property
    def decrypted_document_number(self) -> str:
        """
        Get decrypted document number.
        
        Returns:
            Decrypted document number
        """
        try:
            return decrypt_pii(self.document_number)
        except Exception:
            # If decryption fails, return as-is (might be unencrypted legacy data)
            return self.document_number

    @property
    def decrypted_full_name(self) -> str:
        """
        Get decrypted full name.
        
        Returns:
            Decrypted full name
        """
        try:
            return decrypt_pii(self.full_name)
        except Exception:
            # If decryption fails, return as-is (might be unencrypted legacy data)
            return self.full_name

    def __repr__(self) -> str:
        return f"<LoanApplication(id={self.id}, country={self.country_code}, status={self.status.value})>"
