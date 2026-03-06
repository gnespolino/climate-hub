"""MCP server exposing Climate Hub tools for AI assistants."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from climate_hub.acfreedom.control import DeviceControl
from climate_hub.acfreedom.coordinator import DeviceCoordinator
from climate_hub.acfreedom.exceptions import (
    ClimateHubError,
    DeviceNotFoundError,
    DeviceOfflineError,
    InvalidParameterError,
    ServerBusyError,
)

mcp = FastMCP("Climate Hub")

# The coordinator is injected at startup via set_coordinator()
_coordinator: DeviceCoordinator | None = None


def set_coordinator(coordinator: DeviceCoordinator) -> None:
    """Set the device coordinator for MCP tools."""
    global _coordinator
    _coordinator = coordinator


def _get_coordinator() -> DeviceCoordinator:
    if _coordinator is None:
        raise RuntimeError("DeviceCoordinator not initialized")
    return _coordinator


def _device_to_dict(device: Any) -> dict[str, Any]:
    """Convert a Device to a summary dict for MCP responses."""
    return {
        "endpoint_id": device.endpoint_id,
        "name": device.friendly_name,
        "online": device.is_online,
        "target_temperature": device.get_temperature_target(),
        "ambient_temperature": device.get_temperature_ambient(),
        "mode": DeviceControl.get_mode_name(device.params.get("ac_mode", -1)),
        "fan_speed": DeviceControl.get_fan_speed_name(device.params.get("ac_mark", -1)),
        "vertical_swing": device.params.get("ac_vdir") == 1,
        "horizontal_swing": device.params.get("ac_hdir") == 1,
    }


@mcp.tool
async def list_devices() -> list[dict[str, Any]]:
    """List all AC devices with their current status.

    Returns a list of all registered air conditioners with name, online status,
    temperature, mode, fan speed, and swing state.
    """
    coordinator = _get_coordinator()
    return [_device_to_dict(d) for d in coordinator.get_devices()]


@mcp.tool
async def get_device_status(device: str) -> dict[str, Any]:
    """Get the current status of a specific AC device.

    Args:
        device: Device name (or partial name, case-insensitive) or endpoint ID.
    """
    coordinator = _get_coordinator()
    try:
        return _device_to_dict(coordinator.find_device(device))
    except DeviceNotFoundError as e:
        return {"error": e.message}


@mcp.tool
async def turn_on(device: str) -> dict[str, Any]:
    """Turn on an air conditioner.

    Args:
        device: Device name (or partial name, case-insensitive) or endpoint ID.
    """
    coordinator = _get_coordinator()
    try:
        await coordinator.set_power(device, on=True)
        return _device_to_dict(coordinator.find_device(device))
    except (DeviceNotFoundError, DeviceOfflineError, ServerBusyError, ClimateHubError) as e:
        return {"error": e.message}


@mcp.tool
async def turn_off(device: str) -> dict[str, Any]:
    """Turn off an air conditioner.

    Args:
        device: Device name (or partial name, case-insensitive) or endpoint ID.
    """
    coordinator = _get_coordinator()
    try:
        await coordinator.set_power(device, on=False)
        return _device_to_dict(coordinator.find_device(device))
    except (DeviceNotFoundError, DeviceOfflineError, ServerBusyError, ClimateHubError) as e:
        return {"error": e.message}


@mcp.tool
async def set_temperature(device: str, temperature: float) -> dict[str, Any]:
    """Set the target temperature of an air conditioner.

    Args:
        device: Device name (or partial name, case-insensitive) or endpoint ID.
        temperature: Target temperature in Celsius (16-30, supports 0.5 increments).
    """
    coordinator = _get_coordinator()
    try:
        await coordinator.set_temperature(device, temperature)
        return _device_to_dict(coordinator.find_device(device))
    except (
        DeviceNotFoundError,
        DeviceOfflineError,
        InvalidParameterError,
        ServerBusyError,
        ClimateHubError,
    ) as e:
        return {"error": e.message}


@mcp.tool
async def set_mode(device: str, mode: str) -> dict[str, Any]:
    """Set the operating mode of an air conditioner.

    Args:
        device: Device name (or partial name, case-insensitive) or endpoint ID.
        mode: Operating mode - one of: cool, heat, dry, fan, auto.
    """
    coordinator = _get_coordinator()
    try:
        await coordinator.set_mode(device, mode)
        return _device_to_dict(coordinator.find_device(device))
    except (
        DeviceNotFoundError,
        DeviceOfflineError,
        InvalidParameterError,
        ServerBusyError,
        ClimateHubError,
    ) as e:
        return {"error": e.message}


@mcp.tool
async def set_fan_speed(device: str, speed: str) -> dict[str, Any]:
    """Set the fan speed of an air conditioner.

    Args:
        device: Device name (or partial name, case-insensitive) or endpoint ID.
        speed: Fan speed - one of: auto, low, medium, high, turbo, mute.
    """
    coordinator = _get_coordinator()
    try:
        await coordinator.set_fan_speed(device, speed)
        return _device_to_dict(coordinator.find_device(device))
    except (
        DeviceNotFoundError,
        DeviceOfflineError,
        InvalidParameterError,
        ServerBusyError,
        ClimateHubError,
    ) as e:
        return {"error": e.message}


@mcp.tool
async def set_swing(device: str, direction: str, on: bool) -> dict[str, Any]:
    """Set the swing (oscillation) of an air conditioner.

    Args:
        device: Device name (or partial name, case-insensitive) or endpoint ID.
        direction: Swing direction - one of: vertical, horizontal.
        on: True to enable swing, False to disable.
    """
    coordinator = _get_coordinator()
    try:
        await coordinator.set_swing(device, direction, on)
        return _device_to_dict(coordinator.find_device(device))
    except (
        DeviceNotFoundError,
        DeviceOfflineError,
        InvalidParameterError,
        ServerBusyError,
        ClimateHubError,
    ) as e:
        return {"error": e.message}
