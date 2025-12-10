"""Health check schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""

    status: str = Field(
        ...,
        description="Health status of the service",
        examples=["healthy", "unhealthy"],
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the health check",
    )
    version: str = Field(
        ...,
        description="Application version",
    )
    environment: str = Field(
        ...,
        description="Current environment",
    )


class HealthDetailResponse(HealthResponse):
    """Detailed health check response including dependencies."""

    database: str = Field(
        ...,
        description="Database connection status",
        examples=["connected", "disconnected"],
    )
    redis: str = Field(
        ...,
        description="Redis connection status",
        examples=["connected", "disconnected"],
    )
    details: Optional[dict] = Field(
        default=None,
        description="Additional health check details",
    )
