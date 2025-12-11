"""Webhooks API Schemas."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BankingWebhookPayload(BaseModel):
    """
    Webhook payload from banking providers.

    Different providers may send different fields,
    but all should include these common fields.
    """

    event_type: str = Field(
        ...,
        description="Type of event (status_update, risk_assessment, verification)",
        examples=["status_update"],
    )
    loan_reference: str = Field(
        ...,
        description="Reference to the loan (usually our loan_id or document_hash)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    timestamp: datetime = Field(
        ...,
        description="When the event occurred at the provider",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data",
    )

    # Optional fields that some providers may include
    provider_reference: Optional[str] = Field(
        None,
        description="Provider's internal reference",
    )
    status: Optional[str] = Field(
        None,
        description="New status (for status_update events)",
    )
    risk_score: Optional[int] = Field(
        None,
        ge=0,
        le=1000,
        description="Risk score (for risk_assessment events)",
    )


class WebhookResponse(BaseModel):
    """Response schema for webhook processing."""

    received: bool = Field(
        True,
        description="Whether the webhook was received",
    )
    event_id: UUID = Field(
        ...,
        description="ID of the created webhook event",
    )
    processed: bool = Field(
        ...,
        description="Whether the webhook was processed immediately",
    )
    message: str = Field(
        ...,
        description="Processing result message",
    )


class WebhookErrorResponse(BaseModel):
    """Error response for webhook failures."""

    received: bool = False
    error: str
    details: Optional[dict[str, Any]] = None


class WebhookEventResponse(BaseModel):
    """Response schema for webhook event details."""

    id: UUID
    source: str
    event_type: str
    processed: bool
    processed_at: Optional[datetime]
    processing_error: Optional[str]
    loan_id: Optional[UUID]
    created_at: datetime

    model_config = {"from_attributes": True}
