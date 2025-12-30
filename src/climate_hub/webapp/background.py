"""Background tasks for Climate Hub WebApp."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, cast

from climate_hub.acfreedom.manager import DeviceManager
from climate_hub.api.websocket import AuxCloudWebSocket
from climate_hub.webapp.websocket import ConnectionManager

logger = logging.getLogger(__name__)


async def run_cloud_listener(
    device_manager: DeviceManager,
    connection_manager: ConnectionManager,
) -> None:
    """Run the cloud listener background task.

    Connects to the AUX Cloud WebSocket and forwards updates to connected frontend clients.
    Implements robust error handling and exponential backoff for resilience.

    Args:
        device_manager: Initialized DeviceManager instance
        connection_manager: ConnectionManager for broadcasting updates
    """
    logger.info("Starting Cloud Listener background task")

    retry_delay = 5
    max_delay = 300  # 5 minutes

    while True:
        try:
            # Ensure we have valid session/credentials
            if not device_manager.is_logged_in():
                logger.warning("Device manager not logged in. Waiting for login...")
                await asyncio.sleep(10)
                continue

            # Callback for incoming cloud messages
            async def on_cloud_message(data: dict[str, Any]) -> None:
                """Handle message from cloud."""
                msg_type = data.get("msgtype")

                # Only interested in device status updates (typically 'report')
                # But we broadcast everything useful for debugging/status
                logger.debug(f"Received cloud message: {msg_type}")

                # 1. Invalidate backend cache to ensure next API call gets fresh data
                # Optimized: We could update cache directly here in future (Phase 4?)
                if msg_type == "report":
                    device_manager.invalidate_cache()

                # 2. Broadcast to frontend
                await connection_manager.broadcast(data)

            # Establish WebSocket connection
            api = device_manager.api
            async with AuxCloudWebSocket(
                region=api.region,
                headers=api.headers,
                loginsession=cast(str, api.loginsession),
                userid=cast(str, api.userid),
            ) as ws:
                logger.info("Cloud Listener connected to AUX servers")

                # Reset retry delay on successful connection
                retry_delay = 5

                # Register our callback
                ws.add_websocket_listener(on_cloud_message)

                # Keep the context manager alive.
                # AuxCloudWebSocket has internal keep-alive, but we need to prevent
                # the context from exiting immediately.
                # We wait for the internal connection to close or an error to occur.
                while ws.websocket and not ws.websocket.closed:
                    await asyncio.sleep(1)

            logger.warning("Cloud connection closed gracefully. Reconnecting...")

        except asyncio.CancelledError:
            logger.info("Cloud Listener task cancelled. Shutting down.")
            raise

        except Exception as e:
            logger.error(f"Cloud Listener error: {e}. Retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)

            # Exponential backoff
            retry_delay = min(retry_delay * 2, max_delay)
