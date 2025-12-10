"""API v1 main router."""
from fastapi import APIRouter

from app.api.v1.health.router import router as health_router

api_router = APIRouter()

# Include health check routes
api_router.include_router(health_router)

# TODO: Include additional routers
# api_router.include_router(auth_router.router)
# api_router.include_router(loans_router.router)
# api_router.include_router(webhooks_router.router)
