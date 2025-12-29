"""Constants for AUX Cloud API."""

from __future__ import annotations

# API Server URLs
API_SERVER_URL_EU = "https://app-service-deu-f0e9ebbb.smarthomecs.de"
API_SERVER_URL_USA = "https://app-service-usa-fd7cc04c.smarthomecs.com"
API_SERVER_URL_CN = "https://app-service-chn-31a93883.ibroadlink.com"

# WebSocket Server URLs
WEBSOCKET_SERVER_URL_EU = "wss://app-relay-deu-f0e9ebbb.smarthomecs.de"
WEBSOCKET_SERVER_URL_USA = "wss://app-relay-usa-fd7cc04c.smarthomecs.com"
WEBSOCKET_SERVER_URL_CN = "wss://app-relay-chn-31a93883.ibroadlink.com"

# Encryption Keys
TIMESTAMP_TOKEN_ENCRYPT_KEY = "kdixkdqp54545^#*"
PASSWORD_ENCRYPT_KEY = "4969fj#k23#"
BODY_ENCRYPT_KEY = "xgx3d*fe3478$ukx"

# AES Initialization Vector
AES_INITIAL_VECTOR = bytes(
    [
        (b + 256) % 256
        for b in [
            -22,
            -86,
            -86,
            58,
            -69,
            88,
            98,
            -94,
            25,
            24,
            -75,
            119,
            29,
            22,
            21,
            -86,
        ]
    ]
)

# License and Company
LICENSE = "PAFbJJ3WbvDxH5vvWezXN5BujETtH/iuTtIIW5CE/SeHN7oNKqnEajgljTcL0fBQQWM0XAAAAAAnBhJyhMi7zIQMsUcwR/PEwGA3uB5HLOnr+xRrci+FwHMkUtK7v4yo0ZHa+jPvb6djelPP893k7SagmffZmOkLSOsbNs8CAqsu8HuIDs2mDQAAAAA="
LICENSE_ID = "3c015b249dd66ef0f11f9bef59ecd737"
COMPANY_ID = "48eb1b36cf0202ab2ef07b880ecda60d"

# User Agent Spoofing
SPOOF_APP_VERSION = "2.2.10.456537160"
SPOOF_USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 12; SM-G991B Build/SP1A.210812.016)"
SPOOF_SYSTEM = "android"
SPOOF_APP_PLATFORM = "android"

# Parameter Names
AUX_MODE = "ac_mode"
AUX_ECOMODE = "ecomode"
AUX_ERROR_FLAG = "err_flag"

# AC Parameters
AC_POWER = "pwr"
AC_TEMPERATURE_TARGET = "temp"
AC_TEMPERATURE_AMBIENT = "envtemp"
AC_MODE_SPECIAL = "mode"
AC_FAN_SPEED = "ac_mark"
AC_SWING_VERTICAL = "ac_vdir"
AC_SWING_HORIZONTAL = "ac_hdir"
AC_AUXILIARY_HEAT = "ac_astheat"
AC_CLEAN = "ac_clean"
AC_HEALTH = "ac_health"
AC_CHILD_LOCK = "childlock"
AC_COMFORTABLE_WIND = "comfwind"
AC_MILDEW_PROOF = "mldprf"
AC_SLEEP = "ac_slp"
AC_SCREEN_DISPLAY = "scrdisp"
AC_POWER_LIMIT = "pwrlimit"
AC_POWER_LIMIT_SWITCH = "pwrlimitswitch"

# Heat Pump Parameters
HP_HEATER_POWER = "ac_pwr"
HP_HEATER_TEMPERATURE_TARGET = "ac_temp"
HP_HEATER_AUTO_WATER_TEMP = "hp_auto_wtemp"
HP_WATER_POWER = "hp_pwr"
HP_QUIET_MODE = "qtmode"
HP_HOT_WATER_TANK_TEMPERATURE = "hp_water_tank_temp"
HP_HOT_WATER_TEMPERATURE_TARGET = "hp_hotwater_temp"
HP_WATER_FAST_HOTWATER = "hp_fast_hotwater"

# Parameter Value Presets
AC_POWER_ON = {AC_POWER: 1}
AC_POWER_OFF = {AC_POWER: 0}
AC_MODE_COOLING = {AUX_MODE: 0}
AC_MODE_HEATING = {AUX_MODE: 1}
AC_MODE_DRY = {AUX_MODE: 2}
AC_MODE_FAN = {AUX_MODE: 3}
AC_MODE_AUTO = {AUX_MODE: 4}
AC_SWING_VERTICAL_ON = {AC_SWING_VERTICAL: 1}
AC_SWING_VERTICAL_OFF = {AC_SWING_VERTICAL: 0}
AC_SWING_HORIZONTAL_ON = {AC_SWING_HORIZONTAL: 1}
AC_SWING_HORIZONTAL_OFF = {AC_SWING_HORIZONTAL: 0}
AUX_ECOMODE_ON = {AUX_ECOMODE: 1}
AUX_ECOMODE_OFF = {AUX_ECOMODE: 0}
