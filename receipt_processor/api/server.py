import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn

from .endpoints import upload, receipts, passes
from ..agent import receipt_processor_system
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Receipt Processor API Server")
    logger.info(f"System components: {await receipt_processor_system.get_system_status()}")

    yield  # Application is running

    # Shutdown
    logger.info("Shutting down Receipt Processor API Server")

# Create FastAPI application
app = FastAPI(
    title="Receipt Processor API",
    description="Multi-agent receipt processing system with wallet pass generation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api/v1")
app.include_router(receipts.router, prefix="/api/v1")
app.include_router(passes.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Receipt Processor API",
        "version": "1.0.0",
        "description": "Multi-agent receipt processing system",
        "endpoints": {
            "upload": "/api/v1/upload",
            "receipts": "/api/v1/receipts",
            "passes": "/api/v1/passes",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        system_status = await receipt_processor_system.get_system_status()
        return {
            "status": "healthy",
            "timestamp": system_status["timestamp"],
            "components": system_status["components"],
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "version": "1.0.0"
        }


@app.get("/system/status")
async def get_system_status():
    """Get detailed system status."""
    return await receipt_processor_system.get_system_status()

# Development server function


def run_dev_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True
):
    """Run the development server."""
    uvicorn.run(
        "receipt_processor.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_dev_server()
