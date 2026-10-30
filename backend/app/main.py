from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models, database
from app.core.config import settings
from app.core.errors import AegisException, aegis_exception_handler, generic_exception_handler
from app.core.ws_manager import ws_manager
from app.api.v1 import api_router
from app.api.v1.endpoints.ws import router as ws_router

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aegis.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database table initialization and shutdown."""
    logger.info("Initializing Aegis Engine database models...")
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Aegis Engine platform started successfully.")
    yield
    logger.info("Aegis Engine platform shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-Agent Reliability, Evaluation, and Adversarial Testing Engine",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AegisException, aegis_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(ws_router)  # Mounted at /ws/traces


# Root & Health Check Endpoints
@app.get("/", tags=["Health"])
def read_root():
    """Health check root endpoint."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Service health and connectivity check."""
    return {
        "status": "healthy",
        "database": "connected",
        "active_ws_clients": len(ws_manager.active_connections),
    }


# Backwards compatibility alias for websocket connection manager
manager = ws_manager
