"""Background device refresh manager with per-device and bulk update tasks."""

from __future__ import annotations

import asyncio
import contextlib
import time

from climate_hub.acfreedom.manager import DeviceManager
from climate_hub.logging_config import get_logger
from climate_hub.webapp.websocket import ConnectionManager

logger = get_logger(__name__)


class DeviceRefreshManager:
    """Manages background refresh tasks for device state updates.

    Architecture:
    - Initial fetch: all devices WITH full params (startup)
    - Bulk refresh every 60s: all devices WITH full params
    - Per-device refresh tasks: each device refreshes WITH params every 60s or on-demand
    - Ready event: set immediately after initial fetch
    """

    def __init__(self, device_manager: DeviceManager, connection_manager: ConnectionManager):
        """Initialize refresh manager.

        Args:
            device_manager: Device manager instance
            connection_manager: WebSocket connection manager for broadcasting updates
        """
        self.device_manager = device_manager
        self.connection_manager = connection_manager

        # Per-device refresh tasks and timers
        self.device_tasks: dict[str, asyncio.Task[None]] = {}
        self.device_timers: dict[str, float] = {}  # Last refresh timestamp per device

        # Bulk refresh task
        self.bulk_task: asyncio.Task[None] | None = None

        # Refresh intervals
        self.device_refresh_interval = 60  # seconds
        self.bulk_refresh_interval = 60  # seconds

        # Event to trigger immediate device refresh
        self.refresh_events: dict[str, asyncio.Event] = {}

        # Ready event: set when initial fetch complete
        self.ready_event = asyncio.Event()

    async def start(self) -> None:
        """Start all background refresh tasks and wait for initial refresh."""
        logger.info("Starting device refresh manager")

        # Step 1: Fetch all devices WITH params (initial bulk)
        await self.device_manager.refresh_devices()
        logger.info(f"Initial fetch: {len(self.device_manager.devices)} devices with full params")

        # Step 2: Create per-device refresh tasks (will refresh every 60s)
        for device in self.device_manager.devices:
            self._start_device_task(device.endpoint_id)

        logger.info(f"Started {len(self.device_tasks)} per-device refresh tasks")

        # Cache is ready immediately (initial fetch complete)
        self.ready_event.set()
        logger.info("Cache fully populated - webapp ready")

        # Step 3: Start bulk refresh loop (every 60s WITH params)
        self.bulk_task = asyncio.create_task(self._bulk_refresh_loop())
        logger.info("Started bulk refresh loop (60s interval, full params)")

    async def stop(self) -> None:
        """Stop all background refresh tasks."""
        logger.info("Stopping device refresh manager")

        # Cancel all device tasks
        for task in self.device_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self.device_tasks:
            await asyncio.gather(*self.device_tasks.values(), return_exceptions=True)

        # Cancel bulk task
        if self.bulk_task:
            self.bulk_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.bulk_task

        logger.info("Device refresh manager stopped")

    def trigger_device_refresh(self, device_id: str) -> None:
        """Trigger immediate refresh for a specific device (e.g., after control operation).

        Args:
            device_id: Device endpoint ID to refresh
        """
        if device_id in self.refresh_events:
            self.refresh_events[device_id].set()
            logger.debug(f"Triggered immediate refresh for device {device_id}")

    def _start_device_task(self, device_id: str) -> None:
        """Start refresh task for a specific device.

        Args:
            device_id: Device endpoint ID
        """
        self.refresh_events[device_id] = asyncio.Event()
        self.device_timers[device_id] = time.time()
        self.device_tasks[device_id] = asyncio.create_task(self._device_refresh_loop(device_id))

    async def _device_refresh_loop(self, device_id: str) -> None:
        """Background task that refreshes a specific device.

        Refreshes every 60s OR when triggered by an operation.
        Initial fetch already done by start().

        Args:
            device_id: Device endpoint ID to refresh
        """
        logger.debug(f"Started refresh loop for device {device_id}")

        # Initialize timestamp (already fetched by start())
        self.device_timers[device_id] = time.time()

        while True:
            try:
                # Wait for either timeout (60s) or immediate trigger
                try:
                    await asyncio.wait_for(
                        self.refresh_events[device_id].wait(), timeout=self.device_refresh_interval
                    )
                    # Immediate trigger received
                    logger.debug(f"Immediate refresh triggered for {device_id}")
                except asyncio.TimeoutError:
                    # Normal 60s timeout
                    logger.debug(f"Periodic refresh for {device_id} (60s timeout)")

                # Clear the event for next trigger
                self.refresh_events[device_id].clear()

                # Refresh this specific device with full params
                await self._refresh_single_device(device_id)

                # Update last refresh timestamp
                self.device_timers[device_id] = time.time()

            except asyncio.CancelledError:
                logger.debug(f"Refresh loop cancelled for device {device_id}")
                break
            except Exception as e:
                logger.error(f"Error in device refresh loop for {device_id}: {e}")
                # Wait a bit before retrying to avoid tight error loops
                await asyncio.sleep(5)

    async def _refresh_single_device(self, device_id: str) -> None:
        """Refresh a single device and update cache.

        Args:
            device_id: Device endpoint ID to refresh
        """
        try:
            # Find device in cache
            device = next(
                (d for d in self.device_manager.devices if d.endpoint_id == device_id), None
            )

            if not device:
                logger.warning(f"Device {device_id} not found in cache")
                return

            # Fetch fresh params for this device
            await self.device_manager.fetch_device_params(device)

            logger.debug(
                f"Refreshed device {device.friendly_name}: "
                f"temp={device.get_temperature_target()}°C, "
                f"ambient={device.get_temperature_ambient()}°C"
            )

            # Broadcast update with full device data to connected WebSocket clients
            await self.connection_manager.broadcast_device_update(device)

        except Exception as e:
            logger.error(f"Failed to refresh device {device_id}: {e}")

    async def _bulk_refresh_loop(self) -> None:
        """Background task that refreshes all devices periodically WITH full params.

        Runs every 60s to keep all device info fresh.
        """
        logger.info("Bulk refresh loop started")

        while True:
            try:
                await asyncio.sleep(self.bulk_refresh_interval)

                logger.debug("Bulk refresh: updating all devices with full params")

                # Refresh all devices WITH full params
                await self.device_manager.refresh_devices()

                logger.info(f"Bulk refresh completed: {len(self.device_manager.devices)} devices")

            except asyncio.CancelledError:
                logger.info("Bulk refresh loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in bulk refresh loop: {e}")
                await asyncio.sleep(5)
