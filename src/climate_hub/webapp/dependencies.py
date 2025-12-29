"""Dependencies for the Web API."""

from __future__ import annotations

import functools
from typing import Annotated

from fastapi import Depends, HTTPException, status

from climate_hub.acfreedom.exceptions import AuthenticationError, ConfigurationError
from climate_hub.acfreedom.manager import DeviceManager
from climate_hub.cli.config import ConfigManager

# Global managers for reuse
_config_manager = ConfigManager()
_device_manager = DeviceManager(region=_config_manager.get_region())


@functools.lru_cache
def get_config() -> ConfigManager:
    """Get configuration manager.

    Returns:
        ConfigManager instance
    """
    return _config_manager


async def get_device_manager(
    config: Annotated[ConfigManager, Depends(get_config)],
) -> DeviceManager:
    """Get authenticated device manager.

    Args:
        config: Config manager dependency

    Returns:
        Authenticated DeviceManager

    Raises:
        HTTPException: If authentication fails
    """
    if not config.has_credentials():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credentials not configured. Please run 'climate login' on the host.",
        )

    if not _device_manager.is_logged_in():
        try:
            email, password = config.get_credentials()
            await _device_manager.login(email, password)
        except (AuthenticationError, ConfigurationError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {e.message}",
            ) from e

    return _device_manager
