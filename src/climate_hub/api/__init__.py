"""AUX Cloud API client."""

from climate_hub.api.client import AuxCloudAPI
from climate_hub.api.exceptions import AuxAPIError, ExpiredTokenError
from climate_hub.api.models import Device, Family, Room
from climate_hub.api.websocket import AuxCloudWebSocket

__all__ = [
    "AuxCloudAPI",
    "AuxCloudWebSocket",
    "AuxAPIError",
    "ExpiredTokenError",
    "Device",
    "Family",
    "Room",
]
