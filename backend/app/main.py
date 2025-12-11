"""FastAPI Application Entry Point."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import socketio
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.cache import cache
from app.core.config import settings
from app.core.exceptions import BaseAPIException
from app.sockets.handlers import sio
from app.sockets.pg_listener import start_pg_listener, stop_pg_listener

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize Redis cache
    try:
        await cache.connect()
        logger.info("Redis cache connected")
    except Exception as e:
        logger.warning(f"Redis cache not available: {e}")

    # Start PostgreSQL LISTEN for real-time updates
    try:
        await start_pg_listener()
        logger.info("PostgreSQL listener started")
    except Exception as e:
        logger.warning(f"PostgreSQL listener not available: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Stop PostgreSQL listener
    try:
        await stop_pg_listener()
    except Exception as e:
        logger.warning(f"Error stopping PostgreSQL listener: {e}")

    # Disconnect Redis cache
    try:
        await cache.disconnect()
    except Exception as e:
        logger.warning(f"Error disconnecting Redis: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    🏦 **Loan System API** - Sistema de gestión de solicitudes de préstamos multipaís.

    ## Países Soportados
    - 🇪🇸 España (ES) - DNI
    - 🇲🇽 México (MX) - CURP
    - 🇨🇴 Colombia (CO) - CC
    - 🇧🇷 Brasil (BR) - CPF

    ## Funcionalidades
    - Crear solicitudes de crédito
    - Validar reglas de negocio por país
    - Integración con proveedores bancarios
    - Actualización de estados
    - Real-time updates via WebSocket
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(BaseAPIException)
async def base_api_exception_handler(
    request: Request, exc: BaseAPIException
) -> JSONResponse:
    """Handle custom API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "errors": exc.errors,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "errors": [],
            "details": {"error": str(exc)} if settings.DEBUG else {},
        },
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint.

    Returns basic information about the API.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "websocket": "/socket.io",
    }


# Configure Socket.IO CORS
sio.eio.cors_allowed_origins = settings.cors_origins_list

# Create combined ASGI app with Socket.IO
socket_app = socketio.ASGIApp(sio, app)
