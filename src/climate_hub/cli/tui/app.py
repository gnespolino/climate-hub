"""Main Textual application for Climate Hub."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Grid, ScrollableContainer
from textual.widgets import Footer, Header, Static

from climate_hub.acfreedom.manager import DeviceManager
from climate_hub.cli.tui.widgets import DeviceCard


class ClimateApp(App[None]):
    """Climate Hub TUI Application."""

    CSS = """
    Grid {
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
    }

    .card-container {
        height: auto;
        background: $boost;
        border: solid $accent;
        padding: 1;
    }

    #last-update {
        text-align: right;
        padding: 0 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self, manager: DeviceManager, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.manager = manager
        self.device_cards: dict[str, DeviceCard] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Last updated: --", id="last-update")
        with ScrollableContainer():
            yield Grid(id="device-grid")
        yield Footer()

    async def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "Climate Hub Control"
        self.sub_title = "Real-time Monitoring"
        await self.action_refresh()

        # Start periodic refresh
        self.set_interval(10, self.action_refresh)

    async def action_refresh(self) -> None:
        """Refresh device information."""
        try:
            devices = await self.manager.refresh_devices()
            grid = self.query_one("#device-grid", Grid)

            for device in devices:
                if device.endpoint_id in self.device_cards:
                    # Update existing card
                    self.device_cards[device.endpoint_id].update_device(device)
                else:
                    # Create new card
                    card = DeviceCard(device)
                    self.device_cards[device.endpoint_id] = card
                    await grid.mount(card)

            # Update timestamp
            now = datetime.now().strftime("%H:%M:%S")
            self.query_one("#last-update", Static).update(f"Last updated: {now}")

        except Exception as e:
            self.notify(f"Refresh failed: {e}", severity="error")
