"""Unit tests for ConfigManager."""

import os

import pytest

from climate_hub.cli.config import ConfigManager


@pytest.fixture
def temp_config(tmp_path):
    """Fixture for temporary config file path."""
    return tmp_path / "config.json"


def test_env_var_priority(temp_config, mocker):
    """Test that environment variables have highest priority."""
    mocker.patch.dict(
        os.environ, {"CLIMATE_HUB_EMAIL": "env@test.com", "CLIMATE_HUB_PASSWORD": "env-password"}
    )

    cm = ConfigManager(config_path=temp_config)
    email, password = cm.get_credentials()

    assert email == "env@test.com"
    assert password == "env-password"


def test_keyring_retrieval(temp_config, mocker):
    """Test retrieval from keyring when env vars are missing."""
    mocker.patch.dict(os.environ, {}, clear=True)
    mock_keyring = mocker.patch("keyring.get_password")
    mock_keyring.return_value = "keyring-password"

    cm = ConfigManager(config_path=temp_config)
    cm.config.email = "keyring@test.com"

    email, password = cm.get_credentials()

    assert email == "keyring@test.com"
    assert password == "keyring-password"
    mock_keyring.assert_called_with(ConfigManager.SERVICE_NAME, "keyring@test.com")


def test_set_credentials(temp_config, mocker):
    """Test saving credentials to keyring and config file."""
    mock_set_pass = mocker.patch("keyring.set_password")

    cm = ConfigManager(config_path=temp_config)
    cm.set_credentials("user@test.com", "mypass", region="usa")

    assert cm.config.email == "user@test.com"
    assert cm.config.region == "usa"
    assert cm.config.password is None  # Should be None in memory if keyring worked

    mock_set_pass.assert_called_with(ConfigManager.SERVICE_NAME, "user@test.com", "mypass")
    assert temp_config.exists()


def test_get_region_default(temp_config):
    """Test default region retrieval."""
    cm = ConfigManager(config_path=temp_config)
    assert cm.get_region() == "eu"
