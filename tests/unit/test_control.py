"""Unit tests for DeviceControl logic."""

import pytest

from climate_hub.acfreedom.control import DeviceControl
from climate_hub.acfreedom.exceptions import InvalidParameterError
from climate_hub.api import constants as C


def test_validate_temperature_valid():
    """Test valid temperature validation."""
    # No exception should be raised
    DeviceControl.validate_temperature(16)
    DeviceControl.validate_temperature(22)
    DeviceControl.validate_temperature(30)


def test_validate_temperature_invalid():
    """Test invalid temperature validation."""
    with pytest.raises(InvalidParameterError):
        DeviceControl.validate_temperature(15)
    with pytest.raises(InvalidParameterError):
        DeviceControl.validate_temperature(31)


def test_celsius_to_api():
    """Test conversion from Celsius to API format."""
    assert DeviceControl.celsius_to_api(22) == 220
    assert DeviceControl.celsius_to_api(16) == 160


def test_api_to_celsius():
    """Test conversion from API format to Celsius."""
    assert DeviceControl.api_to_celsius(220) == 22.0
    assert DeviceControl.api_to_celsius(165) == 16.5


def test_validate_mode_valid():
    """Test valid mode validation."""
    assert DeviceControl.validate_mode("cool") == C.AC_MODE_COOLING
    assert DeviceControl.validate_mode("HEAT") == C.AC_MODE_HEATING


def test_validate_mode_invalid():
    """Test invalid mode validation."""
    with pytest.raises(InvalidParameterError):
        DeviceControl.validate_mode("invalid")


def test_get_mode_name():
    """Test human-readable mode name retrieval."""
    assert DeviceControl.get_mode_name(0) == "Cooling"
    assert DeviceControl.get_mode_name(99) == "Unknown (99)"


def test_validate_fan_speed_valid():
    """Test valid fan speed validation."""
    result = DeviceControl.validate_fan_speed("turbo")
    assert result == {C.AC_FAN_SPEED: 4}


def test_get_swing_params():
    """Test swing parameter generation."""
    assert DeviceControl.get_swing_params("vertical", True) == C.AC_SWING_VERTICAL_ON
    assert DeviceControl.get_swing_params("horizontal", False) == C.AC_SWING_HORIZONTAL_OFF
