"""Type definitions for AUX Cloud API responses."""

from __future__ import annotations

from typing import Any, TypedDict


class LoginResponse(TypedDict):
    """Response from account/login."""

    status: int
    loginsession: str
    userid: str


class FamilyInfo(TypedDict):
    """Information about a family."""

    familyid: str
    familyname: str
    # There are more fields, but these are the ones we use


class FamilyListResponse(TypedDict):
    """Response from appsync/group/member/getfamilylist."""

    status: int
    data: dict[str, list[FamilyInfo]]


class RoomInfo(TypedDict):
    """Information about a room."""

    roomid: str
    roomname: str
    familyid: str


class RoomListResponse(TypedDict):
    """Response from appsync/group/room/query."""

    status: int
    data: dict[str, list[RoomInfo]]


class DeviceListPayload(TypedDict):
    """Payload for device list response."""

    endpoints: list[dict[str, Any]] | None
    shareFromOther: list[dict[str, Any]] | None


class DeviceListResponse(TypedDict):
    """Response from appsync/group/dev/query."""

    status: int
    data: DeviceListPayload


class DeviceStatePayload(TypedDict):
    """Payload for device state query response."""

    status: int
    data: list[dict[str, Any]]
    # Each item in data has 'did', 'status', and potentially 'state'


class StateEvent(TypedDict):
    """Event container for state response."""

    payload: DeviceStatePayload


class StateResponse(TypedDict):
    """Response from device/control/v2/querystate."""

    event: StateEvent


class ControlData(TypedDict):
    """Internal data structure in control response payload."""

    params: list[str]
    vals: list[list[dict[str, Any]]]


class ControlPayload(TypedDict):
    """Payload for device control response."""

    status: int
    data: str  # This is a JSON string!


class ControlEvent(TypedDict):
    """Event container for control response."""

    payload: ControlPayload


class ControlResponse(TypedDict):
    """Response from device/control/v2/sdkcontrol."""

    event: ControlEvent
