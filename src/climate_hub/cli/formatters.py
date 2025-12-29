"""Output formatting utilities for CLI."""

from __future__ import annotations

from climate_hub.acfreedom.control import DeviceControl
from climate_hub.api.models import Device


class OutputFormatter:
    """Format output for CLI display."""

    @staticmethod
    def format_device_list(devices: list[Device]) -> str:
        """Format device list for display.

        Args:
            devices: List of devices

        Returns:
            Formatted string
        """
        if not devices:
            return "No devices found."

        lines = [f"\nFound {len(devices)} device(s):\n"]

        for i, device in enumerate(devices, 1):
            lines.append(f"{i}. {device.friendly_name}")
            lines.append(f"   ID: {device.endpoint_id}")
            lines.append(f"   Online: {'Yes' if device.is_online else 'No'}")

            if device.is_online and device.params:
                power = device.params.get("pwr")
                temp_target = device.get_temperature_target()
                temp_ambient = device.get_temperature_ambient()

                if power is not None:
                    lines.append(f"   Power: {'ON' if power == 1 else 'OFF'}")
                if temp_target is not None:
                    ambient_str = f" (Ambient: {temp_ambient}°C)" if temp_ambient else ""
                    lines.append(f"   Temperature: {temp_target}°C{ambient_str}")

            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_device_status(device: Device) -> str:
        """Format detailed device status.

        Args:
            device: Device object

        Returns:
            Formatted string
        """
        lines = [
            f"\nDevice: {device.friendly_name}",
            f"ID: {device.endpoint_id}",
            f"Online: {'Yes' if device.is_online else 'No'}\n",
        ]

        if not device.is_online:
            lines.append("Device is offline.")
            return "\n".join(lines)

        params = device.params

        # Power status
        power = params.get("pwr")
        if power is not None:
            lines.append(f"Power: {'ON' if power == 1 else 'OFF'}")

        # Temperature
        temp_target = device.get_temperature_target()
        temp_ambient = device.get_temperature_ambient()
        if temp_target is not None:
            lines.append(f"Target Temperature: {temp_target}°C")
        if temp_ambient is not None:
            lines.append(f"Ambient Temperature: {temp_ambient}°C")

        # Mode
        mode = params.get("ac_mode")
        if mode is not None:
            mode_name = DeviceControl.get_mode_name(mode)
            lines.append(f"Mode: {mode_name}")

        # Fan speed
        fan = params.get("ac_mark")
        if fan is not None:
            fan_name = DeviceControl.get_fan_speed_name(fan)
            lines.append(f"Fan Speed: {fan_name}")

        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def format_success(message: str) -> str:
        """Format success message.

        Args:
            message: Success message

        Returns:
            Formatted string
        """
        return f"✓ {message}"

    @staticmethod
    def format_error(message: str) -> str:
        """Format error message.

        Args:
            message: Error message

        Returns:
            Formatted string
        """
        return f"✗ {message}"
