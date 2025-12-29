"""CLI command implementations."""

from __future__ import annotations

import logging

from climate_hub.acfreedom.exceptions import (
    AuthenticationError,
    ClimateHubError,
    ConfigurationError,
    DeviceNotFoundError,
    DeviceOfflineError,
    InvalidParameterError,
)
from climate_hub.acfreedom.manager import DeviceManager
from climate_hub.cli.config import ConfigManager
from climate_hub.cli.formatters import OutputFormatter

logger = logging.getLogger(__name__)


class CLICommands:
    """Implementation of CLI commands."""

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        device_manager: DeviceManager | None = None,
    ) -> None:
        """Initialize CLI commands.

        Args:
            config_manager: Configuration manager
            device_manager: Device manager
        """
        self.config = config_manager or ConfigManager()
        self.manager = device_manager or DeviceManager(region=self.config.get_region())

    async def login(self, email: str, password: str, region: str = "EU") -> None:
        """Login and save credentials.

        Args:
            email: User email
            password: User password
            region: API region
        """
        try:
            # Create new manager with correct region
            self.manager = DeviceManager(region=region.lower())
            await self.manager.login(email, password)

            self.config.set_credentials(email, password, region.lower())
            print(
                OutputFormatter.format_success(
                    f"Login successful! Credentials saved to {self.config.config_path}"
                )
            )
        except (AuthenticationError, ClimateHubError) as e:
            print(OutputFormatter.format_error(f"Login failed: {e.message}"))

    async def list_devices(self, shared: bool = False) -> None:
        """List all devices.

        Args:
            shared: Include shared devices
        """
        try:
            await self._ensure_logged_in()
            devices = await self.manager.refresh_devices(shared)
            print(OutputFormatter.format_device_list(devices))

            # Cache devices
            self.config.cache_devices(devices)

        except ConfigurationError as e:
            print(OutputFormatter.format_error(e.message))
        except ClimateHubError as e:
            print(OutputFormatter.format_error(f"Error listing devices: {e.message}"))

    async def device_status(self, device_id: str) -> None:
        """Show device status.

        Args:
            device_id: Device ID or name
        """
        try:
            await self._ensure_logged_in()

            # Refresh devices first
            await self.manager.refresh_devices()

            device = self.manager.find_device(device_id)
            print(OutputFormatter.format_device_status(device))

        except ConfigurationError as e:
            print(OutputFormatter.format_error(e.message))
        except DeviceNotFoundError as e:
            print(OutputFormatter.format_error(e.message))
            print("Run 'climate list' to see available devices.")
        except ClimateHubError as e:
            print(OutputFormatter.format_error(f"Error getting status: {e.message}"))

    async def set_power(self, device_id: str, on: bool) -> None:
        """Turn device on or off.

        Args:
            device_id: Device ID or name
            on: True to turn on, False to turn off
        """
        try:
            await self._ensure_logged_in()
            await self.manager.refresh_devices()

            await self.manager.set_power(device_id, on)
            print(OutputFormatter.format_success(f"Device {'turned ON' if on else 'turned OFF'}"))

        except (ConfigurationError, DeviceNotFoundError, DeviceOfflineError) as e:
            print(OutputFormatter.format_error(e.message))
        except ClimateHubError as e:
            print(OutputFormatter.format_error(f"Error setting power: {e.message}"))

    async def set_temperature(self, device_id: str, temperature: int) -> None:
        """Set target temperature.

        Args:
            device_id: Device ID or name
            temperature: Temperature in Celsius
        """
        try:
            await self._ensure_logged_in()
            await self.manager.refresh_devices()

            await self.manager.set_temperature(device_id, temperature)
            print(OutputFormatter.format_success(f"Temperature set to {temperature}°C"))

        except (
            ConfigurationError,
            DeviceNotFoundError,
            DeviceOfflineError,
            InvalidParameterError,
        ) as e:
            print(OutputFormatter.format_error(e.message))
        except ClimateHubError as e:
            print(OutputFormatter.format_error(f"Error setting temperature: {e.message}"))

    async def set_mode(self, device_id: str, mode: str) -> None:
        """Set operation mode.

        Args:
            device_id: Device ID or name
            mode: Mode string
        """
        try:
            await self._ensure_logged_in()
            await self.manager.refresh_devices()

            await self.manager.set_mode(device_id, mode)
            print(OutputFormatter.format_success(f"Mode set to {mode}"))

        except (
            ConfigurationError,
            DeviceNotFoundError,
            DeviceOfflineError,
            InvalidParameterError,
        ) as e:
            print(OutputFormatter.format_error(e.message))
        except ClimateHubError as e:
            print(OutputFormatter.format_error(f"Error setting mode: {e.message}"))

    async def set_fan_speed(self, device_id: str, speed: str) -> None:
        """Set fan speed.

        Args:
            device_id: Device ID or name
            speed: Fan speed string
        """
        try:
            await self._ensure_logged_in()
            await self.manager.refresh_devices()

            await self.manager.set_fan_speed(device_id, speed)
            print(OutputFormatter.format_success(f"Fan speed set to {speed}"))

        except (
            ConfigurationError,
            DeviceNotFoundError,
            DeviceOfflineError,
            InvalidParameterError,
        ) as e:
            print(OutputFormatter.format_error(e.message))
        except ClimateHubError as e:
            print(OutputFormatter.format_error(f"Error setting fan speed: {e.message}"))

    async def set_swing(self, device_id: str, direction: str, state: str) -> None:
        """Set swing (oscillation).

        Args:
            device_id: Device ID or name
            direction: Direction (vertical, horizontal)
            state: State (on, off)
        """
        try:
            await self._ensure_logged_in()
            await self.manager.refresh_devices()

            on = state.lower() == "on"
            await self.manager.set_swing(device_id, direction, on)
            print(OutputFormatter.format_success(f"Swing {direction} turned {state.upper()}"))

        except (
            ConfigurationError,
            DeviceNotFoundError,
            DeviceOfflineError,
            InvalidParameterError,
        ) as e:
            print(OutputFormatter.format_error(e.message))
        except ClimateHubError as e:
            print(OutputFormatter.format_error(f"Error setting swing: {e.message}"))

    async def _ensure_logged_in(self) -> None:
        """Ensure user is logged in.

        Raises:
            ConfigurationError: If not logged in
        """
        if not self.config.has_credentials():
            raise ConfigurationError("No credentials found. Please run 'climate login' first.")

        email, password = self.config.get_credentials()
        if not self.manager.is_logged_in():
            await self.manager.login(email, password)
