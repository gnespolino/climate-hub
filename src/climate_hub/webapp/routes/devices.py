"""Device management routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from climate_hub.acfreedom.control import DeviceControl
from climate_hub.acfreedom.coordinator import DeviceCoordinator
from climate_hub.acfreedom.exceptions import DeviceNotFoundError
from climate_hub.api.models import Device
from climate_hub.webapp.dependencies import get_coordinator
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
    coordinator: Annotated[DeviceCoordinator, Depends(get_coordinator)],
) -> DeviceListResponse:
    """List all available devices from cache.

    ALWAYS returns cached devices. Never triggers API calls.
    Cache is populated and maintained by DeviceCoordinator.

    Args:
        coordinator: Device coordinator dependency

    Returns:
        List of devices from cache
    """
    devices = coordinator.get_devices()
    return DeviceListResponse(devices=[_to_dto(d) for d in devices])


@router.get("/{device_id}", response_model=DeviceStatusDTO)
async def get_device(
    device_id: str,
    coordinator: Annotated[DeviceCoordinator, Depends(get_coordinator)],
) -> DeviceStatusDTO:
    """Get detailed status of a specific device from cache.

    ALWAYS returns from cache. Never triggers API calls.
    Cache is populated and maintained by DeviceCoordinator.

    Args:
        device_id: Device ID or name
        coordinator: Device coordinator dependency

    Returns:
        Device status from cache

    Raises:
        HTTPException: If device not found
    """
    try:
        device = coordinator.find_device(device_id)
        return _to_dto(device)
    except DeviceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e
