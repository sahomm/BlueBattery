"""Datenhaltung eines BlueBattery-Hauptgeräts (MQTT-Empfang, Untergeräte, Befehle)."""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    COMMAND_DEBOUNCE,
    COMMAND_TIMEOUT,
    HEATER_GRACE_UPTIME,
    KEY_ALDE,
    KEY_DISPLAY,
    KEY_TRUMA,
    PREFIX_BATTERY,
    PREFIX_BLE,
    PREFIX_TANK,
    PREFIX_TANK_CTL,
    SIGNAL_UPDATE,
)

_LOGGER = logging.getLogger(__name__)

_TANK_CHANNEL = re.compile(r"^BlueLevel_\d+$")
_MISSING = ("--", "", None)

# Bekannte Felder je Block – alles andere wird einmalig als unbekannt gemeldet.
KNOWN_FIELDS: dict[str, set[str]] = {
    "root": {
        "rssi_dBm", "heap_B", "CPU_temp_C", "uptime_s", "ambient_temp_C",
        "ambient_humidity_RH", "ambient_dewpoint_C", "tankDevices", "truma", "alde",
        "bleSensors",
    },
    "battery": {
        "rssi", "snaps", "battery_SOC_%", "battery_voltage_V", "battery_current_A",
        "solar_current_A", "solar_power_W", "booster_current_A", "booster_charge_Ah",
        "car_voltage_V", "solar_charge_Ah", "pv_voltage_V", "pv_peak_power_W",
        "pv_charger_phase", "booster_charger_phase", "booster_limit_status",
        "relais_status", "device_temperature_C", "solar_Wh", "battery_in_Wh",
        "battery_out_Wh", "land_Wh", "booster_Wh",
    },
    "tank_ctl": {"ble_name", "rssi", "roll", "pitch", "available", "age_s"},
    "tank": {
        "rssi", "name", "capacity", "unit", "level", "display_level", "type", "roll",
        "pitch", "display_volume", "fill", "bda", "ble_name", "slot", "available", "age_s",
    },
    "truma": {
        "alive", "heating_mode", "error", "error_txt", "room_temps", "water_temps",
        "vent_mode", "target_room", "target_water", "current_room", "current_water",
        "voltage", "ac_supply", "energy_mode", "aircon_mode", "aircon_vent",
        "target_aircon", "current_aircon", "aircon_temps",
    },
    "alde": {
        "alde_on", "mode", "has2Zones", "alde_on1", "alde_on2", "target_zone1",
        "target_zone2", "current_zone1_C", "current_zone2_C", "current_zone3_C",
        "current_zone1", "current_zone2", "current_zone3", "target_water",
        "current_water_C", "water_temps", "room_temps", "gas_on", "el_power",
        "gas_prio", "ac_supply", "error_txt",
    },
    "ble": {
        "index", "name", "type", "assigned_icon", "rssi", "temperature", "humidity",
        "battery", "mac", "uptime", "connCnt",
    },
}


def to_number(value: Any) -> float | int | None:
    """Wandelt Zahl, Text mit Zahl ('+0.7', '12.6V') oder Platzhalter in Zahl/None.

    Ganzzahlen bleiben Ganzzahlen (SOC 69 statt 69.0)."""
    if value in _MISSING or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        match = re.search(r"[-+]?\d+(?:[.,]\d+)?", value)
        if match:
            return float(match.group(0).replace(",", "."))
    return None


def normalize_mac(mac: str) -> str:
    """'AA:BB:CC:00:00:01' -> 'AABBCC000001'."""
    return mac.replace(":", "").replace("-", "").upper()


def split_info_topic(topic: str) -> tuple[str, str] | None:
    """'<basis>/<node>/info' -> (basis, node)."""
    parts = topic.split("/")
    if len(parts) < 3 or parts[-1] != "info":
        return None
    return "/".join(parts[:-2]), parts[-2]


def parse_json(payload: Any) -> dict[str, Any] | None:
    """Payload als JSON-Objekt, sonst None."""
    if isinstance(payload, (bytes, bytearray)):
        try:
            payload = payload.decode()
        except UnicodeDecodeError:
            return None
    if not isinstance(payload, str) or not payload:
        return None
    try:
        data = json.loads(payload)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


@dataclass(frozen=True)
class SubDevice:
    """Ein im Status gefundenes Untergerät."""

    key: str
    kind: str  # display | battery | truma | alde | tank_ctl | tank | ble
    label: str
    parent: str = KEY_DISPLAY


def find_subdevices(status: dict[str, Any]) -> dict[str, SubDevice]:
    """Ermittelt alle Untergeräte mit stabilem Schlüssel aus einem Status."""
    found: dict[str, SubDevice] = {}
    for key, block in status.items():
        if not isinstance(block, dict):
            continue
        if key.startswith("BB_"):
            ident = key[3:]
            found[PREFIX_BATTERY + ident] = SubDevice(
                PREFIX_BATTERY + ident, "battery", f"BlueBattery {ident}"
            )
        elif key == "truma":
            found[KEY_TRUMA] = SubDevice(KEY_TRUMA, "truma", "Truma (TIN)")
        elif key == "alde":
            found[KEY_ALDE] = SubDevice(KEY_ALDE, "alde", "Alde (TIN)")
        elif key == "tankDevices":
            for bda, ctl in block.items():
                if isinstance(ctl, dict):
                    sub_key = f"{PREFIX_TANK_CTL}{bda.upper()}"
                    found[sub_key] = SubDevice(
                        sub_key, "tank_ctl", f"BB-Tank {ctl.get('ble_name') or bda}"
                    )
        elif _TANK_CHANNEL.match(key) and "bda" in block:
            bda = str(block["bda"]).upper()
            slot = int(block.get("slot", 0))
            sub_key = f"{PREFIX_TANK}{bda}:{slot}"
            parent_key = f"{PREFIX_TANK_CTL}{bda}"
            name = block.get("name") or "Tank"
            found[sub_key] = SubDevice(
                sub_key,
                "tank",
                f"{name} ({block.get('ble_name') or bda} S{slot + 1})",
                parent=parent_key,
            )
        elif key == "bleSensors":
            for sensor in block.values():
                if isinstance(sensor, dict) and sensor.get("mac"):
                    mac = normalize_mac(str(sensor["mac"]))
                    sub_key = PREFIX_BLE + mac
                    found[sub_key] = SubDevice(
                        sub_key, "ble", str(sensor.get("name") or f"Sensor {mac[-4:]}")
                    )
    # Tank-Kanal ohne exportierten Controller hängt direkt am Display
    for sub_key, sub in list(found.items()):
        if sub.kind == "tank" and sub.parent not in found:
            found[sub_key] = SubDevice(sub.key, sub.kind, sub.label, KEY_DISPLAY)
    return found


def find_block(status: dict[str, Any], key: str) -> dict[str, Any] | None:
    """Liefert den aktuellen Datenblock eines Untergeräts (oder None, wenn es fehlt)."""
    if key == KEY_DISPLAY:
        return status
    if key.startswith(PREFIX_BATTERY):
        block = status.get("BB_" + key[len(PREFIX_BATTERY):])
    elif key in (KEY_TRUMA, KEY_ALDE):
        block = status.get(key)
    elif key.startswith(PREFIX_TANK_CTL):
        wanted = key[len(PREFIX_TANK_CTL):]
        ctls = status.get("tankDevices") or {}
        block = next((v for k, v in ctls.items() if k.upper() == wanted), None)
    elif key.startswith(PREFIX_TANK):
        bda, _, slot = key[len(PREFIX_TANK):].rpartition(":")
        block = next(
            (
                v
                for k, v in status.items()
                if _TANK_CHANNEL.match(k)
                and isinstance(v, dict)
                and str(v.get("bda", "")).upper() == bda
                and str(v.get("slot", 0)) == slot
            ),
            None,
        )
    elif key.startswith(PREFIX_BLE):
        mac = key[len(PREFIX_BLE):]
        sensors = status.get("bleSensors") or {}
        block = next(
            (
                v
                for v in sensors.values()
                if isinstance(v, dict) and normalize_mac(str(v.get("mac", ""))) == mac
            ),
            None,
        )
    else:
        block = None
    return block if isinstance(block, dict) else None


def unknown_fields(status: dict[str, Any]) -> set[str]:
    """Felder im Status, die diese Version der Integration nicht kennt."""
    unknown: set[str] = set()
    for key, value in status.items():
        if key.startswith("BB_") and isinstance(value, dict):
            unknown |= {f"BB_*.{f}" for f in value if f not in KNOWN_FIELDS["battery"]}
        elif _TANK_CHANNEL.match(key) and isinstance(value, dict):
            unknown |= {f"BlueLevel_*.{f}" for f in value if f not in KNOWN_FIELDS["tank"]}
        elif key == "tankDevices" and isinstance(value, dict):
            for ctl in value.values():
                if isinstance(ctl, dict):
                    unknown |= {
                        f"tankDevices.*.{f}" for f in ctl if f not in KNOWN_FIELDS["tank_ctl"]
                    }
        elif key in ("truma", "alde") and isinstance(value, dict):
            unknown |= {f"{key}.{f}" for f in value if f not in KNOWN_FIELDS[key]}
        elif key == "bleSensors" and isinstance(value, dict):
            for sensor in value.values():
                if isinstance(sensor, dict):
                    unknown |= {
                        f"bleSensors.*.{f}" for f in sensor if f not in KNOWN_FIELDS["ble"]
                    }
        elif key not in KNOWN_FIELDS["root"]:
            unknown.add(key)
    return unknown


@dataclass
class PendingCommand:
    """Ein gesendeter, noch nicht im Status sichtbarer Befehl."""

    heater: str
    payload: dict[str, int]
    sent: float


@dataclass
class BlueBatteryDevice:
    """Laufzeitdaten eines Hauptgeräts (z. B. BB-Display)."""

    hass: HomeAssistant
    node: str
    base_topic: str
    timeout: int
    info: dict[str, Any] = field(default_factory=dict)
    status: dict[str, Any] = field(default_factory=dict)
    last_fresh: float | None = None  # monotonic, letzter NICHT-retained Status
    last_update: float | None = None  # Wanduhr, letzter Status überhaupt
    alive: dict[str, int | None] = field(default_factory=lambda: {"truma": None, "alde": None})
    pending: dict[str, PendingCommand] = field(default_factory=dict)
    reported_unknown: set[str] = field(default_factory=set)
    _unsubs: list[CALLBACK_TYPE] = field(default_factory=list)
    _online: bool = False
    _status_listeners: list[Callable[[], None]] = field(default_factory=list)
    _info_listeners: list[Callable[[], None]] = field(default_factory=list)

    @property
    def prefix(self) -> str:
        """Gerätepräfix `<basis>/<node>`."""
        return f"{self.base_topic}/{self.node}"

    @property
    def signal(self) -> str:
        """Dispatcher-Signal für Entitäten."""
        return SIGNAL_UPDATE.format(self.node)

    # --- Empfang ---------------------------------------------------------------

    async def async_start(self) -> None:
        """MQTT abonnieren und Erreichbarkeit überwachen."""
        subscriptions: list[tuple[str, Callable[[ReceiveMessage], None]]] = [
            (f"{self.prefix}/info", self._on_info),
            (f"{self.prefix}/status", self._on_status),
            (f"{self.prefix}/truma/alive", self._on_alive("truma")),
            (f"{self.prefix}/alde/alive", self._on_alive("alde")),
        ]
        for topic, handler in subscriptions:
            self._unsubs.append(await mqtt.async_subscribe(self.hass, topic, handler, qos=0))
        self._unsubs.append(
            async_track_time_interval(self.hass, self._check_timeouts, timedelta(seconds=15))
        )

    @callback
    def async_stop(self) -> None:
        """Abos beenden."""
        while self._unsubs:
            self._unsubs.pop()()

    @callback
    def add_status_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Listener für jeden neuen Status (z. B. Erkennung neuer Untergeräte)."""
        self._status_listeners.append(listener)
        return lambda: self._status_listeners.remove(listener)

    @callback
    def add_info_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Listener für geänderte Geräteinfo (Firmware-Version, URL)."""
        self._info_listeners.append(listener)
        return lambda: self._info_listeners.remove(listener)

    @callback
    def _on_info(self, msg: ReceiveMessage) -> None:
        if (data := parse_json(msg.payload)) is not None:
            changed = data != self.info
            self.info = data
            if changed:
                for listener in list(self._info_listeners):
                    listener()
            self._notify()

    @callback
    def _on_status(self, msg: ReceiveMessage) -> None:
        data = parse_json(msg.payload)
        if data is None:
            _LOGGER.debug("%s: Status ist kein JSON-Objekt, ignoriert", self.node)
            return
        self.status = data
        self.last_update = time.time()
        if not msg.retain:
            self.last_fresh = time.monotonic()
        self._report_unknown(data)
        self._resolve_pending()
        for listener in list(self._status_listeners):
            listener()
        self._notify()

    def _on_alive(self, heater: str) -> Callable[[ReceiveMessage], None]:
        @callback
        def handler(msg: ReceiveMessage) -> None:
            value = to_number(msg.payload)
            self.alive[heater] = None if value is None else int(value)
            self._notify()

        return handler

    @callback
    def _check_timeouts(self, _now: Any = None) -> None:
        changed = self.online != self._online
        now = time.monotonic()
        for heater, cmd in list(self.pending.items()):
            if now - cmd.sent > COMMAND_TIMEOUT:
                _LOGGER.warning(
                    "%s: %s-Befehl %s wurde nach %s s nicht im Status bestätigt",
                    self.node, heater, cmd.payload, COMMAND_TIMEOUT,
                )
                del self.pending[heater]
                changed = True
        if changed:
            self._notify()

    @callback
    def _notify(self) -> None:
        self._online = self.online
        async_dispatcher_send(self.hass, self.signal)

    def _report_unknown(self, status: dict[str, Any]) -> None:
        new = unknown_fields(status) - self.reported_unknown
        if new:
            self.reported_unknown |= new
            _LOGGER.info(
                "%s (Firmware %s) liefert Felder, die diese Integration noch nicht kennt: %s",
                self.node, self.info.get("FirmwareVersion", "?"), ", ".join(sorted(new)),
            )

    # --- Zustand ---------------------------------------------------------------

    @property
    def online(self) -> bool:
        """Display sendet aktiv (frischer Status innerhalb des Zeitlimits)."""
        return self.last_fresh is not None and time.monotonic() - self.last_fresh <= self.timeout

    def block(self, key: str) -> dict[str, Any] | None:
        """Aktueller Datenblock eines Untergeräts."""
        return find_block(self.status, key) if self.status else None

    def subdevices(self) -> dict[str, SubDevice]:
        """Alle aktuell im Status enthaltenen Untergeräte."""
        return find_subdevices(self.status) if self.status else {}

    def heater_alive(self, heater: str) -> int | None:
        """`alive` einer Heizung – eigenes Topic hat Vorrang vor dem Status-Feld."""
        if self.alive.get(heater) is not None:
            return self.alive[heater]
        block = self.block(heater)
        value = to_number(block.get("alive")) if block else None
        return None if value is None else int(value)

    def in_grace_period(self) -> bool:
        """Display ist frisch gestartet – Heizungsverbindung darf noch fehlen."""
        uptime = to_number(self.status.get("uptime_s"))
        return uptime is not None and uptime < HEATER_GRACE_UPTIME

    # --- Befehle ---------------------------------------------------------------

    async def async_send(self, heater: str, payload: dict[str, int]) -> None:
        """Befehl an `set/<heater>` senden (nicht retained, Felder in Reihenfolge)."""
        current = self.pending.get(heater)
        if (
            current is not None
            and current.payload == payload
            and time.monotonic() - current.sent < COMMAND_DEBOUNCE
        ):
            _LOGGER.debug("%s: gleicher Befehl %s wird nicht erneut gesendet", self.node, payload)
            return
        await mqtt.async_publish(
            self.hass, f"{self.prefix}/set/{heater}", json.dumps(payload), qos=0, retain=False
        )
        self.pending[heater] = PendingCommand(heater, dict(payload), time.monotonic())
        self._notify()

    def _resolve_pending(self) -> None:
        for heater, cmd in list(self.pending.items()):
            block = self.status.get(heater)
            if isinstance(block, dict) and all(
                to_number(block.get(k)) == float(v) for k, v in cmd.payload.items()
            ):
                del self.pending[heater]
