"""Pydantic models for the Web API."""

from __future__ import annotations

from typing import Any

from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseWebModel(BaseModel):
    """Base model with camelCase aliasing for Web API."""

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        populate_by_name=True,
    )


class DeviceStatusDTO(BaseWebModel):
    """Device status data transfer object."""

    endpoint_id: str
    friendly_name: str
    is_online: bool
    state: int
    last_updated: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    # Enriched fields
    target_temperature: float | None = None
    ambient_temperature: float | None = None
    mode: str | None = None
    fan_speed: str | None = None


class DeviceListResponse(BaseModel):
    """Response model for device list."""

    devices: list[DeviceStatusDTO]


class PowerCommand(BaseWebModel):
    """Command to set power state."""

    on: bool


class TemperatureCommand(BaseWebModel):
    """Command to set temperature."""

    temperature: int = Field(ge=16, le=30)


class ModeCommand(BaseWebModel):
    """Command to set mode."""

    mode: str  # cool, heat, dry, fan, auto


class FanCommand(BaseWebModel):
    """Command to set fan speed."""

    speed: str  # auto, low, medium, high, turbo, mute
