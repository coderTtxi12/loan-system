"""API v1 main router."""
from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.health.router import router as health_router
from app.api.v1.loans.router import router as loans_router
from app.api.v1.webhooks.router import router as webhooks_router

api_router = APIRouter()

# Include health check routes
api_router.include_router(health_router)

# Include auth routes
api_router.include_router(auth_router)

# Include loans routes
api_router.include_router(loans_router)

# Include webhooks routes
api_router.include_router(webhooks_router)
