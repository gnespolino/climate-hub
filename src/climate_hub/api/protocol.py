"""Protocol layer for building AUX Cloud API requests."""

from __future__ import annotations

import base64
import json
import time
from typing import Any

from climate_hub.api.constants import LICENSE
from climate_hub.api.models import Device


def build_directive_header(
    namespace: str,
    name: str,
    message_id_prefix: str,
    **kwargs: str,
) -> dict[str, str]:
    """Build directive header for API requests.

    Args:
        namespace: API namespace (e.g., "DNA.QueryState")
        name: API command name (e.g., "queryState")
        message_id_prefix: Prefix for message ID (typically userid)
        **kwargs: Additional header fields

    Returns:
        Directive header dictionary
    """
    timestamp = int(time.time())
    return {
        "namespace": namespace,
        "name": name,
        "interfaceVersion": "2",
        "senderId": "sdk",
        "messageId": f"{message_id_prefix}-{timestamp}",
        **kwargs,
    }


def build_query_state_request(
    devices: list[dict[str, str]],
    userid: str,
) -> dict[str, Any]:
    """Build request to query device states.

    Args:
        devices: List of devices with 'did' and 'devSession' keys
        userid: User ID for message ID prefix

    Returns:
        Query state request payload
    """
    timestamp = int(time.time())
    return {
        "directive": {
            "header": build_directive_header(
                namespace="DNA.QueryState",
                name="queryState",
                messageType="controlgw.batch",
                message_id_prefix=userid,
                timstamp=f"{timestamp}",
            ),
            "payload": {"studata": devices, "msgtype": "batch"},
        }
    }


def build_control_request(
    device: Device,
    action: str,
    params: list[str],
    vals: list[list[dict[str, int]]] | None = None,
) -> dict[str, Any]:
    """Build device control request.

    Args:
        device: Device object
        action: Action type ("get" or "set")
        params: Parameter names
        vals: Parameter values (for "set" action)

    Returns:
        Control request payload
    """
    if vals is None:
        vals = []

    # Decode cookie and build mapped cookie
    cookie = json.loads(base64.b64decode(device.cookie.encode()))
    mapped_cookie = base64.b64encode(
        json.dumps(
            {
                "device": {
                    "id": cookie["terminalid"],
                    "key": cookie["aeskey"],
                    "devSession": device.dev_session,
                    "aeskey": cookie["aeskey"],
                    "did": device.endpoint_id,
                    "pid": device.product_id,
                    "mac": device.mac,
                }
            },
            separators=(",", ":"),
        ).encode()
    ).decode()

    payload: dict[str, Any] = {
        "act": action,
        "params": params,
        "vals": vals,
        "did": device.endpoint_id,
    }

    # Special case for getting ambient mode
    if len(params) == 1 and action == "get":
        payload["vals"] = [[{"val": 0, "idx": 1}]]

    return {
        "directive": {
            "header": build_directive_header(
                namespace="DNA.KeyValueControl",
                name="KeyValueControl",
                message_id_prefix=device.endpoint_id,
            ),
            "endpoint": {
                "devicePairedInfo": {
                    "did": device.endpoint_id,
                    "pid": device.product_id,
                    "mac": device.mac,
                    "devicetypeflag": device.device_type_flag,
                    "cookie": mapped_cookie,
                },
                "endpointId": device.endpoint_id,
                "cookie": {},
                "devSession": device.dev_session,
            },
            "payload": payload,
        }
    }


def parse_state_response(response: dict[str, Any]) -> dict[str, Any]:
    """Parse device state query response.

    Args:
        response: API response

    Returns:
        Parsed payload

    Raises:
        ValueError: If response is invalid
    """
    if (
        "event" in response
        and "payload" in response["event"]
        and response["event"]["payload"].get("status") == 0
    ):
        return response["event"]["payload"]

    raise ValueError(f"Invalid state response: {response}")


def parse_control_response(response: dict[str, Any]) -> dict[str, Any]:
    """Parse device control response.

    Args:
        response: API response

    Returns:
        Dictionary of parameter name to value

    Raises:
        ValueError: If response is invalid
    """
    if (
        "event" not in response
        or "payload" not in response["event"]
        or "data" not in response["event"]["payload"]
    ):
        raise ValueError(f"Invalid control response: {response}")

    data = json.loads(response["event"]["payload"]["data"])
    result: dict[str, Any] = {}

    for i in range(len(data["params"])):
        result[data["params"][i]] = data["vals"][i][0]["val"]

    return result


def get_license_param() -> dict[str, str]:
    """Get license query parameter.

    Returns:
        Dictionary with license parameter
    """
    return {"license": LICENSE}
