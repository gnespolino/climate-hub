"""Custom widgets for Climate Hub TUI."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from climate_hub.acfreedom.control import DeviceControl
from climate_hub.api.models import Device


class DeviceCard(Static):
    """A widget to display device information."""

    def __init__(self, device: Device, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.device = device

    def compose(self) -> ComposeResult:
        with Vertical(classes="card-container"):
            yield Static(self._render_panel())

    def _render_panel(self) -> Panel:
        """Render the device info panel."""
        status_color = "green" if self.device.is_online else "red"
        status_text = "● ONLINE" if self.device.is_online else "○ OFFLINE"

        title = Text.assemble(
            (f"{self.device.friendly_name} ", "bold white"),
            (status_text, f"bold {status_color}"),
        )

        table = Table.grid(padding=(0, 1))
        table.add_column(style="bold cyan")
        table.add_column()

        # Target Temperature
        target_temp = self.device.get_temperature_target()
        table.add_row("Target Temp:", f"{target_temp or '--'}°C")

        # Ambient Temperature
        ambient_temp = self.device.get_temperature_ambient()
        table.add_row("Ambient Temp:", f"{ambient_temp or '--'}°C")

        # Power and Mode logic
        is_on = self.device.params.get("pwr") == 1

        if is_on:
            mode_val = self.device.params.get("ac_mode", -1)
            mode_name = DeviceControl.get_mode_name(mode_val)
            mode_emoji = self._get_mode_emoji(mode_name)
            table.add_row("Mode:", f"{mode_emoji} {mode_name}")

            # Fan Speed
            fan_val = self.device.params.get("ac_mark", -1)
            fan_name = DeviceControl.get_fan_speed_name(fan_val)
            table.add_row("Fan Speed:", fan_name)
        else:
            table.add_row("Mode:", "[dim]OFF[/dim]")
            table.add_row("Fan Speed:", "[dim]--[/dim]")

        return Panel(
            table,
            title=title,
            border_style="blue" if self.device.is_online else "white",
            expand=True,
        )

    def _get_mode_emoji(self, mode: str) -> str:
        """Get emoji for operational mode."""
        return {
            "Cooling": "❄️",
            "Heating": "🔥",
            "Dry": "💧",
            "Fan": "🌀",
            "Auto": "🤖",
        }.get(mode, "❓")

    def update_device(self, device: Device) -> None:
        """Update widget with new device data."""
        self.device = device
        self.query_one(Static).update(self._render_panel())
