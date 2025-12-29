"""Pydantic models and enums for AUX Cloud API."""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Region(str, Enum):
    """API server regions."""

    EU = "eu"
    USA = "usa"
    CN = "cn"


class ACMode(IntEnum):
    """Air conditioner operation modes."""

    COOLING = 0
    HEATING = 1
    DRY = 2
    FAN = 3
    AUTO = 4


class ACFanSpeed(IntEnum):
    """Air conditioner fan speeds."""

    AUTO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    TURBO = 4
    MUTE = 5


class HPMode(IntEnum):
    """Heat pump operation modes."""

    AUTO = 0
    COOLING = 1
    HEATING = 4


class DeviceType(str):
    """Device type identifiers."""

    AC_GENERIC = "ac_generic"
    HEAT_PUMP = "heat_pump"
    UNKNOWN = "unknown"


class DeviceState(IntEnum):
    """Device online/offline state."""

    OFFLINE = 0
    ONLINE = 1


class Room(BaseModel):
    """Room within a family."""

    model_config = ConfigDict(populate_by_name=True)

    room_id: str = Field(alias="roomid")
    family_id: str = Field(alias="familyid")
    name: str


class Device(BaseModel):
    """Air conditioner or heat pump device."""

    model_config = ConfigDict(populate_by_name=True)

    endpoint_id: str = Field(alias="endpointId")
    product_id: str = Field(alias="productId")
    friendly_name: str = Field(default="Unnamed", alias="friendlyName")
    mac: str
    dev_session: str = Field(alias="devSession")
    device_type_flag: int = Field(alias="devicetypeFlag")
    cookie: str
    state: int = DeviceState.OFFLINE
    params: dict[str, Any] = Field(default_factory=dict)
    last_updated: str | None = None

    @property
    def is_online(self) -> bool:
        """Check if device is online."""
        return self.state == DeviceState.ONLINE

    @property
    def device_type(self) -> str:
        """Determine device type from product ID."""
        if self.product_id in [
            "000000000000000000000000c0620000",
            "0000000000000000000000002a4e0000",
        ]:
            return DeviceType.AC_GENERIC
        if self.product_id == "000000000000000000000000c3aa0000":
            return DeviceType.HEAT_PUMP
        return DeviceType.UNKNOWN

    def get_temperature_target(self) -> float | None:
        """Get target temperature in Celsius (converts from tenths)."""
        temp = self.params.get("temp")
        if isinstance(temp, int):
            return temp / 10.0
        return None

    def get_temperature_ambient(self) -> float | None:
        """Get ambient temperature in Celsius (converts from tenths)."""
        temp = self.params.get("envtemp")
        if isinstance(temp, int):
            return temp / 10.0
        return None


class Family(BaseModel):
    """Family/group of devices."""

    model_config = ConfigDict(populate_by_name=True)

    family_id: str = Field(alias="familyid")
    name: str
    rooms: list[Room] = Field(default_factory=list)
    devices: list[Device] = Field(default_factory=list)


class DirectiveHeader(BaseModel):
    """Directive header for API requests."""

    model_config = ConfigDict(populate_by_name=True)

    namespace: str
    name: str
    interface_version: str = Field(default="2", alias="interfaceVersion")
    sender_id: str = Field(default="sdk", alias="senderId")
    message_id: str = Field(alias="messageId")


class DeviceDirective(BaseModel):
    """Device control directive."""

    model_config = ConfigDict(populate_by_name=True)

    did: str
    dev_session: str = Field(alias="devSession")


class Credentials(BaseModel):
    """User credentials for API authentication."""

    email: str
    password: str
    region: str = Region.EU


class LoginResponse(BaseModel):
    """API login response."""

    status: int
    loginsession: str
    userid: str


class AuxProducts:
    """Product type definitions and parameter mappings."""

    # Device type product IDs
    AC_GENERIC_IDS = [
        "000000000000000000000000c0620000",
        "0000000000000000000000002a4e0000",
    ]
    HEAT_PUMP_IDS = ["000000000000000000000000c3aa0000"]

    # AC parameters list
    AC_PARAMS = [
        "ac_astheat",
        "ac_clean",
        "ac_hdir",
        "ac_health",
        "ac_mark",
        "ac_mode",
        "ac_slp",
        "ac_vdir",
        "ecomode",
        "err_flag",
        "mldprf",
        "pwr",
        "scrdisp",
        "temp",
        "envtemp",
        "pwrlimit",
        "pwrlimitswitch",
        "childlock",
        "comfwind",
        "new_type",
        "ac_tempconvert",
        "sleepdiy",
        "ac_errcode1",
        "tempunit",
        "tenelec",
    ]

    # AC special parameters
    AC_SPECIAL_PARAMS = ["mode"]

    # Heat Pump parameters
    HP_PARAMS = [
        "ac_errcode1",
        "ac_mode",
        "ac_pwr",
        "ac_temp",
        "ecomode",
        "err_flag",
        "hp_auto_wtemp",
        "hp_fast_hotwater",
        "hp_hotwater_temp",
        "hp_pwr",
        "qtmode",
    ]

    # Heat Pump special parameters
    HP_SPECIAL_PARAMS = ["hp_water_tank_temp"]

    @staticmethod
    def get_device_name(product_id: str) -> str:
        """Get device name from product ID."""
        if product_id in AuxProducts.AC_GENERIC_IDS:
            return "AUX Air Conditioner"
        if product_id in AuxProducts.HEAT_PUMP_IDS:
            return "AUX Heat Pump"
        return "Unknown"

    @staticmethod
    def get_params_list(product_id: str) -> list[str] | None:
        """Get parameter list for product ID."""
        if product_id in AuxProducts.AC_GENERIC_IDS:
            return AuxProducts.AC_PARAMS
        if product_id in AuxProducts.HEAT_PUMP_IDS:
            return AuxProducts.HP_PARAMS
        return None

    @staticmethod
    def get_special_params_list(product_id: str) -> list[str] | None:
        """Get special parameter list for product ID."""
        if product_id in AuxProducts.AC_GENERIC_IDS:
            return AuxProducts.AC_SPECIAL_PARAMS
        if product_id in AuxProducts.HEAT_PUMP_IDS:
            return AuxProducts.HP_SPECIAL_PARAMS
        return None
