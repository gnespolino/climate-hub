"""Unit tests for DeviceManager."""

import pytest

from climate_hub.acfreedom.exceptions import AuthenticationError
from climate_hub.acfreedom.manager import DeviceManager
from climate_hub.api.models import Device


@pytest.fixture
def mock_api(mocker):
    """Fixture for mocked AuxCloudAPI."""
    return mocker.patch("climate_hub.acfreedom.manager.AuxCloudAPI", autospec=True).return_value


@pytest.fixture
def manager(mock_api):
    """Fixture for DeviceManager with mocked API."""
    return DeviceManager(api_client=mock_api)


async def test_login_success(manager, mock_api):
    """Test successful login."""
    mock_api.login.return_value = True

    result = await manager.login("test@example.com", "password")

    assert result is True
    mock_api.login.assert_called_once_with("test@example.com", "password")


async def test_login_failure(manager, mock_api):
    """Test login failure mapping."""
    from climate_hub.api.exceptions import AuthenticationError as APIAuthError

    mock_api.login.side_effect = APIAuthError("Invalid credentials")

    with pytest.raises(AuthenticationError) as exc:
        await manager.login("test@example.com", "wrong")

    assert "Invalid credentials" in str(exc.value)


async def test_refresh_devices(manager, mock_api):
    """Test device refreshing and mapping."""
    # Setup mock data
    mock_api.get_families.return_value = [{"familyid": "f1"}]
    mock_api.get_devices.return_value = [
        {
            "endpointId": "d1",
            "productId": "p1",
            "friendlyName": "Living Room",
            "mac": "mac1",
            "devSession": "s1",
            "devicetypeFlag": 1,
            "cookie": "Y29va2ll",  # "cookie" in base64
        }
    ]
    mock_api.bulk_query_device_state.return_value = {
        "data": [{"did": "d1", "state": 1, "status": 0}]
    }
    # Mock get_device_params to avoid further calls
    mock_api.get_device_params.return_value = {"temp": 220}

    devices = await manager.refresh_devices()

    assert len(devices) == 1
    assert devices[0].friendly_name == "Living Room"
    assert devices[0].endpoint_id == "d1"
    assert devices[0].is_online is True
    assert manager.devices == devices


async def test_find_device_by_name(manager):
    """Test finding device by friendly name."""
    device = Device(
        endpointId="id-123",
        productId="p1",
        friendlyName="Kitchen AC",
        mac="mac",
        devSession="sess",
        devicetypeFlag=1,
        cookie="c",
    )
    manager.devices = [device]

    found = manager.find_device("kitchen")
    assert found == device
