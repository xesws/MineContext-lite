"""FastAPI application entry point for MineContext-v2."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from backend.api.routes import router
from backend.api.analytics_routes import router as analytics_router
from backend.api.reports_routes import router as reports_router
from backend.api.todos_routes import router as todos_router
from backend.config import settings
from backend.database import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting MineContext-v2 server")
    logger.info(f"Database: {settings.storage.database_path}")
    logger.info(f"Screenshot directory: {settings.capture.screenshot_dir}")

    # Ensure directories exist
    Path(settings.capture.screenshot_dir).mkdir(parents=True, exist_ok=True)

    # Auto-start capture if configured
    if settings.capture.auto_start:
        from backend.capture import capture_service
        capture_service.start()
        logger.info("Screenshot capture auto-started")

    yield

    # Shutdown
    logger.info("Shutting down MineContext-v2 server")
    from backend.capture import capture_service
    if capture_service.is_running:
        capture_service.stop()
        logger.info("Screenshot capture stopped")


# Create FastAPI application
app = FastAPI(
    title="MineContext-v2",
    description="Lightweight context-aware AI application for screenshot capture and analysis",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")
app.include_router(analytics_router, prefix="/api", tags=["Analytics"])
app.include_router(reports_router, prefix="/api", tags=["Reports"])
app.include_router(todos_router, prefix="/api", tags=["TODOs"])

# Mount static directories
# Serve screenshots
screenshots_dir = Path(settings.capture.screenshot_dir)
if screenshots_dir.exists():
    app.mount("/screenshots", StaticFiles(directory=str(screenshots_dir)), name="screenshots")

# Serve frontend
frontend_dir = Path("frontend")
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from backend.capture import capture_service

    return {
        "status": "ok",
        "database_connected": True,
        "capture_running": capture_service.is_running,
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.server.host}:{settings.server.port}")
    uvicorn.run(
        "backend.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug,
    )
