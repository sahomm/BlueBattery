"""Umstieg von der Firmware-eigenen HA-Discovery des BB-Displays.

Die Firmware legt Entitäten über MQTT-Discovery an (Plattform `mqtt`). Diese
können nicht an `bluebattery` übergeben werden. History und Statistiken hängen
aber an der `entity_id` – deshalb übernehmen die neuen Entitäten die alten IDs:

1. vorbereiten: alte Entitäten über ihre bekannten unique_id-Muster den neuen
   Feldern zuordnen und die Zuordnung speichern (solange die alten noch existieren)
2. Nutzer schaltet die Discovery im Display aus -> HA löscht die alten Einträge
3. abschließen: neue Entitäten auf die gemerkten alten `entity_id`s umbenennen
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, KEY_DISPLAY, KEY_TRUMA, PREFIX_BATTERY, PREFIX_BLE, PREFIX_TANK, PREFIX_TANK_CTL
from .data import BlueBatteryDevice

OPT_MIGRATION = "migration_plan"

# alter Feldname -> (Domain, neuer Beschreibungs-Schlüssel)
_BATTERY = {
    "battery_current_A": ("sensor", "battery_current"),
    "solar_a": ("sensor", "solar_current"),
    "solar_panel_v": ("sensor", "pv_voltage"),
    "solar_power_w": ("sensor", "solar_power"),
    "battery_SOC": ("sensor", "soc"),
    "battery_voltage_v": ("sensor", "battery_voltage"),
    "booster_a": ("sensor", "booster_current"),
    "booster_charger_phase": ("sensor", "booster_charger_phase"),
    "booster_charge_ah": ("sensor", "booster_charge"),
    "starterbattery_voltage_v": ("sensor", "starter_voltage"),
    "device_temperature": ("sensor", "device_temp"),
    "metering_battery_in": ("sensor", "battery_in_energy"),
    "metering_battery_out": ("sensor", "battery_out_energy"),
    "metering_booster": ("sensor", "booster_energy"),
    "metering_land": ("sensor", "land_energy"),
    "metering_solar": ("sensor", "solar_energy"),
    "solar_charge_ah": ("sensor", "solar_charge"),
    "pv_charger_phase": ("sensor", "pv_charger_phase"),
    "pv_peak_power_W": ("sensor", "pv_peak_power"),
    "rssi_dBm": ("sensor", "battery_rssi"),
    "relais_status": ("binary_sensor", "relay"),
}
_BLE = {
    "battery": ("sensor", "battery"),
    "humidity": ("sensor", "humidity"),
    "rssi": ("sensor", "rssi"),
    "temp": ("sensor", "temperature"),
    "uptime": ("sensor", "connection_duration"),
    "connCnt": ("sensor", "connection_count"),
}
_TANK = {
    "fill": ("sensor", "volume"),
    "level": ("sensor", "level"),
    "capacity": ("sensor", "capacity"),
    "type": ("sensor", "tank_type"),
    "pitch": ("sensor", "pitch"),
    "roll": ("sensor", "roll"),
    "rssi": ("sensor", "rssi"),
}
_DISPLAY = {
    "cpu_temp": ("sensor", "cpu_temp"),
    "ambient_dewpoint": ("sensor", "ambient_dewpoint"),
    "ambient_humidity": ("sensor", "ambient_humidity"),
    "ambient_temp": ("sensor", "ambient_temp"),
    "heap": ("sensor", "heap"),
    "rssi": ("sensor", "wifi_rssi"),
    "uptime": ("sensor", "uptime"),
}
_TRUMA = {
    "current_room": ("sensor", "room_temp"),
    "current_water": ("sensor", "water_temp"),
    "error_code": ("sensor", "error_code"),
    "error": ("sensor", "error_text"),
    "vent_mode": ("sensor", "vent_mode"),
    "voltage": ("sensor", "supply_voltage"),
}

_RE_BATTERY = re.compile(r"^bb_(.+)_([0-9A-Fa-f]{6})$")
_RE_BLE = re.compile(r"^mi_(\w+?)_([0-9A-Fa-f]{6})$")
_RE_BBTANK = re.compile(r"^bbtank_([0-9A-Fa-f]{12})_S(\d+)_(\w+)$")
_RE_BLUELEVEL = re.compile(r"^bluelevel_(\w+?)_(\w+)$")
_RE_DISPLAY = re.compile(r"^bbd_(\w+)_([0-9A-Fa-f]{12})$")
_RE_TRUMA = re.compile(r"^truma_(\w+)_([0-9A-Fa-f]{12})$")


@dataclass(frozen=True)
class MigrationItem:
    """Alte Entität -> neue Entität (per unique_id)."""

    old_entity_id: str
    new_unique_id: str
    domain: str


def _target(unique_id: str, device: BlueBatteryDevice) -> tuple[str, str, str] | None:
    """(Domain, Untergeräte-Schlüssel, Feld) für eine alte Discovery-unique_id."""
    node_mac = device.node.split("_", 1)[1].upper()
    subs = device.subdevices()

    if unique_id.upper() == f"TIN_TRUMA_HEATER_{node_mac}":
        return "climate", KEY_TRUMA, "truma_heater"
    if unique_id.upper() == f"TRUMA_BOILER_{node_mac}":
        return "select", KEY_TRUMA, "boiler"
    if unique_id.upper() == f"BB_TRUMA_ALIVE_{node_mac}":
        return "sensor", KEY_TRUMA, "connection_state"
    if (m := _RE_TRUMA.match(unique_id)) and m.group(2).upper() == node_mac and m.group(1) in _TRUMA:
        domain, field = _TRUMA[m.group(1)]
        return domain, KEY_TRUMA, field
    if (m := _RE_DISPLAY.match(unique_id)) and m.group(2).upper() == node_mac and m.group(1) in _DISPLAY:
        domain, field = _DISPLAY[m.group(1)]
        return domain, KEY_DISPLAY, field
    if (m := _RE_BBTANK.match(unique_id)) and m.group(3) in _TANK:
        domain, field = _TANK[m.group(3)]
        return domain, f"{PREFIX_TANK}{m.group(1).upper()}:{int(m.group(2)) - 1}", field
    if (m := _RE_BLE.match(unique_id)) and m.group(1) in _BLE:
        mac6 = m.group(2).upper()
        key = next((k for k in subs if k.startswith(PREFIX_BLE) and k.endswith(mac6)), None)
        if key:
            domain, field = _BLE[m.group(1)]
            return domain, key, field
    if (m := _RE_BLUELEVEL.match(unique_id)) and m.group(1) in _TANK:
        ble_name = m.group(2)
        domain, field = _TANK[m.group(1)]
        for key in subs:  # zuerst Tank-Controller (BB-Tank), sonst Kanal (BlueLevel+)
            if key.startswith(PREFIX_TANK_CTL) and (device.block(key) or {}).get("ble_name") == ble_name:
                return domain, key, field
        for key in subs:
            if key.startswith(PREFIX_TANK) and not key.startswith(PREFIX_TANK_CTL):
                block = device.block(key) or {}
                if block.get("ble_name") == ble_name and int(block.get("slot", 0)) == 0:
                    return domain, key, field
    if (m := _RE_BATTERY.match(unique_id)) and m.group(1) in _BATTERY:
        domain, field = _BATTERY[m.group(1)]
        return domain, f"{PREFIX_BATTERY}{m.group(2).upper()}", field
    return None


@callback
def async_plan(hass: HomeAssistant, device: BlueBatteryDevice, selected: list[str]) -> list[MigrationItem]:
    """Zuordnung alt -> neu aus der Entity-Registry ermitteln."""
    ent_reg = er.async_get(hass)
    plan: dict[str, MigrationItem] = {}
    for entry in list(ent_reg.entities.values()):
        if entry.platform != "mqtt" or not entry.unique_id:
            continue
        target = _target(entry.unique_id, device)
        if target is None:
            continue
        domain, key, field = target
        if domain != entry.domain or (key != KEY_DISPLAY and key not in selected):
            continue
        new_uid = f"{device.node}|{key}|{field}"
        if ent_reg.async_get_entity_id(domain, DOMAIN, new_uid) is None:
            continue
        # Eine neue Entität kann nur eine alte ID übernehmen – die erste gewinnt
        plan.setdefault(new_uid, MigrationItem(entry.entity_id, new_uid, domain))
    return sorted(plan.values(), key=lambda i: i.old_entity_id)


def plan_to_options(plan: list[MigrationItem]) -> list[dict[str, str]]:
    """Plan für die Optionen des Config-Entries."""
    return [{"old": i.old_entity_id, "new_uid": i.new_unique_id, "domain": i.domain} for i in plan]


@callback
def async_apply(hass: HomeAssistant, stored: list[dict[str, Any]], force_remove: bool) -> dict[str, list[str]]:
    """Neue Entitäten auf die alten IDs umbenennen.

    Rückgabe: umbenannt / blockiert (alte Entität existiert noch) / fehlt (neue nicht gefunden).
    """
    ent_reg = er.async_get(hass)
    result: dict[str, list[str]] = {"renamed": [], "blocked": [], "missing": []}
    for item in stored:
        old_id, new_uid, domain = item["old"], item["new_uid"], item["domain"]
        new_id = ent_reg.async_get_entity_id(domain, DOMAIN, new_uid)
        if new_id is None:
            result["missing"].append(old_id)
            continue
        if new_id == old_id:
            continue
        if (old := ent_reg.async_get(old_id)) is not None:
            if old.platform == "mqtt" and force_remove:
                ent_reg.async_remove(old_id)
            else:
                result["blocked"].append(old_id)
                continue
        ent_reg.async_update_entity(new_id, new_entity_id=old_id)
        result["renamed"].append(old_id)
    return result
