"""Device management routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from climate_hub.acfreedom.control import DeviceControl
from climate_hub.acfreedom.exceptions import DeviceNotFoundError
from climate_hub.acfreedom.manager import DeviceManager
from climate_hub.api.models import Device
from climate_hub.webapp.dependencies import get_device_manager
from climate_hub.webapp.models import DeviceListResponse, DeviceStatusDTO

router = APIRouter(prefix="/devices")


def _to_dto(device: Device) -> DeviceStatusDTO:
    """Convert Device model to DTO with enriched fields.

    Args:
        device: Source device model

    Returns:
        Enriched DTO
    """
    return DeviceStatusDTO(
        endpoint_id=device.endpoint_id,
        friendly_name=device.friendly_name,
        is_online=device.is_online,
        state=device.state,
        last_updated=device.last_updated,
        params=device.params,
        target_temperature=device.get_temperature_target(),
        ambient_temperature=device.get_temperature_ambient(),
        mode=DeviceControl.get_mode_name(device.params.get("ac_mode", -1)),
        fan_speed=DeviceControl.get_fan_speed_name(device.params.get("ac_mark", -1)),
    )


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    manager: Annotated[DeviceManager, Depends(get_device_manager)],
    shared: bool = False,
    refresh: bool = False,
) -> DeviceListResponse:
    """List all available devices with caching.

    By default, returns cached devices (TTL: 30s) to reduce API calls.
    Use ?refresh=true to force fresh data from API.

    Args:
        manager: Device manager dependency
        shared: Whether to include shared devices
        refresh: Force refresh from API (bypass cache)

    Returns:
        List of devices (cached or fresh)

    Example:
        GET /devices              # Use cache (30s TTL)
        GET /devices?refresh=true # Force API refresh
    """
    # Force refresh if requested (ttl=0 bypasses cache)
    ttl = 0 if refresh else 30

    devices = await manager.get_devices_cached(shared=shared, ttl=ttl)
    return DeviceListResponse(devices=[_to_dto(d) for d in devices])


@router.get("/{device_id}", response_model=DeviceStatusDTO)
async def get_device(
    device_id: str,
    manager: Annotated[DeviceManager, Depends(get_device_manager)],
    refresh: bool = False,
) -> DeviceStatusDTO:
    """Get detailed status of a specific device with full parameters.

    This endpoint always fetches device parameters to provide complete information
    for frontend rendering. Uses cache for device list but fetches params on-demand.

    Args:
        device_id: Device ID or name
        manager: Device manager dependency
        refresh: Force full refresh from API (bypass cache)

    Returns:
        Device status with complete parameters

    Raises:
        HTTPException: If device not found

    Example:
        GET /devices/living_room              # Use cached list + fetch params
        GET /devices/living_room?refresh=true # Full API refresh
    """
    try:
        # Use cache by default, force refresh if requested
        ttl = 0 if refresh else 60
        # Always fetch params for single device to ensure complete data
        fetch_params = refresh

        # Get devices (from cache or API)
        await manager.get_devices_cached(ttl=ttl, fetch_params=fetch_params)
        device = manager.find_device(device_id)

        # If params are missing (not in cache), fetch them now
        if not device.params and device.is_online:
            await manager.fetch_device_params(device)

        return _to_dto(device)
    except DeviceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e
