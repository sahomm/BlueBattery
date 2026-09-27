"""Binärsensoren der BlueBattery-Integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import BlueBatteryConfigEntry
from .data import BlueBatteryDevice, to_number
from .entity import BlueBatteryEntity


def _heater_connected(heater: str) -> Callable[[dict[str, Any] | None, BlueBatteryDevice], bool | None]:
    def get(_block: dict[str, Any] | None, device: BlueBatteryDevice) -> bool | None:
        return device.heater_connected(heater)

    return get


def _heater_problem(heater: str) -> Callable[[dict[str, Any] | None, BlueBatteryDevice], bool | None]:
    """Störung: Fehlercode, Heizungsstatus „Fehler“ oder Verbindung weg (nach Schonfrist)."""

    def get(block: dict[str, Any] | None, device: BlueBatteryDevice) -> bool | None:
        alive = device.heater_alive(heater)
        if alive == 3:
            return True
        if alive in (0, 1) and not device.in_grace_period():
            return True
        if block is not None:
            code = to_number(block.get("error"))
            if code is not None and code != 0:
                return True
        return None if alive is None and block is None else False

    return get


def _flag(field: str) -> Callable[[dict[str, Any] | None, BlueBatteryDevice], bool | None]:
    def get(block: dict[str, Any] | None, _device: BlueBatteryDevice) -> bool | None:
        num = to_number(block.get(field)) if block else None
        return None if num is None else num != 0

    return get


@dataclass(frozen=True, kw_only=True)
class BlueBatteryBinaryDescription(BinarySensorEntityDescription):
    """Beschreibung eines Binärsensors."""

    kinds: tuple[str, ...]
    value_fn: Callable[[dict[str, Any] | None, BlueBatteryDevice], bool | None]
    # Bleibt verfügbar, solange HA läuft bzw. das Display sendet (für Ausfall-Automationen)
    always_available: bool = False
    needs_display_only: bool = False
    exists_fn: Callable[[dict[str, Any] | None], bool] = lambda block: True


BINARY_SENSORS: tuple[BlueBatteryBinaryDescription, ...] = (
    BlueBatteryBinaryDescription(
        key="connected", translation_key="display_connected", kinds=("display",),
        value_fn=lambda _b, device: device.online,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC, always_available=True,
    ),
    BlueBatteryBinaryDescription(
        key="relay", translation_key="relay", kinds=("battery",), value_fn=_flag("relais_status"),
        exists_fn=lambda block: block is None or "relais_status" in block,
    ),
    BlueBatteryBinaryDescription(
        key="heater_connected", translation_key="heater_connected", kinds=("truma", "alde"),
        value_fn=lambda block, device: None,  # wird je Heizung ersetzt (siehe unten)
        device_class=BinarySensorDeviceClass.CONNECTIVITY, needs_display_only=True,
    ),
    BlueBatteryBinaryDescription(
        key="heater_problem", translation_key="heater_problem", kinds=("truma", "alde"),
        value_fn=lambda block, device: None,
        device_class=BinarySensorDeviceClass.PROBLEM, needs_display_only=True,
    ),
    BlueBatteryBinaryDescription(
        key="ac_supply", translation_key="ac_supply", kinds=("truma", "alde"), value_fn=_flag("ac_supply"),
        device_class=BinarySensorDeviceClass.PLUG, entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda block: block is None or "ac_supply" in block,
    ),
)

_PER_HEATER = {
    "heater_connected": _heater_connected,
    "heater_problem": _heater_problem,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BlueBatteryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Binärsensoren anlegen."""
    runtime = entry.runtime_data
    device = runtime.device
    entities = []
    for sub in runtime.subdevices:
        block = device.block(sub.key)
        for description in BINARY_SENSORS:
            if sub.kind not in description.kinds or not description.exists_fn(block):
                continue
            if description.key in _PER_HEATER:
                description = replace(description, value_fn=_PER_HEATER[description.key](sub.key))
            entities.append(BlueBatteryBinarySensor(device, sub, description))
    async_add_entities(entities)


class BlueBatteryBinarySensor(BlueBatteryEntity, BinarySensorEntity):
    """Binärwert eines BlueBattery-Untergeräts."""

    entity_description: BlueBatteryBinaryDescription

    @property
    def available(self) -> bool:
        """Verbindungs- und Störungsmelder bleiben verfügbar, damit Automationen greifen."""
        if self.entity_description.always_available:
            return True
        if self.entity_description.needs_display_only:
            return self.device.online
        return super().available

    @property
    def is_on(self) -> bool | None:
        """Aktueller Zustand."""
        return self.entity_description.value_fn(self.block, self.device)
