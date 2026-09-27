"""Konstanten der BlueBattery-Integration."""

from __future__ import annotations

import re
from typing import Final

DOMAIN: Final = "bluebattery"
MANUFACTURER: Final = "BlueBattery"

# Produkte, die als Hauptgerät erkannt werden (ProductName in `info` -> Muster der Geräte-ID)
PRODUCT_BB_DISPLAY: Final = "BB-Display"
PRODUCT_NODE_PATTERNS: Final[dict[str, re.Pattern[str]]] = {
    PRODUCT_BB_DISPLAY: re.compile(r"^BB-D_[0-9A-F]{12}$"),
}

DEFAULT_BASE_TOPIC: Final = "BlueBattery/BB-Display"

# Config-Entry
CONF_NODE: Final = "node"
CONF_BASE_TOPIC: Final = "base_topic"
CONF_PRODUCT: Final = "product"

# Optionen
OPT_SELECTED: Final = "selected"
OPT_IGNORED: Final = "ignored"
OPT_TIMEOUT: Final = "timeout"
OPT_REMOVE_DESELECTED: Final = "remove_deselected"
OPT_TRUMA_EXTENDED_MODES: Final = "truma_extended_modes"
OPT_TRUMA_COMBI_E: Final = "truma_combi_e"

DEFAULT_TIMEOUT: Final = 90  # s ohne frischen Status -> Display nicht erreichbar
MIN_TIMEOUT: Final = 30
MAX_TIMEOUT: Final = 900

# Schonfrist nach Display-Neustart, in der ein Heizungs-`alive` != 2 kein Problem ist
HEATER_GRACE_UPTIME: Final = 180
# Zeit, nach der ein nicht bestätigter Befehl als „ohne Wirkung“ gilt
COMMAND_TIMEOUT: Final = 90
# Gleicher Befehl wird innerhalb dieser Zeit nicht erneut gesendet
COMMAND_DEBOUNCE: Final = 2.0

# Schlüssel der Untergeräte (siehe docs/ARCHITEKTUR.md, Kap. 5.2)
KEY_DISPLAY: Final = "display"
KEY_TRUMA: Final = "truma"
KEY_ALDE: Final = "alde"
PREFIX_BATTERY: Final = "bb:"
PREFIX_TANK_CTL: Final = "tankctl:"
PREFIX_TANK: Final = "tank:"
PREFIX_BLE: Final = "ble:"

SIGNAL_UPDATE: Final = "bluebattery_update_{}"

# Truma
TRUMA_HEATING_MODES: Final[dict[int, str]] = {
    1: "eco",
    10: "high",
    2: "vario_night",
    3: "vario_auto",
    11: "boost",
}
TRUMA_BASIC_PRESETS: Final = ("eco", "high")
TRUMA_WATER_MODES: Final[dict[str, int]] = {"off": 0, "eco": 40, "high": 55, "boost": 60}
TRUMA_ENERGY_MODES: Final[dict[str, int]] = {
    "gas": 0,
    "mix_900": 1,
    "mix_1800": 2,
    "electric_900": 3,
    "electric_1800": 4,
}
TRUMA_MIN_TEMP: Final = 5
TRUMA_MAX_TEMP: Final = 30
TRUMA_DEFAULT_TARGET: Final = 20

# Alde
ALDE_WATER_MODES: Final[dict[str, int]] = {"off": 0, "on": 50, "boost": 65}
ALDE_EL_POWER: Final[dict[str, int]] = {"off": 0, "1kw": 1, "2kw": 2, "3kw": 3}
ALDE_GAS_PRIO: Final[dict[str, int]] = {"electric": 0, "gas": 1}

# Heizungs-Verbindungsstatus (`alive`)
ALIVE_STATES: Final[dict[int, str]] = {
    0: "offline",
    1: "not_connected",
    2: "ok",
    3: "error",
}

# Diagnose: diese Schlüssel werden geschwärzt
REDACT_KEYS: Final = {"mac", "bda", "url", "ble_name", "name", CONF_NODE, CONF_BASE_TOPIC}
