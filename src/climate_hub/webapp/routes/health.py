"""Health check endpoint."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from climate_hub import __version__
from climate_hub.acfreedom.coordinator import DeviceCoordinator
from climate_hub.cli.config import ConfigManager
from climate_hub.webapp.dependencies import get_config

logger = logging.getLogger(__name__)

router = APIRouter()


class ServiceStatus(BaseModel):
    """Status of a service component."""

    available: bool
    message: str | None = None


class HealthResponse(BaseModel):
    """Comprehensive health check response."""

    status: str = Field(description="Overall health status: healthy, degraded, or unhealthy")
    version: str = Field(description="Application version")
    config: ServiceStatus = Field(description="Configuration service status")
    authentication: ServiceStatus = Field(description="Authentication status")
    cloud_api: ServiceStatus = Field(description="Cloud API connectivity status")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    config: Annotated[ConfigManager, Depends(get_config)],
) -> HealthResponse:
    """Comprehensive health check endpoint.

    Checks:
    - Application version
    - Configuration availability
    - Credentials configuration
    - Cloud API connectivity (if authenticated)

    Args:
        request: FastAPI request object
        config: Configuration manager dependency

    Returns:
        Detailed health status
    """
    # Check configuration
    config_status = ServiceStatus(available=True, message="Configuration loaded successfully")

    # Check authentication/credentials
    auth_status = ServiceStatus(available=False, message="No credentials configured")
    if config.has_credentials():
        auth_status = ServiceStatus(available=True, message="Credentials configured")

    # Check cloud API connectivity
    cloud_status = ServiceStatus(available=False, message="Not authenticated")
    coordinator: DeviceCoordinator | None = getattr(request.app.state, "coordinator", None)

    if coordinator and coordinator.api.is_logged_in():
        try:
            # Quick health check: try to get families (lightweight operation)
            await coordinator.api.get_families()
            cloud_status = ServiceStatus(available=True, message="Cloud API responding")
            logger.debug("Cloud API health check passed")
        except Exception as e:
            cloud_status = ServiceStatus(
                available=False, message=f"Cloud API error: {type(e).__name__}"
            )
            logger.warning(f"Cloud API health check failed: {e}")

    # Determine overall status
    if cloud_status.available and auth_status.available:
        overall_status = "healthy"
    elif auth_status.available:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        version=__version__,
        config=config_status,
        authentication=auth_status,
        cloud_api=cloud_status,
    )
