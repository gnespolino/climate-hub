"""Configuration management for Climate Hub."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import keyring
from pydantic import BaseModel, Field, field_validator

from climate_hub.acfreedom.exceptions import ConfigurationError
from climate_hub.api.models import Device, Region

logger = logging.getLogger(__name__)


class AppConfig(BaseModel):
    """Application configuration with validation."""

    email: str | None = None
    # Password is excluded from JSON dump to prevent plaintext storage
    password: str | None = Field(default=None, exclude=True)
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
        if isinstance(v, Region):
            return v.value
        return str(v).lower()


class ConfigManager:
    """Manages application configuration file."""

    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "climate-hub"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
    SERVICE_NAME = "climate-hub"
    ENV_EMAIL = "CLIMATE_HUB_EMAIL"
    ENV_PASSWORD = "CLIMATE_HUB_PASSWORD"

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize config manager.

        Args:
            config_path: Optional custom config file path
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_FILE
        self.config = self._load()

    def _load(self) -> AppConfig:
        """Load configuration from file.

        Automatically migrates plaintext passwords to keyring on load.

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

            # Check for legacy plaintext password and migrate to keyring
            legacy_password = data.get("password")
            email = data.get("email")

            if legacy_password and email:
                logger.info("Detected plaintext password in config. Migrating to system keyring...")
                try:
                    keyring.set_password(self.SERVICE_NAME, email, legacy_password)
                    logger.info("✓ Password migrated to keyring successfully")
                    # Remove password from data to prevent loading into model
                    data.pop("password", None)
                    # Save cleaned config immediately
                    config = AppConfig(**data)
                    self.config_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.config_path, "w") as f:
                        json.dump(config.model_dump(mode="json"), f, indent=2)
                    logger.info("✓ Config file cleaned (password removed)")
                    return config
                except Exception as e:
                    logger.warning(f"Keyring migration failed: {e}. Keeping plaintext fallback.")
                    # Fall through to load config with password field

            return AppConfig(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ConfigurationError(f"Invalid config file: {e}") from e

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        # We use model_dump(mode="json") which respects exclude=True for password
        with open(self.config_path, "w") as f:
            json.dump(self.config.model_dump(mode="json"), f, indent=2)

    def has_credentials(self) -> bool:
        """Check if credentials are configured.

        Returns:
            True if credentials exist
        """
        # 1. Check Env Vars
        if os.getenv(self.ENV_EMAIL) and os.getenv(self.ENV_PASSWORD):
            return True

        # 2. Check Config + Keyring
        if self.config.email:
            try:
                if keyring.get_password(self.SERVICE_NAME, self.config.email):
                    return True
            except Exception:
                pass  # Keyring might fail in some envs

            # 3. Check Legacy Plaintext (Migration/Fallback)
            # We need to manually check the file content or memory since exclude=True hides it
            if self.config.password:
                return True

        return False

    def get_credentials(self) -> tuple[str, str]:
        """Get stored credentials.

        Returns:
            Tuple of (email, password)

        Raises:
            ConfigurationError: If credentials not configured
        """
        # 1. Env Vars
        env_email = os.getenv(self.ENV_EMAIL)
        env_pass = os.getenv(self.ENV_PASSWORD)
        if env_email and env_pass:
            return env_email, env_pass

        if not self.config.email:
            raise ConfigurationError("No email configured. Please run 'climate login'.")

        # 2. Keyring
        try:
            password = keyring.get_password(self.SERVICE_NAME, self.config.email)
            if password:
                return self.config.email, password
        except Exception as e:
            logger.warning("Failed to access keyring: %s", e)

        # 3. Legacy/Memory Fallback
        if self.config.password:
            return self.config.email, self.config.password

        raise ConfigurationError("No password found. Please run 'climate login' again.")

    def set_credentials(self, email: str, password: str, region: str = "eu") -> None:
        """Store credentials safely.

        Args:
            email: User email
            password: User password
            region: API region
        """
        self.config.email = email
        self.config.region = region

        # Save password to keyring
        try:
            keyring.set_password(self.SERVICE_NAME, email, password)
        except Exception as e:
            logger.error("Failed to save password to keyring: %s", e)
            logger.warning("Falling back to plaintext config storage (INSECURE)")
            self.config.password = password
        else:
            # Clear password from config object so it's not saved to JSON
            self.config.password = None

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
