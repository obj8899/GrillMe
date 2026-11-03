"""Health check route for GrillMe backend."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.config import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Schema for service health status."""

    status: str
    service: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse, summary="Service health check")
def health_check() -> HealthResponse:
    """Return health status of the GrillMe backend API."""
    return HealthResponse(
        status="healthy",
        service="grillme-backend",
        version=settings.version,
        environment=settings.environment,
    )
