"""Loans API Schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.loan import LoanStatus


class LoanCreateRequest(BaseModel):
    """Request schema for creating a loan application."""

    country_code: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="ISO 2-letter country code (ES, MX, CO, BR)",
        examples=["ES"],
    )
    document_type: str = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Document type (DNI, CURP, CC, CPF)",
        examples=["DNI"],
    )
    document_number: str = Field(
        ...,
        min_length=5,
        max_length=50,
        description="Document number",
        examples=["12345678Z"],
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Applicant's full name",
        examples=["Juan García López"],
    )
    amount_requested: Decimal = Field(
        ...,
        gt=0,
        le=10000000,
        description="Loan amount requested",
        examples=[15000.00],
    )
    monthly_income: Decimal = Field(
        ...,
        ge=0,
        le=10000000,
        description="Monthly income",
        examples=[3500.00],
    )

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        """Validate and uppercase country code."""
        return v.upper()

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        """Validate and uppercase document type."""
        return v.upper()


class LoanResponse(BaseModel):
    """Response schema for a loan application."""

    id: UUID
    country_code: str
    document_type: str
    full_name: str
    amount_requested: Decimal
    monthly_income: Decimal
    currency: str
    status: LoanStatus
    risk_score: Optional[int] = None
    requires_review: bool
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    # Exclude sensitive fields
    # document_number and document_hash are not exposed

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_decryption(cls, obj):
        """
        Create response from ORM object with decrypted PII.
        
        Args:
            obj: LoanApplication ORM object
            
        Returns:
            LoanResponse with decrypted full_name
        """
        return cls(
            id=obj.id,
            country_code=obj.country_code,
            document_type=obj.document_type,
            full_name=obj.decrypted_full_name,  # Use decrypted property
            amount_requested=obj.amount_requested,
            monthly_income=obj.monthly_income,
            currency=obj.currency,
            status=obj.status,
            risk_score=obj.risk_score,
            requires_review=obj.requires_review,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            processed_at=obj.processed_at,
        )


class LoanDetailResponse(LoanResponse):
    """Detailed response including banking info and metadata."""

    banking_info: Optional[dict[str, Any]] = None
    extra_data: Optional[dict[str, Any]] = None


class LoanListResponse(BaseModel):
    """Response schema for paginated loan list."""

    items: list[LoanResponse]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def from_results(
        cls,
        items: list,
        total: int,
        page: int,
        page_size: int,
    ) -> "LoanListResponse":
        """Create response from query results with decrypted PII."""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=[LoanResponse.from_orm_with_decryption(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


class LoanStatusUpdateRequest(BaseModel):
    """Request schema for updating loan status."""

    status: LoanStatus = Field(
        ...,
        description="New status for the loan",
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for status change",
    )


class LoanStatusHistoryResponse(BaseModel):
    """Response schema for status history entry."""

    id: UUID
    previous_status: Optional[str]
    new_status: str
    changed_by: Optional[UUID]
    reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class LoanStatisticsResponse(BaseModel):
    """Response schema for loan statistics."""

    # Total number of loans (all statuses)
    total_count: int
    # Explicit alias used by the frontend dashboard
    total_loans: int

    # Breakdown by status and country
    by_status: dict[str, int]
    by_country: dict[str, int]

    # Monetary statistics
    total_amount_requested: float
    average_amount: float

    # Risk / review statistics
    average_risk_score: Optional[float] = None
    pending_review_count: int
