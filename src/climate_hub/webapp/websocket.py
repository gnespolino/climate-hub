"""WebSocket connection manager for handling frontend clients."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

from climate_hub.api.models import Device

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept connection and add to active list.

        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove connection from active list.

        Args:
            websocket: WebSocket connection
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any] | str) -> None:
        """Broadcast message to all connected clients.

        Robustly handles disconnections during broadcast.

        Args:
            message: Dictionary (will be JSON encoded) or raw JSON string
        """
        if not self.active_connections:
            return

        # Ensure message is a JSON string if it's a dict
        if isinstance(message, dict):
            try:
                # Use default=str to handle non-serializable objects gracefully
                text_message = json.dumps(message, default=str)
            except Exception as e:
                logger.error(f"Failed to serialize broadcast message: {e}")
                return
        else:
            text_message = message

        logger.debug(
            f"Broadcasting to {len(self.active_connections)} clients: {text_message[:100]}..."
        )

        disconnected: list[WebSocket] = []

        # Snapshot copy of list not needed if we don't modify it during iteration,
        # but safely collecting disconnected clients to remove later is correct.
        for connection in self.active_connections:
            try:
                await connection.send_text(text_message)
            except Exception as e:
                logger.warning(f"Failed to send to client, assuming disconnected: {e}")
                disconnected.append(connection)

        # Cleanup disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_initial_state(self, websocket: WebSocket, devices: list[Device]) -> None:
        """Send initial state with all device data to a newly connected client.

        Args:
            websocket: WebSocket connection
            devices: List of all devices
        """
        from climate_hub.webapp.routes.devices import _to_dto

        try:
            await websocket.send_json(
                {
                    "type": "initial_state",
                    "devices": [_to_dto(device).model_dump(by_alias=True) for device in devices],
                }
            )
            logger.info(f"Sent initial state with {len(devices)} devices to new client")
        except Exception as e:
            logger.error(f"Failed to send initial state: {e}")

    async def broadcast_device_update(self, device: Device) -> None:
        """Broadcast single device update with full data to all clients.

        Args:
            device: Updated device
        """
        from climate_hub.webapp.routes.devices import _to_dto

        await self.broadcast(
            {"type": "device_update", "device": _to_dto(device).model_dump(by_alias=True)}
        )
