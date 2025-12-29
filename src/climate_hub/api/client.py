"""HTTP client for AUX Cloud API."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

import aiohttp

from climate_hub.api import constants as C
from climate_hub.api.crypto import encrypt_aes_cbc_zero_padding
from climate_hub.api.exceptions import AuxAPIError
from climate_hub.api.protocol import (
    build_control_request,
    build_query_state_request,
    get_license_param,
    parse_control_response,
    parse_state_response,
)

logger = logging.getLogger(__name__)


class AuxCloudAPI:
    """Client for AUX Cloud API."""

    def __init__(self, region: str = "eu") -> None:
        """Initialize API client.

        Args:
            region: API region (eu, usa, cn)
        """
        self.url = {
            "eu": C.API_SERVER_URL_EU,
            "usa": C.API_SERVER_URL_USA,
            "cn": C.API_SERVER_URL_CN,
        }.get(region, C.API_SERVER_URL_EU)

        self.region = region
        self.loginsession: str | None = None
        self.userid: str | None = None

    def _get_headers(self, **kwargs: str) -> dict[str, str]:
        """Build HTTP headers for API requests.

        Args:
            **kwargs: Additional headers

        Returns:
            Headers dictionary
        """
        return {
            "Content-Type": "application/x-java-serialized-object",
            "licenseId": C.LICENSE_ID,
            "lid": C.LICENSE_ID,
            "language": "en",
            "appVersion": C.SPOOF_APP_VERSION,
            "User-Agent": C.SPOOF_USER_AGENT,
            "system": C.SPOOF_SYSTEM,
            "appPlatform": C.SPOOF_APP_PLATFORM,
            "loginsession": self.loginsession or "",
            "userid": self.userid or "",
            **kwargs,
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        data_raw: str | bytes | None = None,
        params: dict[str, str] | None = None,
        ssl: bool = False,
    ) -> dict[str, Any]:
        """Make HTTP request to API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            headers: HTTP headers
            data: JSON data
            data_raw: Raw data string
            params: Query parameters
            ssl: SSL verification

        Returns:
            JSON response

        Raises:
            AuxAPIError: If request fails
        """
        url = f"{self.url}/{endpoint}"
        logger.debug("Making %s request to %s", method, endpoint)

        try:
            async with aiohttp.ClientSession() as session, session.request(
                method=method,
                url=url,
                headers=headers,
                data=(
                    data_raw
                    if data_raw
                    else json.dumps(data, separators=(",", ":"))
                    if data
                    else None
                ),
                params=params,
                ssl=ssl,
            ) as response:
                response_text = await response.text()
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError as exc:
                    raise AuxAPIError(
                        f"Failed to parse JSON response: {response_text}"
                    ) from exc
        except aiohttp.ClientError as exc:
            raise AuxAPIError(f"Network error: {exc}") from exc

    async def login(self, email: str, password: str) -> bool:
        """Login to AUX cloud services.

        Args:
            email: User email
            password: User password

        Returns:
            True if login successful

        Raises:
            AuxAPIError: If login fails
        """
        current_time = int(time.time())

        # Hash password
        sha_password = hashlib.sha1(f"{password}{C.PASSWORD_ENCRYPT_KEY}".encode()).hexdigest()

        payload = {
            "email": email,
            "password": sha_password,
            "companyid": C.COMPANY_ID,
            "lid": C.LICENSE_ID,
        }
        json_payload = json.dumps(payload, separators=(",", ":"))

        # Token for request validation
        token = hashlib.md5(f"{json_payload}{C.BODY_ENCRYPT_KEY}".encode()).hexdigest()

        # Encryption key from timestamp
        md5_key = hashlib.md5(f"{current_time}{C.TIMESTAMP_TOKEN_ENCRYPT_KEY}".encode()).digest()

        # Encrypt payload
        encrypted_data = encrypt_aes_cbc_zero_padding(
            C.AES_INITIAL_VECTOR, md5_key, json_payload.encode()
        )

        json_data = await self._make_request(
            method="POST",
            endpoint="account/login",
            headers=self._get_headers(timestamp=str(current_time), token=token),
            data_raw=encrypted_data,
            ssl=False,
        )

        if json_data.get("status") == 0:
            self.loginsession = json_data["loginsession"]
            self.userid = json_data["userid"]
            logger.info("Login successful for user %s", email)
            return True

        raise AuxAPIError(f"Login failed: {json_data}")

    def is_logged_in(self) -> bool:
        """Check if user is logged in.

        Returns:
            True if logged in
        """
        return self.loginsession is not None and self.userid is not None

    async def get_families(self) -> list[dict[str, Any]]:
        """Get list of families.

        Returns:
            List of family dictionaries

        Raises:
            AuxAPIError: If request fails
        """
        logger.debug("Getting families list")

        json_data = await self._make_request(
            method="POST",
            endpoint="appsync/group/member/getfamilylist",
            headers=self._get_headers(),
            ssl=False,
        )

        if json_data.get("status") == 0:
            return json_data["data"]["familyList"]

        raise AuxAPIError(f"Failed to get families: {json_data}")

    async def get_rooms(self, familyid: str) -> list[dict[str, Any]]:
        """Get list of rooms in a family.

        Args:
            familyid: Family ID

        Returns:
            List of room dictionaries

        Raises:
            AuxAPIError: If request fails
        """
        logger.debug("Getting rooms for family %s", familyid)

        json_data = await self._make_request(
            method="POST",
            endpoint="appsync/group/room/query",
            headers=self._get_headers(familyid=familyid),
            ssl=False,
        )

        if json_data.get("status") == 0:
            return json_data["data"]["roomList"]

        raise AuxAPIError(f"Failed to get rooms: {json_data}")

    async def query_device_state(self, device_id: str, dev_session: str) -> dict[str, Any]:
        """Query single device state.

        Args:
            device_id: Device endpoint ID
            dev_session: Device session token

        Returns:
            Device state payload

        Raises:
            AuxAPIError: If request fails
        """
        queried_device = [{"did": device_id, "devSession": dev_session}]
        data = build_query_state_request(queried_device, self.userid or "")

        json_data = await self._make_request(
            method="POST",
            endpoint="device/control/v2/querystate",
            data=data,
            headers=self._get_headers(),
            ssl=False,
        )

        return parse_state_response(json_data)

    async def bulk_query_device_state(self, devices: list[dict[str, str]]) -> dict[str, Any]:
        """Query multiple device states in one request.

        Args:
            devices: List of devices with 'endpointId' and 'devSession' keys

        Returns:
            Bulk state query payload

        Raises:
            AuxAPIError: If request fails
        """
        queried_devices = [
            {"did": dev["endpointId"], "devSession": dev["devSession"]} for dev in devices
        ]
        data = build_query_state_request(queried_devices, self.userid or "")

        json_data = await self._make_request(
            method="POST",
            endpoint="device/control/v2/querystate",
            data=data,
            headers=self._get_headers(),
            ssl=False,
        )

        return parse_state_response(json_data)

    async def get_device_params(
        self, device: Any, params: list[str] | None = None
    ) -> dict[str, Any]:
        """Get device parameters.

        Args:
            device: Device object (must have Device interface)
            params: List of parameter names (empty for all)

        Returns:
            Dictionary of parameter name to value

        Raises:
            AuxAPIError: If request fails
        """
        if params is None:
            params = []

        data = build_control_request(device, "get", params)

        json_data = await self._make_request(
            method="POST",
            endpoint="device/control/v2/sdkcontrol",
            data=data,
            params=get_license_param(),
            headers=self._get_headers(),
            ssl=False,
        )

        return parse_control_response(json_data)

    async def set_device_params(self, device: Any, values: dict[str, Any]) -> dict[str, Any]:
        """Set device parameters.

        Args:
            device: Device object (must have Device interface)
            values: Dictionary of parameter name to value

        Returns:
            Response data

        Raises:
            AuxAPIError: If request fails
        """
        params = list(values.keys())
        vals = [[{"idx": 1, "val": v}] for v in values.values()]

        data = build_control_request(device, "set", params, vals)

        json_data = await self._make_request(
            method="POST",
            endpoint="device/control/v2/sdkcontrol",
            data=data,
            params=get_license_param(),
            headers=self._get_headers(),
            ssl=False,
        )

        return parse_control_response(json_data)
