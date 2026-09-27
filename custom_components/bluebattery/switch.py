"""Schalter: Gasbetrieb der Alde (experimentell)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import BlueBatteryConfigEntry
from .const import KEY_ALDE
from .data import to_number
from .entity import BlueBatteryEntity

GAS = SwitchEntityDescription(key="gas", translation_key="alde_gas")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BlueBatteryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Schalter anlegen."""
    runtime = entry.runtime_data
    async_add_entities(
        AldeGasSwitch(runtime.device, sub, GAS) for sub in runtime.subdevices if sub.key == KEY_ALDE
    )


class AldeGasSwitch(BlueBatteryEntity, SwitchEntity):
    """Gasbetrieb ein/aus."""

    @property
    def available(self) -> bool:
        """Nur bedienbar, wenn die Heizung verbunden ist."""
        return super().available and self.device.heater_alive(KEY_ALDE) == 2

    @property
    def is_on(self) -> bool | None:
        """`gas_on`."""
        block = self.block
        value = to_number(block.get("gas_on")) if block else None
        return None if value is None else value != 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Gas ein."""
        await self.device.async_send(KEY_ALDE, {"gas_on": 1})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Gas aus."""
        await self.device.async_send(KEY_ALDE, {"gas_on": 0})
