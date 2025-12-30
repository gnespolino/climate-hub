"""FastAPI web application for Climate Hub."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from climate_hub import __version__
from climate_hub.acfreedom.coordinator import DeviceCoordinator
from climate_hub.api.client import AuxCloudAPI
from climate_hub.cli.config import ConfigManager
from climate_hub.logging_config import configure_from_env, get_logger
from climate_hub.webapp.background import run_cloud_listener
from climate_hub.webapp.middleware import RequestLoggingMiddleware
from climate_hub.webapp.routes import control, devices, health
from climate_hub.webapp.websocket import ConnectionManager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan events.

    Handles initialization and cleanup of shared resources like DeviceCoordinator.
    This ensures proper resource management across all worker processes.

    Args:
        app: FastAPI application instance

    Yields:
        None during application runtime
    """
    # Configure logging from environment variables
    configure_from_env()
    logger.info(f"Starting Climate Hub v{__version__}")

    # Startup: Initialize shared resources
    config = ConfigManager()
    api_client = AuxCloudAPI(region=config.get_region())
    connection_manager = ConnectionManager()

    # Attempt auto-login if credentials are available
    if config.has_credentials():
        try:
            email, password = config.get_credentials()
            await api_client.login(email, password)
            logger.info("API client authenticated successfully")
        except Exception as e:
            logger.warning(f"Auto-login failed: {str(e)}. Manual login required.")

    # Initialize coordinator
    coordinator = DeviceCoordinator(api_client)

    # Bridge coordinator updates to frontend WebSockets
    coordinator.on_update(connection_manager.broadcast_device_update)

    # Store in app.state for request-scoped access
    app.state.config = config
    app.state.coordinator = coordinator
    app.state.connection_manager = connection_manager

    # Start coordinator (Blocks until first full refresh of all devices)
    await coordinator.start()

    # Start background tasks
    # Cloud Listener: bridges AUX Cloud WebSocket -> Coordinator triggers
    listener_task = asyncio.create_task(run_cloud_listener(coordinator, connection_manager))

    logger.info("Application startup complete")

    yield

    # Shutdown: Cleanup resources
    logger.info("Application shutdown initiated")

    # Stop coordinator
    await coordinator.stop()

    # Cancel background tasks
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        logger.info("Cloud listener task stopped")


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="Climate Hub API",
        description="REST API for AC Freedom compatible HVAC devices",
        version=__version__,
        lifespan=lifespan,
    )

    # Request logging middleware (applied first, logs last)
    app.add_middleware(RequestLoggingMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static files and templates
    base_dir = Path(__file__).resolve().parent
    app.mount("/static", StaticFiles(directory=base_dir / "static"), name="static")
    templates = Jinja2Templates(directory=base_dir / "templates")

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(devices.router, tags=["devices"])
    app.include_router(control.router, tags=["control"])

    @app.get("/")
    async def dashboard(request: Request) -> Response:
        return templates.TemplateResponse("index.html", {"request": request})

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time updates."""
        connection_manager: ConnectionManager = app.state.connection_manager
        coordinator: DeviceCoordinator = app.state.coordinator

        await connection_manager.connect(websocket)

        # Send initial state with all device data
        await connection_manager.send_initial_state(websocket, coordinator.get_devices())

        try:
            while True:
                # Keep connection open and listen for client messages (optional)
                # Currently we only push server -> client
                await websocket.receive_text()
        except WebSocketDisconnect:
            connection_manager.disconnect(websocket)

    return app


app = create_app()


def run() -> None:
    """Run the web application."""
    uvicorn.run(
        "climate_hub.webapp.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
