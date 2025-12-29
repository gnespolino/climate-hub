"""FastAPI web application for Climate Hub."""

from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from climate_hub import __version__
from climate_hub.webapp.routes import control, devices, health


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="Climate Hub API",
        description="REST API for AC Freedom compatible HVAC devices",
        version=__version__,
    )

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
