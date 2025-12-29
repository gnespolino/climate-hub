"""Device control routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from climate_hub.acfreedom.exceptions import (
    DeviceNotFoundError,
    DeviceOfflineError,
    InvalidParameterError,
    ServerBusyError,
)
from climate_hub.acfreedom.manager import DeviceManager
from climate_hub.webapp.dependencies import get_device_manager
from climate_hub.webapp.models import (
    DeviceStatusDTO,
    FanCommand,
    ModeCommand,
    PowerCommand,
    TemperatureCommand,
)
from climate_hub.webapp.routes.devices import _to_dto

router = APIRouter(prefix="/devices")


@router.post("/{device_id}/power", response_model=DeviceStatusDTO)
async def set_power(
    device_id: str,
    command: PowerCommand,
    manager: Annotated[DeviceManager, Depends(get_device_manager)],
) -> DeviceStatusDTO:
    """Turn device on or off."""
    try:
        await manager.set_power(device_id, command.on)
        return _to_dto(manager.find_device(device_id))
    except (DeviceNotFoundError, DeviceOfflineError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e
    except ServerBusyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        ) from e


@router.post("/{device_id}/temperature", response_model=DeviceStatusDTO)
async def set_temperature(
    device_id: str,
    command: TemperatureCommand,
    manager: Annotated[DeviceManager, Depends(get_device_manager)],
) -> DeviceStatusDTO:
    """Set target temperature."""
    try:
        await manager.set_temperature(device_id, command.temperature)
        return _to_dto(manager.find_device(device_id))
    except (DeviceNotFoundError, DeviceOfflineError, InvalidParameterError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e
    except ServerBusyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        ) from e


@router.post("/{device_id}/mode", response_model=DeviceStatusDTO)
async def set_mode(
    device_id: str,
    command: ModeCommand,
    manager: Annotated[DeviceManager, Depends(get_device_manager)],
) -> DeviceStatusDTO:
    """Set operation mode."""
    try:
        await manager.set_mode(device_id, command.mode)
        return _to_dto(manager.find_device(device_id))
    except (DeviceNotFoundError, DeviceOfflineError, InvalidParameterError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e
    except ServerBusyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        ) from e


@router.post("/{device_id}/fan", response_model=DeviceStatusDTO)
async def set_fan_speed(
    device_id: str,
    command: FanCommand,
    manager: Annotated[DeviceManager, Depends(get_device_manager)],
) -> DeviceStatusDTO:
    """Set fan speed."""
    try:
        await manager.set_fan_speed(device_id, command.speed)
        return _to_dto(manager.find_device(device_id))
    except (DeviceNotFoundError, DeviceOfflineError, InvalidParameterError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e
    except ServerBusyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        ) from e
