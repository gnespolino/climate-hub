"""Background tasks for Climate Hub WebApp."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from climate_hub.acfreedom.coordinator import DeviceCoordinator
from climate_hub.api import constants as C
from climate_hub.api.websocket import AuxCloudWebSocket
from climate_hub.logging_config import get_logger
from climate_hub.webapp.websocket import ConnectionManager

logger = get_logger(__name__)


async def run_cloud_listener(
    coordinator: DeviceCoordinator,
    connection_manager: ConnectionManager,
) -> None:
    """Run the cloud listener background task.

    Connects to the AUX Cloud WebSocket and triggers updates in the coordinator.
    Implements robust error handling and exponential backoff for resilience.

    Args:
        coordinator: Initialized DeviceCoordinator instance
        connection_manager: ConnectionManager for broadcasting updates
    """
    logger.info("Starting Cloud Listener background task")

    retry_delay = 5
    max_delay = 300  # 5 minutes

    while True:
        try:
            # Ensure we have valid session/credentials
            if not coordinator.api.is_logged_in():
                logger.warning("Coordinator API not logged in. Waiting for login...")
                await asyncio.sleep(10)
                continue

            # Callback for incoming cloud messages
            async def on_cloud_message(data: dict[str, Any]) -> None:
                """Handle message from cloud."""
                msg_type = data.get("msgtype")

                logger.debug(f"Received cloud message: {msg_type}")

                # Handle device state updates (push messages)
                if msg_type == "push":
                    # Extract device ID from push message
                    endpoint_id = data.get("data", {}).get("endpointId")
                    if endpoint_id:
                        # Trigger immediate update in coordinator
                        # The coordinator will fetch new state and notify callbacks
                        coordinator.trigger_update(endpoint_id)
                        logger.debug(f"Triggered coordinator update for: {endpoint_id}")
                    else:
                        # Fallback: broadcast full message if no device ID
                        await connection_manager.broadcast(data)
                else:
                    # For other message types, broadcast as-is
                    await connection_manager.broadcast(data)

            # Establish WebSocket connection
            api = coordinator.api

            # IMPORTANT: WebSocket requires additional headers (CompanyId, Origin)
            # Reference: maeek/ha-aux-cloud initialize_websocket() method
            ws_headers = api._get_headers(CompanyId=C.COMPANY_ID, Origin=api.url)

            async with AuxCloudWebSocket(
                region=api.region,
                headers=ws_headers,
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
