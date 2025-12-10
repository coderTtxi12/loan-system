"""Health check endpoints."""
from datetime import datetime

from fastapi import APIRouter, status

from app.api.v1.health.schemas import HealthDetailResponse, HealthResponse
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Returns the basic health status of the API",
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.

    Returns:
        HealthResponse: Basic health status with timestamp and version.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/ready",
    response_model=HealthDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Returns detailed health status including database and cache connectivity",
)
async def readiness_check() -> HealthDetailResponse:
    """
    Readiness check endpoint for Kubernetes.

    Checks connectivity to:
    - PostgreSQL database
    - Redis cache

    Returns:
        HealthDetailResponse: Detailed health status including dependencies.
    """
    # TODO: Implement actual database and redis connectivity checks in Commit 3
    # For now, return simulated status
    db_status = "connected"
    redis_status = "connected"

    overall_status = (
        "healthy" if db_status == "connected" and redis_status == "connected" else "unhealthy"
    )

    return HealthDetailResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        redis=redis_status,
        details={
            "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "configured",
            "redis_url": settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL,
        },
    )
