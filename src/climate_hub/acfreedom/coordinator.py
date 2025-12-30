"""Device coordinator for managing device cache and active monitoring."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from climate_hub.acfreedom.control import DeviceControl
from climate_hub.acfreedom.device import DeviceFinder
from climate_hub.acfreedom.exceptions import (
    ClimateHubError,
    DeviceNotFoundError,
    DeviceOfflineError,
    ServerBusyError,
)
from climate_hub.api.client import AuxCloudAPI
from climate_hub.api.constants import (
    AC_POWER_OFF,
    AC_POWER_ON,
    AC_TEMPERATURE_TARGET,
)
from climate_hub.api.exceptions import (
    AuxAPIError,
)
from climate_hub.api.exceptions import (
    DeviceOfflineError as APIDeviceOfflineError,
)
from climate_hub.api.exceptions import (
    ServerBusyError as APIServerBusyError,
)
from climate_hub.api.models import AuxProducts, Device

logger = logging.getLogger(__name__)


class DeviceCoordinator:
    """Orchestrates device discovery, monitoring, and state management.

    This class serves as a 'Digital Twin' hub, maintaining an up-to-date
    in-memory cache of all devices and their parameters.
    """

    def __init__(self, api_client: AuxCloudAPI) -> None:
        """Initialize coordinator.

        Args:
            api_client: Logged-in API client
        """
        self.api = api_client
        self._devices: dict[str, Device] = {}
        self._monitors: dict[str, asyncio.Task[None]] = {}
        self._triggers: dict[str, asyncio.Event] = {}
        self._ready_events: dict[str, asyncio.Event] = {}
        self._discovery_task: asyncio.Task[None] | None = None
        self._on_update_callbacks: list[Callable[[Device], Any]] = []

        # Intervals
        self.discovery_interval = 60
        self.monitor_interval = 60

    def on_update(self, callback: Callable[[Device], Any]) -> None:
        """Register a callback for device updates.

        Args:
            callback: Function called with the updated Device object
        """
        self._on_update_callbacks.append(callback)

    async def _notify_update(self, device: Device) -> None:
        """Notify all callbacks of a device update."""
        for callback in self._on_update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(device)
                else:
                    callback(device)
            except Exception as e:
                logger.error("Error in update callback: %s", e)

    async def start(self) -> None:
        """Start the coordinator and wait for initial synchronization."""
        logger.info("Starting DeviceCoordinator...")

        # 1. Initial Discovery
        await self._discovery_step()

        # 2. Start Monitors and Wait for Initial Data
        if not self._devices:
            logger.warning("No devices found during initial discovery")
        else:
            # Start monitors for all discovered devices
            for device_id in self._devices:
                self._start_monitor(device_id)

            # Wait for all monitors to complete at least one cycle
            logger.info("Waiting for initial per-device parameter fetch...")
            await asyncio.gather(
                *[self._ready_events[did].wait() for did in self._ready_events],
                return_exceptions=True,
            )

        # 3. Start Discovery Loop in background
        self._discovery_task = asyncio.create_task(self._discovery_loop())

        logger.info("DeviceCoordinator started and synchronized")

    async def stop(self) -> None:
        """Stop all background tasks."""
        if self._discovery_task:
            self._discovery_task.cancel()

        for task in self._monitors.values():
            task.cancel()

        if self._monitors:
            await asyncio.gather(*self._monitors.values(), return_exceptions=True)

        logger.info("DeviceCoordinator stopped")

    def get_devices(self) -> list[Device]:
        """Get all devices from cache."""
        return list(self._devices.values())

    def find_device(self, device_id: str) -> Device:
        """Find device by ID or name in cache."""
        device = DeviceFinder.find_device(self.get_devices(), device_id)
        if not device:
            raise DeviceNotFoundError(device_id)
        return device

    def trigger_update(self, device_id: str) -> None:
        """Trigger an immediate update for a device."""
        if device_id in self._triggers:
            self._triggers[device_id].set()
            logger.debug("Update triggered for device %s", device_id)

    async def _discovery_step(self) -> None:
        """Perform a single discovery step (Type 1 task)."""
        try:
            families_data = await self.api.get_families()
            all_discovered_ids = set()

            for family in families_data:
                family_id = family["familyid"]
                # Discovery without params
                devices_raw = await self.api.get_devices(family_id, shared=True)

                # Query basic state (online/offline)
                if devices_raw:
                    state_data = await self.api.bulk_query_device_state(devices_raw)
                    for dev_raw in devices_raw:
                        did = dev_raw["did"]
                        all_discovered_ids.add(did)

                        state = next((s["state"] for s in state_data["data"] if s["did"] == did), 0)

                        if did not in self._devices:
                            # New device found
                            logger.info("New device discovered: %s", did)
                            device = Device(**dev_raw)
                            device.state = state
                            self._devices[did] = device
                            if self._discovery_task:  # If loop is already running
                                self._start_monitor(did)
                        else:
                            # Update basic state in existing device
                            self._devices[did].state = state

            # Cleanup removed devices
            removed_ids = set(self._devices.keys()) - all_discovered_ids
            for did in removed_ids:
                logger.info("Device removed: %s", did)
                if did in self._monitors:
                    self._monitors[did].cancel()
                    del self._monitors[did]
                if did in self._triggers:
                    del self._triggers[did]
                if did in self._ready_events:
                    del self._ready_events[did]
                del self._devices[did]

        except Exception as e:
            logger.error("Error during discovery step: %s", e)

    async def _discovery_loop(self) -> None:
        """Periodic discovery loop (Type 1 task)."""
        while True:
            await asyncio.sleep(self.discovery_interval)
            await self._discovery_step()

    def _start_monitor(self, device_id: str) -> None:
        """Start a monitor task for a specific device (Type 2 task)."""
        if device_id in self._monitors:
            return

        self._triggers[device_id] = asyncio.Event()
        self._ready_events[device_id] = asyncio.Event()
        self._monitors[device_id] = asyncio.create_task(self._monitor_loop(device_id))

    async def _monitor_loop(self, device_id: str) -> None:
        """Active monitor loop for a single device (Type 2 task)."""
        logger.debug("Starting monitor for device %s", device_id)

        while True:
            try:
                # 1. Fetch Parameters
                device = self._devices.get(device_id)
                if device and device.is_online:
                    await self._fetch_params(device)
                    device.last_updated = time.strftime("%Y-%m-%d %H:%M:%S")
                    await self._notify_update(device)

                # Signal ready on first successful (or offline) pass
                if not self._ready_events[device_id].is_set():
                    self._ready_events[device_id].set()

                # 2. Wait for Trigger or Timeout
                try:
                    await asyncio.wait_for(
                        self._triggers[device_id].wait(), timeout=self.monitor_interval
                    )
                    logger.debug("Monitor for %s woken up by trigger", device_id)
                except asyncio.TimeoutError:
                    logger.debug("Monitor for %s periodic wakeup", device_id)

                self._triggers[device_id].clear()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitor loop for %s: %s", device_id, e)
                # Signal ready even on error to not block startup forever
                self._ready_events[device_id].set()
                await asyncio.sleep(10)

    async def _fetch_params(self, device: Device) -> None:
        """Fetch all parameters for a device."""
        # Standard params
        params = await self.api.get_device_params(device, [])
        device.params = params

        # Special params
        special_list = AuxProducts.get_special_params_list(device.product_id)
        if special_list:
            special_params = await self.api.get_device_params(device, special_list)
            device.params.update(special_params)

    # --- Control Methods ---

    async def _execute_control(self, device_id: str, params: dict[str, Any]) -> None:
        """Execute control command and trigger immediate update."""
        device = self.find_device(device_id)
        if not device.is_online:
            raise DeviceOfflineError(device.endpoint_id, device.friendly_name)

        try:
            await self.api.set_device_params(device, params)
            # Wake up monitor immediately to reflect changes
            self.trigger_update(device.endpoint_id)
        except APIServerBusyError:
            raise ServerBusyError() from None
        except APIDeviceOfflineError as e:
            raise DeviceOfflineError(device.endpoint_id, device.friendly_name) from e
        except AuxAPIError as e:
            raise ClimateHubError(str(e)) from e

    async def set_power(self, device_id: str, on: bool) -> None:
        """Set device power state."""
        params = AC_POWER_ON if on else AC_POWER_OFF
        await self._execute_control(device_id, params)

    async def set_temperature(self, device_id: str, temperature: float) -> None:
        """Set target temperature."""
        DeviceControl.validate_temperature(temperature)
        params = {AC_TEMPERATURE_TARGET: int(temperature * 10)}
        await self._execute_control(device_id, params)

    async def set_mode(self, device_id: str, mode: str) -> None:
        """Set operation mode."""
        params = DeviceControl.validate_mode(mode)
        await self._execute_control(device_id, params)

    async def set_fan_speed(self, device_id: str, speed: str) -> None:
        """Set fan speed."""
        params = DeviceControl.validate_fan_speed(speed)
        await self._execute_control(device_id, params)

    async def set_swing(self, device_id: str, direction: str, on: bool) -> None:
        """Set swing state."""
        DeviceControl.validate_swing_direction(direction)
        params = DeviceControl.get_swing_params(direction, on)
        await self._execute_control(device_id, params)
