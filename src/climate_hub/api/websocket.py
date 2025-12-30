"""WebSocket client for AUX Cloud real-time updates."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp

from climate_hub.api import constants as C

logger = logging.getLogger(__name__)


class AuxCloudWebSocket:
    """WebSocket client for real-time device updates with automatic reconnection."""

    def __init__(
        self,
        region: str,
        headers: dict[str, str],
        loginsession: str,
        userid: str,
    ) -> None:
        """Initialize WebSocket client.

        Args:
            region: API region (eu, usa, cn)
            headers: HTTP headers for connection
            loginsession: User login session token
            userid: User ID
        """
        self.websocket_url = {
            "eu": C.WEBSOCKET_SERVER_URL_EU,
            "usa": C.WEBSOCKET_SERVER_URL_USA,
            "cn": C.WEBSOCKET_SERVER_URL_CN,
        }.get(region, C.WEBSOCKET_SERVER_URL_EU)

        self.headers = headers
        self.loginsession = loginsession
        self.userid = userid

        self.session: aiohttp.ClientSession | None = None
        self.websocket: aiohttp.ClientWebSocketResponse | None = None
        self._listeners: list[Callable[[dict[str, Any]], Awaitable[None]]] = []
        self._reconnect_task: asyncio.Task[None] | None = None
        self._stop_reconnect = asyncio.Event()
        self.api_initialized = False

    async def __aenter__(self) -> AuxCloudWebSocket:
        """Async context manager entry - initialize connection.

        Returns:
            Self for context manager usage
        """
        await self.initialize_websocket()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit - cleanup resources.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        await self.close_websocket()

    async def initialize_websocket(self) -> None:
        """Initialize WebSocket connection and authenticate.

        Raises:
            Exception: If connection fails
        """
        url = f"{self.websocket_url}/appsync/apprelay/relayconnect"

        try:
            # Create session (will be closed in close_websocket)
            self.session = aiohttp.ClientSession()

            # IMPORTANT: AUX Cloud WebSocket server requires ALL HTTP headers
            # (unlike standard WebSocket implementations). The server validates
            # authentication during handshake using loginsession/userid headers.
            # Reference: maeek/ha-aux-cloud uses full headers without filtering.
            logger.debug(f"Attempting WebSocket connection to: {url}")
            logger.debug(f"WebSocket headers: {self.headers}")
            logger.debug(f"Auth: userid={self.userid}, loginsession={self.loginsession[:20]}...")

            try:
                self.websocket = await self.session.ws_connect(url, headers=self.headers, ssl=False)
            except aiohttp.WSServerHandshakeError as handshake_error:
                # Capture detailed handshake error information
                logger.error("WebSocket handshake failed!")
                logger.error(f"  Status: {handshake_error.status}")
                logger.error(f"  Message: {handshake_error.message}")
                logger.error(f"  Headers sent: {self.headers}")
                if handshake_error.headers:
                    logger.error(f"  Response headers: {dict(handshake_error.headers)}")
                # Try to read response body if available
                if hasattr(handshake_error, "history") and handshake_error.history:
                    logger.error(f"  Response history: {handshake_error.history}")
                raise

            logger.info("WebSocket connection established")

            # Start listening for messages
            asyncio.create_task(self._listen_to_websocket())

            # Send initialization message
            await self.send_data(
                {
                    "data": {"relayrule": "share"},
                    "messageid": str(int(time.time())) + "000",
                    "msgtype": "init",
                    "scope": {
                        "loginsession": self.loginsession,
                        "userid": self.userid,
                    },
                }
            )

            # Start keep-alive loop
            asyncio.create_task(self._keepalive_loop())

        except Exception as e:
            logger.error("Failed to establish WebSocket connection: %s", e)
            await self.close_websocket()
            raise

    async def _listen_to_websocket(self) -> None:
        """Listen for incoming WebSocket messages."""
        if not self.websocket:
            return

        try:
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    status = data.get("status", -1)
                    msgtype = data.get("msgtype")

                    # Handle authentication/ping failures
                    if status != 0 and msgtype in {"initk", "pingk"}:
                        await self.close_websocket()
                        await self._schedule_reconnect()
                        logger.debug(
                            "Received WebSocket message status %s, reconnecting...",
                            status,
                        )
                        return

                    # WebSocket API authenticated
                    if msgtype == "initk":
                        logger.info("WebSocket API initialized")
                        self.api_initialized = True
                        continue

                    # Keep-alive response
                    if msgtype == "pingk":
                        logger.debug("WebSocket ping acknowledged")
                        continue

                    # Notify listeners of data messages
                    logger.debug("WebSocket message received: %s", msg.data)
                    await self._notify_listeners(data)

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error("WebSocket error: %s", msg.data)
                    break

        except Exception as e:
            logger.error("WebSocket connection lost: %s", e)
        finally:
            await self._schedule_reconnect()

    async def _keepalive_websocket(self) -> None:
        """Send keep-alive ping to server."""
        if self.websocket and not self.websocket.closed:
            try:
                await self.send_data(
                    {
                        "messageid": str(int(time.time())) + "000",
                        "msgtype": "ping",
                    }
                )
                logger.debug("WebSocket keep-alive sent")
            except Exception as e:
                logger.error("Failed to send WebSocket keep-alive: %s", e)
                await self._schedule_reconnect()

    async def _keepalive_loop(self) -> None:
        """Keep-alive loop that runs every 10 seconds."""
        while self.websocket and not self.websocket.closed:
            await self._keepalive_websocket()
            await asyncio.sleep(10)

    async def _notify_listeners(self, message: dict[str, Any]) -> None:
        """Notify all registered listeners of incoming message.

        Args:
            message: Message data to send to listeners
        """
        for listener in self._listeners:
            try:
                await listener(message)
            except Exception as e:
                logger.error("Error in WebSocket listener: %s", e)

    def add_websocket_listener(self, listener: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """Register a listener for WebSocket messages.

        Args:
            listener: Async callable that receives message dict
        """
        self._listeners.append(listener)

    def remove_websocket_listener(
        self, listener: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Remove a registered listener.

        Args:
            listener: Listener to remove
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    async def _schedule_reconnect(self) -> None:
        """Schedule automatic reconnection if not already scheduled."""
        if self._reconnect_task is None:
            self._stop_reconnect.clear()
            self._reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Reconnection loop with exponential backoff."""
        retry_delay = 10  # Start with 10 seconds

        while not self._stop_reconnect.is_set():
            logger.debug("Attempting to reconnect WebSocket...")
            try:
                await self.initialize_websocket()
                logger.info("Successfully reconnected to WebSocket")
                self._reconnect_task = None
                return
            except (ConnectionError, aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error("Reconnect failed: %s", e)
                await asyncio.sleep(retry_delay)
                # Could add exponential backoff here if needed
                # retry_delay = min(retry_delay * 2, 300)  # Max 5 minutes

    async def send_data(self, data: dict[str, Any]) -> None:
        """Send JSON data to WebSocket server.

        Args:
            data: Dictionary to send as JSON

        Raises:
            ConnectionError: If WebSocket is not connected
        """
        if not self.websocket or self.websocket.closed:
            raise ConnectionError("WebSocket is not connected")

        try:
            json_data = json.dumps(data)
            await self.websocket.send_str(json_data)
            logger.debug("Sent JSON data via WebSocket: %s", json_data)
        except Exception as e:
            logger.error("Failed to send JSON data via WebSocket: %s", e)
            raise

    async def close_websocket(self) -> None:
        """Close WebSocket connection and cleanup resources."""
        # Stop reconnection attempts
        self._stop_reconnect.set()

        # Cancel reconnect task if running
        if self._reconnect_task:
            self._reconnect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reconnect_task
            self._reconnect_task = None

        # Close WebSocket
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
            self.websocket = None

        # IMPORTANT: Close the session to prevent resource leak
        if self.session and not self.session.closed:
            await self.session.close()
            # Give the session time to close gracefully
            await asyncio.sleep(0.25)
            self.session = None

        self.api_initialized = False
        logger.info("WebSocket connection closed")
