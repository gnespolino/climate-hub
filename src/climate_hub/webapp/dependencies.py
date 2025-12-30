"""Dependencies for the Web API."""

from __future__ import annotations

from fastapi import Request

from climate_hub.acfreedom.coordinator import DeviceCoordinator
from climate_hub.cli.config import ConfigManager


def get_config(request: Request) -> ConfigManager:
    """Get configuration manager from app state.

    This retrieves the ConfigManager instance that was initialized
    during application startup in the lifespan event handler.

    Args:
        request: FastAPI request object

    Returns:
        ConfigManager instance from app state
    """
    config: ConfigManager = request.app.state.config
    return config


def get_coordinator(
    request: Request,
) -> DeviceCoordinator:
    """Get device coordinator from app state.

    Args:
        request: FastAPI request object

    Returns:
        DeviceCoordinator instance from app state
    """
    coordinator: DeviceCoordinator = request.app.state.coordinator
    return coordinator
