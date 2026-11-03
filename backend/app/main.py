"""Main FastAPI application entry point for GrillMe."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import health
from backend.app.core.config import settings


def create_application() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    application = FastAPI(
        title=settings.project_name,
        version=settings.version,
        description=settings.description,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routes
    application.include_router(health.router, prefix="/api")
    application.include_router(health.router)  # Also expose /health at top level

    @application.get("/", tags=["root"], summary="API root information")
    def root() -> dict[str, str]:
        """Root endpoint returning basic service information."""
        return {
            "name": settings.project_name,
            "version": settings.version,
            "status": "running",
            "docs": "/docs",
        }

    return application


app = create_application()
