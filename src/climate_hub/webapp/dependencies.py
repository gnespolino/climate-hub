"""Dependencies for the Web API."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from climate_hub.acfreedom.exceptions import AuthenticationError, ConfigurationError
from climate_hub.acfreedom.manager import DeviceManager
from climate_hub.cli.config import ConfigManager
from climate_hub.webapp.device_refresh import DeviceRefreshManager


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


async def get_device_manager(
    request: Request,
    config: Annotated[ConfigManager, Depends(get_config)],
) -> DeviceManager:
    """Get authenticated device manager from app state.

    This retrieves the DeviceManager instance that was initialized
    during application startup. If not already authenticated, it
    attempts to login using stored credentials.

    Args:
        request: FastAPI request object
        config: Config manager dependency

    Returns:
        Authenticated DeviceManager

    Raises:
        HTTPException: If credentials missing or authentication fails
    """
    device_manager: DeviceManager = request.app.state.device_manager

    # Check if already authenticated
    if device_manager.is_logged_in():
        return device_manager

    # Verify credentials exist
    if not config.has_credentials():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credentials not configured. Please run 'climate login' on the host.",
        )

    # Attempt login
    try:
        email, password = config.get_credentials()
        await device_manager.login(email, password)
    except (AuthenticationError, ConfigurationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e.message}",
        ) from e

    return device_manager


def get_refresh_manager(request: Request) -> DeviceRefreshManager:
    """Get device refresh manager from app state.

    Args:
        request: FastAPI request object

    Returns:
        DeviceRefreshManager instance from app state
    """
    refresh_manager: DeviceRefreshManager = request.app.state.refresh_manager
    return refresh_manager
