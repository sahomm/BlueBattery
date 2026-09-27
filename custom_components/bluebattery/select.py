"""Auswahlen: Boiler, Energieart (Truma); Warmwasser, Elektrostufe, Priorität (Alde)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import BlueBatteryConfigEntry
from .const import (
    ALDE_EL_POWER,
    ALDE_GAS_PRIO,
    ALDE_WATER_MODES,
    OPT_TRUMA_COMBI_E,
    TRUMA_ENERGY_MODES,
    TRUMA_WATER_MODES,
)
from .data import to_number
from .entity import BlueBatteryEntity


@dataclass(frozen=True, kw_only=True)
class BlueBatterySelectDescription(SelectEntityDescription):
    """Auswahl: JSON-Feld und Zuordnung Option -> Wert."""

    kind: str
    field: str
    mapping: dict[str, int]
    option_flag: str | None = None  # nur anlegen, wenn diese Option gesetzt ist


SELECTS: tuple[BlueBatterySelectDescription, ...] = (
    BlueBatterySelectDescription(
        key="boiler", translation_key="truma_boiler", kind="truma",
        field="target_water", mapping=TRUMA_WATER_MODES,
    ),
    BlueBatterySelectDescription(
        key="energy_source", translation_key="truma_energy", kind="truma",
        field="energy_mode", mapping=TRUMA_ENERGY_MODES, option_flag=OPT_TRUMA_COMBI_E,
    ),
    BlueBatterySelectDescription(
        key="hot_water", translation_key="alde_water", kind="alde",
        field="target_water", mapping=ALDE_WATER_MODES,
    ),
    BlueBatterySelectDescription(
        key="electric_power", translation_key="alde_el_power", kind="alde",
        field="el_power", mapping=ALDE_EL_POWER,
    ),
    BlueBatterySelectDescription(
        key="energy_priority", translation_key="alde_gas_prio", kind="alde",
        field="gas_prio", mapping=ALDE_GAS_PRIO,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BlueBatteryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Auswahlen anlegen."""
    runtime = entry.runtime_data
    async_add_entities(
        BlueBatterySelect(runtime.device, sub, description)
        for sub in runtime.subdevices
        for description in SELECTS
        if sub.kind == description.kind
        and (description.option_flag is None or entry.options.get(description.option_flag))
    )


class BlueBatterySelect(BlueBatteryEntity, SelectEntity):
    """Heizungs-Einstellung mit festen Stufen."""

    entity_description: BlueBatterySelectDescription

    @property
    def options(self) -> list[str]:
        """Mögliche Stufen."""
        return list(self.entity_description.mapping)

    @property
    def available(self) -> bool:
        """Nur bedienbar, wenn die Heizung verbunden ist."""
        return super().available and self.device.heater_alive(self.sub.key) == 2

    @property
    def current_option(self) -> str | None:
        """Aktuelle Stufe."""
        block = self.block
        value = to_number(block.get(self.entity_description.field)) if block else None
        if value is None:
            return None
        return next(
            (name for name, code in self.entity_description.mapping.items() if code == value),
            None,
        )

    async def async_select_option(self, option: str) -> None:
        """Stufe senden."""
        await self.device.async_send(
            self.sub.key, {self.entity_description.field: self.entity_description.mapping[option]}
        )
