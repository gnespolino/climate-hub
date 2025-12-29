"""Main CLI entry point."""

from __future__ import annotations

import argparse
import asyncio
import sys

from climate_hub.cli.commands import CLICommands


def main() -> None:
    """Main entry point for Climate Hub CLI."""
    parser = argparse.ArgumentParser(
        description="Climate Hub - Control hub for AC Freedom compatible HVAC devices"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Save login credentials")
    login_parser.add_argument("email", help="Account email")
    login_parser.add_argument("password", help="Account password")
    login_parser.add_argument(
        "--region",
        choices=["EU", "USA", "CN"],
        default="EU",
        help="Server region (default: EU)",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List all devices")
    list_parser.add_argument("--shared", action="store_true", help="Include shared devices")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show device status")
    status_parser.add_argument("device", help="Device ID or name")

    # On/Off commands
    on_parser = subparsers.add_parser("on", help="Turn device on")
    on_parser.add_argument("device", help="Device ID or name")

    off_parser = subparsers.add_parser("off", help="Turn device off")
    off_parser.add_argument("device", help="Device ID or name")

    # Temperature command
    temp_parser = subparsers.add_parser("temp", help="Set target temperature")
    temp_parser.add_argument("device", help="Device ID or name")
    temp_parser.add_argument("temperature", type=int, help="Temperature (16-30°C)")

    # Mode command
    mode_parser = subparsers.add_parser("mode", help="Set operation mode")
    mode_parser.add_argument("device", help="Device ID or name")
    mode_parser.add_argument(
        "mode",
        choices=["cool", "heat", "dry", "fan", "auto"],
        help="Operation mode",
    )

    # Fan command
    fan_parser = subparsers.add_parser("fan", help="Set fan speed")
    fan_parser.add_argument("device", help="Device ID or name")
    fan_parser.add_argument(
        "speed",
        choices=["auto", "low", "medium", "high", "turbo", "mute"],
        help="Fan speed",
    )

    # Swing command
    swing_parser = subparsers.add_parser("swing", help="Set swing (oscillation) on/off")
    swing_parser.add_argument("device", help="Device ID or name")
    swing_parser.add_argument(
        "direction", choices=["vertical", "horizontal"], help="Swing direction"
    )
    swing_parser.add_argument("state", choices=["on", "off"], help="Turn swing on or off")

    # Watch command
    subparsers.add_parser("watch", help="Launch real-time monitoring dashboard (TUI)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Create CLI commands instance
    cli = CLICommands()

    # Execute command
    if args.command == "login":
        asyncio.run(cli.login(args.email, args.password, args.region))
    elif args.command == "list":
        asyncio.run(cli.list_devices(args.shared))
    elif args.command == "status":
        asyncio.run(cli.device_status(args.device))
    elif args.command == "on":
        asyncio.run(cli.set_power(args.device, True))
    elif args.command == "off":
        asyncio.run(cli.set_power(args.device, False))
    elif args.command == "temp":
        asyncio.run(cli.set_temperature(args.device, args.temperature))
    elif args.command == "mode":
        asyncio.run(cli.set_mode(args.device, args.mode))
    elif args.command == "fan":
        asyncio.run(cli.set_fan_speed(args.device, args.speed))
    elif args.command == "swing":
        asyncio.run(cli.set_swing(args.device, args.direction, args.state))
    elif args.command == "watch":
        asyncio.run(cli.watch())


if __name__ == "__main__":
    main()
