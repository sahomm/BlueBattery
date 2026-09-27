"""BlueBattery-Integration für Home Assistant (MQTT)."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_BASE_TOPIC,
    CONF_NODE,
    DEFAULT_TIMEOUT,
    DOMAIN,
    KEY_ALDE,
    KEY_DISPLAY,
    KEY_TRUMA,
    OPT_IGNORED,
    OPT_REMOVE_DESELECTED,
    OPT_SELECTED,
    OPT_TIMEOUT,
    PREFIX_BATTERY,
    PREFIX_BLE,
    PREFIX_TANK,
    PREFIX_TANK_CTL,
)
from .data import BlueBatteryDevice, SubDevice
from .entity import build_device_info

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

OPT_LABELS = "labels"
FIRST_STATUS_WAIT = 5.0


@dataclass
class BlueBatteryRuntime:
    """Laufzeitdaten eines Config-Entries."""

    device: BlueBatteryDevice
    subdevices: list[SubDevice] = field(default_factory=list)
    # Stand beim Laden – neu geladen wird nur, wenn sich davon etwas ändert
    loaded_data: dict = field(default_factory=dict)
    loaded_options: dict = field(default_factory=dict)


type BlueBatteryConfigEntry = ConfigEntry[BlueBatteryRuntime]


def kind_of(key: str) -> str:
    """Art eines Untergeräts aus seinem Schlüssel."""
    if key == KEY_DISPLAY:
        return "display"
    if key in (KEY_TRUMA, KEY_ALDE):
        return key
    for prefix, kind in (
        (PREFIX_BATTERY, "battery"),
        (PREFIX_TANK_CTL, "tank_ctl"),
        (PREFIX_TANK, "tank"),
        (PREFIX_BLE, "ble"),
    ):
        if key.startswith(prefix):
            return kind
    return "unknown"


def selected_subdevices(entry: ConfigEntry, device: BlueBatteryDevice) -> list[SubDevice]:
    """Display + ausgewählte Untergeräte (auch wenn sie gerade nicht im Status stehen)."""
    selected: list[str] = list(entry.options.get(OPT_SELECTED, []))
    live = device.subdevices()
    labels: dict[str, str] = {
        **{k: s.label for k, s in live.items()},
        **entry.options.get(OPT_LABELS, {}),
    }
    subs = [SubDevice(KEY_DISPLAY, "display", "BB-Display")]
    for key in selected:
        kind = kind_of(key)
        if kind in ("unknown", "display"):
            continue
        parent = KEY_DISPLAY
        if kind == "tank":
            bda = key[len(PREFIX_TANK):].rpartition(":")[0]
            if f"{PREFIX_TANK_CTL}{bda}" in selected:
                parent = f"{PREFIX_TANK_CTL}{bda}"
        subs.append(SubDevice(key, kind, labels.get(key, key), parent))
    return subs


async def async_setup_entry(hass: HomeAssistant, entry: BlueBatteryConfigEntry) -> bool:
    """Hauptgerät einrichten."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        raise ConfigEntryNotReady("MQTT ist nicht verfügbar")

    device = BlueBatteryDevice(
        hass=hass,
        node=entry.data[CONF_NODE],
        base_topic=entry.data[CONF_BASE_TOPIC],
        timeout=int(entry.options.get(OPT_TIMEOUT, DEFAULT_TIMEOUT)),
    )
    first_status = asyncio.Event()
    unsub_first = device.add_status_listener(first_status.set)
    await device.async_start()
    try:
        # Retained `info`/`status` kommen normalerweise sofort – damit wissen die
        # Plattformen beim Anlegen, welche Felder das Gerät liefert.
        async with asyncio.timeout(FIRST_STATUS_WAIT):
            await first_status.wait()
    except TimeoutError:
        _LOGGER.debug("%s: noch kein Status nach %s s", device.node, FIRST_STATUS_WAIT)
    unsub_first()

    entry.runtime_data = BlueBatteryRuntime(
        device,
        selected_subdevices(entry, device),
        loaded_data=dict(entry.data),
        loaded_options=dict(entry.options),
    )
    _register_devices(hass, entry)
    _sync_registry(hass, entry)

    entry.async_on_unload(device.async_stop)
    entry.async_on_unload(device.add_status_listener(lambda: _check_new_devices(hass, entry)))
    entry.async_on_unload(entry.add_update_listener(_async_reload))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _check_new_devices(hass, entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BlueBatteryConfigEntry) -> bool:
    """Entladen."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Hinweise des Eintrags entfernen."""
    ir.async_delete_issue(hass, DOMAIN, _issue_id(entry))


async def _async_reload(hass: HomeAssistant, entry: BlueBatteryConfigEntry) -> None:
    """Nur bei geänderten Optionen/Topic neu laden – HA ruft den Listener auch bei
    rein internen Änderungen (z. B. Discovery-Keys nach erneuter Erkennung)."""
    runtime = entry.runtime_data
    if entry.data == runtime.loaded_data and entry.options == runtime.loaded_options:
        return
    await hass.config_entries.async_reload(entry.entry_id)


def _issue_id(entry: ConfigEntry) -> str:
    return f"new_devices_{entry.data[CONF_NODE]}"


@callback
def _check_new_devices(hass: HomeAssistant, entry: BlueBatteryConfigEntry) -> None:
    """Neue Untergeräte im Status -> Reparatur-Hinweis (keine automatische Übernahme)."""
    known = set(entry.options.get(OPT_SELECTED, [])) | set(entry.options.get(OPT_IGNORED, []))
    found = entry.runtime_data.device.subdevices()
    new = {key: sub for key, sub in found.items() if key not in known}
    if new:
        ir.async_create_issue(
            hass,
            DOMAIN,
            _issue_id(entry),
            is_fixable=False,
            is_persistent=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="new_devices",
            translation_placeholders={
                "title": entry.title,
                "devices": ", ".join(sorted(sub.label for sub in new.values())),
            },
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, _issue_id(entry))


_KIND_ORDER = {"display": 0, "tank_ctl": 1}


@callback
def _register_devices(hass: HomeAssistant, entry: BlueBatteryConfigEntry) -> None:
    """Geräte vor den Entitäten anlegen – übergeordnete zuerst, damit `via_device`
    greift (Tank-Kanal unter BB-Tank). Korrigiert auch bestehende Zuordnungen."""
    dev_reg = dr.async_get(hass)
    device = entry.runtime_data.device
    for sub in sorted(entry.runtime_data.subdevices, key=lambda s: _KIND_ORDER.get(s.kind, 2)):
        dev_reg.async_get_or_create(config_entry_id=entry.entry_id, **build_device_info(device, sub))


@callback
def _sync_registry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Abgewählte Untergeräte deaktivieren (History bleibt) oder entfernen; wieder
    ausgewählte reaktivieren. Standardmäßig deaktivierte Diagnose-Entitäten bleiben
    unberührt, weil nur das Gerät (de)aktiviert wird."""
    selected = set(entry.options.get(OPT_SELECTED, []))
    remove = bool(entry.options.get(OPT_REMOVE_DESELECTED, False))
    dev_reg = dr.async_get(hass)
    node = entry.data[CONF_NODE]
    for device_entry in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        key = next(
            (
                ident.split("|", 1)[1]
                for domain, ident in device_entry.identifiers
                if domain == DOMAIN and ident.startswith(f"{node}|")
            ),
            None,
        )
        if key is None:  # das Display selbst
            continue
        if key in selected:
            if device_entry.disabled_by is dr.DeviceEntryDisabler.INTEGRATION:
                dev_reg.async_update_device(device_entry.id, disabled_by=None)
        elif remove:
            dev_reg.async_update_device(device_entry.id, remove_config_entry_id=entry.entry_id)
        elif device_entry.disabled_by is None:
            # Gerät deaktivieren: Entitäten bleiben mit ihrer History erhalten
            dev_reg.async_update_device(
                device_entry.id, disabled_by=dr.DeviceEntryDisabler.INTEGRATION
            )
