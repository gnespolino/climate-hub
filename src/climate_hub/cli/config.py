"""Configuration management for Climate Hub."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from climate_hub.acfreedom.exceptions import ConfigurationError
from climate_hub.api.models import Device, Region


class AppConfig(BaseModel):
    """Application configuration with validation."""

    email: str | None = None
    password: str | None = None
    region: str = Region.EU
    devices: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("region", mode="before")
    @classmethod
    def validate_region(cls, v: str | Region) -> str:
        """Validate and normalize region.

        Args:
            v: Region value

        Returns:
            Normalized region string
        """
        if isinstance(v, str):
            return v.lower()
        return v


class ConfigManager:
    """Manages application configuration file."""

    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "climate-hub"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize config manager.

        Args:
            config_path: Optional custom config file path
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_FILE
        self.config = self._load()

    def _load(self) -> AppConfig:
        """Load configuration from file.

        Returns:
            Configuration object

        Raises:
            ConfigurationError: If config file is invalid
        """
        if not self.config_path.exists():
            return AppConfig()

        try:
            with open(self.config_path) as f:
                data = json.load(f)
            return AppConfig(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ConfigurationError(f"Invalid config file: {e}") from e

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.config.model_dump(mode="json"), f, indent=2)

    def has_credentials(self) -> bool:
        """Check if credentials are configured.

        Returns:
            True if credentials exist
        """
        return bool(self.config.email and self.config.password)

    def get_credentials(self) -> tuple[str, str]:
        """Get stored credentials.

        Returns:
            Tuple of (email, password)

        Raises:
            ConfigurationError: If credentials not configured
        """
        if not self.has_credentials():
            raise ConfigurationError("No credentials found. Please run 'climate login' first.")
        return self.config.email, self.config.password  # type: ignore

    def set_credentials(self, email: str, password: str, region: str = "eu") -> None:
        """Store credentials.

        Args:
            email: User email
            password: User password
            region: API region
        """
        self.config.email = email
        self.config.password = password
        self.config.region = region
        self.save()

    def cache_devices(self, devices: list[Device]) -> None:
        """Cache device list.

        Args:
            devices: List of devices to cache
        """
        self.config.devices = [d.model_dump(mode="json") for d in devices]
        self.save()

    def get_cached_devices(self) -> list[Device]:
        """Get cached devices.

        Returns:
            List of cached devices
        """
        return [Device(**d) for d in self.config.devices]

    def get_region(self) -> str:
        """Get configured region.

        Returns:
            Region string
        """
        return self.config.region or "eu"
