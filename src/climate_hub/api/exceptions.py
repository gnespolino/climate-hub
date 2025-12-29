"""Exceptions for AUX Cloud API."""

from __future__ import annotations


class AuxAPIError(Exception):
    """Base exception for AUX API errors."""

    def __init__(self, message: str, details: dict[str, str | int] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ExpiredTokenError(AuxAPIError):
    """Raised when API token expires."""

    def __init__(self) -> None:
        super().__init__("API token has expired")


class ProtocolError(AuxAPIError):
    """Raised when API protocol error occurs."""


class NetworkError(AuxAPIError):
    """Raised when network communication fails."""
