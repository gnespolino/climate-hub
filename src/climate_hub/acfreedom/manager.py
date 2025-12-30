"""Device manager for orchestrating API operations."""

from __future__ import annotations

import logging
import time
from collections.abc import Coroutine
from typing import Any, TypeVar

from climate_hub.acfreedom.control import DeviceControl
from climate_hub.acfreedom.device import DeviceFinder
from climate_hub.acfreedom.exceptions import (
    AuthenticationError,
    ClimateHubError,
    DeviceOfflineError,
    ServerBusyError,
)
from climate_hub.api.client import AuxCloudAPI
from climate_hub.api.exceptions import (
    AuthenticationError as APIAuthError,
)
from climate_hub.api.exceptions import (
    AuxAPIError,
)
from climate_hub.api.exceptions import (
    DataError as APIDataError,
)
from climate_hub.api.exceptions import (
    DeviceOfflineError as APIDeviceOfflineError,
)
from climate_hub.api.exceptions import (
    ServerBusyError as APIServerBusyError,
)
from climate_hub.api.models import AuxProducts, Device, Family

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DeviceManager:
    """High-level device management and orchestration."""

    def __init__(self, api_client: AuxCloudAPI | None = None, region: str = "eu") -> None:
        """Initialize device manager.

        Args:
            api_client: API client instance (created if not provided)
            region: API region if creating new client
        """
        self.api = api_client or AuxCloudAPI(region=region)
        self.families: list[Family] = []
        self.devices: list[Device] = []

        # Cache management
        self._cache_timestamp: float = 0.0
        self._cache_ttl: int = 60  # seconds (increased from 30 to reduce API calls)

    async def login(self, email: str, password: str) -> bool:
        """Login to AUX cloud.

        Args:
            email: User email
            password: User password

        Returns:
            True if login successful

        Raises:
            AuthenticationError: If login fails
            ServerBusyError: If server is busy
            ClimateHubError: For other errors
        """
        return await self._wrap_api_call(self.api.login(email, password))

    def is_logged_in(self) -> bool:
        """Check if logged in.

        Returns:
            True if logged in
        """
        return self.api.is_logged_in()

    async def refresh_devices(self, shared: bool = False) -> list[Device]:
        """Refresh and return all devices with full parameters.

        ALWAYS fetches complete device parameters.

        Args:
            shared: Include shared devices

        Returns:
            List of devices with full parameters

        Raises:
            ClimateHubError: If request fails
        """

        async def _refresh() -> list[Device]:
            families_data = await self.api.get_families()

            all_devices: list[Device] = []

            for family_data in families_data:
                family_id = family_data["familyid"]
                # Always fetch params
                devices_data = await self._get_devices_for_family(
                    family_id, shared, fetch_params=True
                )
                all_devices.extend(devices_data)

            self.devices = all_devices
            return all_devices

        return await self._wrap_api_call(_refresh())

    def get_devices(self) -> list[Device]:
        """Get devices from cache (read-only).

        This method ALWAYS returns cached devices and NEVER triggers API calls.
        Cache is populated and maintained by DeviceRefreshManager only.

        Returns:
            List of cached devices (may be empty if not yet initialized)

        Example:
            # Get devices from cache
            devices = manager.get_devices()
        """
        logger.debug(f"Cache READ: returning {len(self.devices)} devices")
        return self.devices

    def invalidate_cache(self) -> None:
        """Force cache invalidation.

        Call this after modifying device state (e.g., turning on/off,
        changing temperature) to ensure next request gets fresh data.

        Example:
            await manager.set_temperature("living_room", 22)
            manager.invalidate_cache()  # Next get_devices_cached() will refresh
        """
        logger.debug("Cache invalidated - next request will refresh from API")
        self._cache_timestamp = 0.0

    async def _wrap_api_call(self, coro: Coroutine[Any, Any, T]) -> T:
        """Wrap API call to map exceptions.

        Args:
            coro: Coroutine to execute

        Returns:
            Result of coroutine

        Raises:
            ServerBusyError: If server is busy
            DeviceOfflineError: If device is offline
            ClimateHubError: For other API errors
        """
        try:
            result = await coro
            return result
        except APIServerBusyError:
            raise ServerBusyError() from None
        except APIDeviceOfflineError as e:
            # Extract device info from the exception if available
            raise ClimateHubError(str(e)) from e
        except APIDataError as e:
            raise ClimateHubError(str(e)) from e
        except APIAuthError as e:
            raise AuthenticationError(str(e)) from e
        except AuxAPIError as e:
            raise ClimateHubError(str(e)) from e

    async def _get_devices_for_family(
        self, family_id: str, shared: bool = False, fetch_params: bool = True
    ) -> list[Device]:
        """Get devices for a specific family.

        Args:
            family_id: Family ID
            shared: Include shared devices
            fetch_params: Whether to fetch device parameters

        Returns:
            List of Device objects
        """
        # Get device list
        devices_raw = await self._wrap_api_call(self.api.get_devices(family_id, shared))

        # Convert to Device objects
        devices = [Device(**dev) for dev in devices_raw]

        # Query device states
        if devices:
            device_states = await self._wrap_api_call(self.api.bulk_query_device_state(devices_raw))

            for device in devices:
                # Update state
                device.state = next(
                    (
                        dev_state["state"]
                        for dev_state in device_states["data"]
                        if dev_state["did"] == device.endpoint_id
                    ),
                    0,
                )

                # Get parameters if online (only if requested)
                if fetch_params and device.is_online:
                    await self.fetch_device_params(device)

                device.last_updated = time.strftime("%Y-%m-%d %H:%M:%S")

        return devices

    async def fetch_device_params(self, device: Device) -> None:
        """Fetch and update device parameters on-demand.

        This method fetches both standard and special parameters for a device
        and updates the device object in-place. Useful for lazy-loading params
        when they're not included in initial device refresh.

        Args:
            device: Device to update (modified in-place)
        """
        try:
            # Get standard params
            params = await self._wrap_api_call(self.api.get_device_params(device, []))
            device.params = params

            # Get special params if available
            special_params_list = AuxProducts.get_special_params_list(device.product_id)
            if special_params_list:
                special_params = await self._wrap_api_call(
                    self.api.get_device_params(device, special_params_list)
                )
                device.params.update(special_params)

        except Exception as e:
            logger.error("Error fetching params for %s: %s", device.endpoint_id, e)

    def find_device(self, device_id: str) -> Device:
        """Find device by ID or name.

        Args:
            device_id: Device ID or name

        Returns:
            Device object

        Raises:
            DeviceNotFoundError: If device not found
        """
        return DeviceFinder.find_device(self.devices, device_id)

    async def set_power(self, device_id: str, on: bool) -> None:
        """Turn device on or off.

        Args:
            device_id: Device ID or name
            on: True to turn on, False to turn off

        Raises:
            DeviceNotFoundError: If device not found
            DeviceOfflineError: If device is offline
        """
        device = self.find_device(device_id)

        if not device.is_online:
            raise DeviceOfflineError(device.endpoint_id, device.friendly_name)

        from climate_hub.api.constants import AC_POWER_OFF, AC_POWER_ON

        params = AC_POWER_ON if on else AC_POWER_OFF
        await self._wrap_api_call(self.api.set_device_params(device, params))

    async def set_temperature(self, device_id: str, temperature: float) -> None:
        """Set target temperature.

        Args:
            device_id: Device ID or name
            temperature: Temperature in Celsius (16-30, supports 0.5 increments)

        Raises:
            DeviceNotFoundError: If device not found
            DeviceOfflineError: If device is offline
            InvalidParameterError: If temperature out of range
        """
        device = self.find_device(device_id)

        if not device.is_online:
            raise DeviceOfflineError(device.endpoint_id, device.friendly_name)

        DeviceControl.validate_temperature(temperature)

        from climate_hub.api.constants import AC_TEMPERATURE_TARGET

        # Convert to tenths (API expects temperature * 10, e.g., 22.0°C -> 220)
        params = {AC_TEMPERATURE_TARGET: int(temperature * 10)}
        await self._wrap_api_call(self.api.set_device_params(device, params))

    async def set_mode(self, device_id: str, mode: str) -> None:
        """Set operation mode.

        Args:
            device_id: Device ID or name
            mode: Mode string (cool, heat, dry, fan, auto)

        Raises:
            DeviceNotFoundError: If device not found
            DeviceOfflineError: If device is offline
            InvalidParameterError: If mode invalid
        """
        device = self.find_device(device_id)

        if not device.is_online:
            raise DeviceOfflineError(device.endpoint_id, device.friendly_name)

        params = DeviceControl.validate_mode(mode)
        await self._wrap_api_call(self.api.set_device_params(device, params))

    async def set_fan_speed(self, device_id: str, speed: str) -> None:
        """Set fan speed.

        Args:
            device_id: Device ID or name
            speed: Fan speed string (auto, low, medium, high, turbo, mute)

        Raises:
            DeviceNotFoundError: If device not found
            DeviceOfflineError: If device is offline
            InvalidParameterError: If speed invalid
        """
        device = self.find_device(device_id)

        if not device.is_online:
            raise DeviceOfflineError(device.endpoint_id, device.friendly_name)

        params = DeviceControl.validate_fan_speed(speed)
        await self._wrap_api_call(self.api.set_device_params(device, params))

    async def set_swing(self, device_id: str, direction: str, on: bool) -> None:
        """Set swing (oscillation).

        Args:
            device_id: Device ID or name
            direction: Direction (vertical, horizontal)
            on: True to turn on, False to turn off

        Raises:
            DeviceNotFoundError: If device not found
            DeviceOfflineError: If device is offline
            InvalidParameterError: If direction invalid
        """
        device = self.find_device(device_id)

        if not device.is_online:
            raise DeviceOfflineError(device.endpoint_id, device.friendly_name)

        DeviceControl.validate_swing_direction(direction)
        params = DeviceControl.get_swing_params(direction, on)
        await self._wrap_api_call(self.api.set_device_params(device, params))
