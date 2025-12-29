"""Device lookup and management utilities."""

from __future__ import annotations

from climate_hub.acfreedom.exceptions import DeviceNotFoundError
from climate_hub.api.models import Device


class DeviceFinder:
    """Utilities for finding and filtering devices."""

    @staticmethod
    def find_device(devices: list[Device], device_id: str) -> Device:
        """Find device by ID or name.

        Tries in order:
        1. Exact endpoint ID match
        2. Exact friendly name match (case-insensitive)
        3. Partial friendly name match (case-insensitive substring)

        Args:
            devices: List of devices to search
            device_id: Device ID or name to search for

        Returns:
            Matching device

        Raises:
            DeviceNotFoundError: If no device found
        """
        if not devices:
            raise DeviceNotFoundError(device_id)

        # Try exact ID match
        for device in devices:
            if device.endpoint_id == device_id:
                return device

        # Try exact name match (case-insensitive)
        device_id_lower = device_id.lower()
        for device in devices:
            if device.friendly_name.lower() == device_id_lower:
                return device

        # Try partial name match (case-insensitive substring)
        for device in devices:
            if device_id_lower in device.friendly_name.lower():
                return device

        raise DeviceNotFoundError(device_id)

    @staticmethod
    def filter_online(devices: list[Device]) -> list[Device]:
        """Filter for only online devices.

        Args:
            devices: List of devices

        Returns:
            List of online devices only
        """
        return [d for d in devices if d.is_online]

    @staticmethod
    def filter_by_type(devices: list[Device], device_type: str) -> list[Device]:
        """Filter devices by type.

        Args:
            devices: List of devices
            device_type: Device type to filter for

        Returns:
            List of matching devices
        """
        return [d for d in devices if d.device_type == device_type]
