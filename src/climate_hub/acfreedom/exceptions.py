"""Business logic exceptions for Climate Hub."""

from __future__ import annotations


class ClimateHubError(Exception):
    """Base exception for all Climate Hub business logic errors."""

    def __init__(self, message: str, details: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(ClimateHubError):
    """Authentication failed."""

    def __init__(self, reason: str = "Authentication failed") -> None:
        super().__init__(f"Authentication error: {reason}", {"reason": reason})
        self.reason = reason


class DeviceNotFoundError(ClimateHubError):
    """Device not found by ID or name."""

    def __init__(self, device_id: str) -> None:
        super().__init__(
            f"Device not found: {device_id}",
            {"device_id": device_id},
        )
        self.device_id = device_id


class DeviceOfflineError(ClimateHubError):
    """Device is offline and cannot be controlled."""

    def __init__(self, device_id: str, device_name: str) -> None:
        super().__init__(
            f"Device '{device_name}' is offline",
            {"device_id": device_id, "device_name": device_name},
        )
        self.device_id = device_id
        self.device_name = device_name


class InvalidParameterError(ClimateHubError):
    """Invalid parameter value provided."""

    def __init__(
        self, param_name: str, value: str | int, valid_values: list[str] | None = None
    ) -> None:
        msg = f"Invalid {param_name}: {value}"
        if valid_values:
            msg += f". Valid values: {', '.join(valid_values)}"
        super().__init__(msg, {"param_name": param_name, "value": str(value)})
        self.param_name = param_name
        self.value = value
        self.valid_values = valid_values


class ConfigurationError(ClimateHubError):
    """Configuration error (missing or invalid config)."""
