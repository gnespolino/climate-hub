"""Device control logic and validation."""

from __future__ import annotations

from typing import cast

from climate_hub.acfreedom.exceptions import InvalidParameterError
from climate_hub.api import constants as C
from climate_hub.api.models import ACFanSpeed, ACMode


class DeviceControl:
    """Device control logic with validation."""

    # Temperature constants
    MIN_TEMPERATURE = 16
    MAX_TEMPERATURE = 30

    # Mode mappings (string to API dict)
    MODE_MAP = {
        "cool": C.AC_MODE_COOLING,
        "heat": C.AC_MODE_HEATING,
        "dry": C.AC_MODE_DRY,
        "fan": C.AC_MODE_FAN,
        "auto": C.AC_MODE_AUTO,
    }

    # Mode names (int to string)
    MODE_NAMES = {
        ACMode.COOLING: "Cooling",
        ACMode.HEATING: "Heating",
        ACMode.DRY: "Dry",
        ACMode.FAN: "Fan",
        ACMode.AUTO: "Auto",
    }

    # Fan speed mappings (string to int)
    FAN_SPEED_MAP = {
        "auto": ACFanSpeed.AUTO,
        "low": ACFanSpeed.LOW,
        "medium": ACFanSpeed.MEDIUM,
        "high": ACFanSpeed.HIGH,
        "turbo": ACFanSpeed.TURBO,
        "mute": ACFanSpeed.MUTE,
    }

    # Fan speed names (int to string)
    FAN_SPEED_NAMES = {
        ACFanSpeed.AUTO: "Auto",
        ACFanSpeed.LOW: "Low",
        ACFanSpeed.MEDIUM: "Medium",
        ACFanSpeed.HIGH: "High",
        ACFanSpeed.TURBO: "Turbo",
        ACFanSpeed.MUTE: "Mute",
    }

    @staticmethod
    def validate_temperature(temperature: float) -> None:
        """Validate temperature is in valid range.

        Args:
            temperature: Temperature in Celsius (supports 0.5 increments)

        Raises:
            InvalidParameterError: If temperature is out of range
        """
        if not (DeviceControl.MIN_TEMPERATURE <= temperature <= DeviceControl.MAX_TEMPERATURE):
            raise InvalidParameterError(
                "temperature",
                temperature,
                [f"{DeviceControl.MIN_TEMPERATURE}-{DeviceControl.MAX_TEMPERATURE}°C"],
            )

    @staticmethod
    def celsius_to_api(celsius: int) -> int:
        """Convert Celsius to API format (tenths of degrees).

        Args:
            celsius: Temperature in Celsius

        Returns:
            Temperature in tenths (e.g., 22 -> 220)
        """
        return celsius * 10

    @staticmethod
    def api_to_celsius(api_temp: int) -> float:
        """Convert API temperature to Celsius.

        Args:
            api_temp: Temperature in tenths

        Returns:
            Temperature in Celsius (e.g., 220 -> 22.0)
        """
        return api_temp / 10.0

    @staticmethod
    def validate_mode(mode: str) -> dict[str, int]:
        """Validate and convert mode string to API dict.

        Args:
            mode: Mode string (cool, heat, dry, fan, auto)

        Returns:
            API mode dictionary

        Raises:
            InvalidParameterError: If mode is invalid
        """
        mode_lower = mode.lower()
        if mode_lower not in DeviceControl.MODE_MAP:
            raise InvalidParameterError("mode", mode, list(DeviceControl.MODE_MAP.keys()))
        return DeviceControl.MODE_MAP[mode_lower]

    @staticmethod
    def get_mode_name(mode: int) -> str:
        """Get human-readable mode name.

        Args:
            mode: Mode integer from API

        Returns:
            Mode name string
        """
        return DeviceControl.MODE_NAMES.get(cast(ACMode, mode), f"Unknown ({mode})")

    @staticmethod
    def validate_fan_speed(speed: str) -> dict[str, int]:
        """Validate and convert fan speed string to API dict.

        Args:
            speed: Fan speed string (auto, low, medium, high, turbo, mute)

        Returns:
            API fan speed dictionary

        Raises:
            InvalidParameterError: If speed is invalid
        """
        speed_lower = speed.lower()
        if speed_lower not in DeviceControl.FAN_SPEED_MAP:
            raise InvalidParameterError(
                "fan_speed", speed, list(DeviceControl.FAN_SPEED_MAP.keys())
            )
        return {C.AC_FAN_SPEED: DeviceControl.FAN_SPEED_MAP[speed_lower]}

    @staticmethod
    def get_fan_speed_name(speed: int) -> str:
        """Get human-readable fan speed name.

        Args:
            speed: Fan speed integer from API

        Returns:
            Fan speed name string
        """
        return DeviceControl.FAN_SPEED_NAMES.get(cast(ACFanSpeed, speed), f"Unknown ({speed})")

    @staticmethod
    def validate_swing_direction(direction: str) -> None:
        """Validate swing direction.

        Args:
            direction: Direction string (vertical, horizontal)

        Raises:
            InvalidParameterError: If direction is invalid
        """
        if direction.lower() not in ["vertical", "horizontal"]:
            raise InvalidParameterError("swing_direction", direction, ["vertical", "horizontal"])

    @staticmethod
    def get_swing_params(direction: str, state: bool) -> dict[str, int]:
        """Get swing parameters for API.

        Args:
            direction: Direction (vertical, horizontal)
            state: True for on, False for off

        Returns:
            API swing parameters
        """
        if direction.lower() == "vertical":
            return C.AC_SWING_VERTICAL_ON if state else C.AC_SWING_VERTICAL_OFF
        return C.AC_SWING_HORIZONTAL_ON if state else C.AC_SWING_HORIZONTAL_OFF
