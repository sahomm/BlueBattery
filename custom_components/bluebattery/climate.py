"""Heizungssteuerung (Truma, Alde) über BB-Display und TIN-Adapter."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import BlueBatteryConfigEntry
from .const import (
    DOMAIN,
    KEY_ALDE,
    KEY_TRUMA,
    OPT_TRUMA_EXTENDED_MODES,
    TRUMA_BASIC_PRESETS,
    TRUMA_DEFAULT_TARGET,
    TRUMA_HEATING_MODES,
    TRUMA_MAX_TEMP,
    TRUMA_MIN_TEMP,
)
from .data import BlueBatteryDevice, SubDevice, to_number
from .entity import BlueBatteryEntity

ATTR_LAST_TARGET = "last_target_temperature"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BlueBatteryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Thermostate anlegen."""
    runtime = entry.runtime_data
    device = runtime.device
    entities: list[ClimateEntity] = []
    for sub in runtime.subdevices:
        if sub.key == KEY_TRUMA:
            entities.append(
                TrumaClimate(device, sub, bool(entry.options.get(OPT_TRUMA_EXTENDED_MODES)))
            )
        elif sub.key == KEY_ALDE:
            entities.append(AldeZoneClimate(device, sub, 1))
            block = device.block(KEY_ALDE)
            if block is None or block.get("has2Zones"):
                entities.append(AldeZoneClimate(device, sub, 2))
    async_add_entities(entities)


class _HeaterClimate(BlueBatteryEntity, ClimateEntity, RestoreEntity):
    """Gemeinsame Basis: Soll-Speicher, Verfügbarkeit, Befehl ausstehend."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1
    _attr_min_temp = TRUMA_MIN_TEMP
    _attr_max_temp = TRUMA_MAX_TEMP
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _enable_turn_on_off_backwards_compatibility = False

    heater: str

    def __init__(self, device: BlueBatteryDevice, sub: SubDevice, key: str) -> None:
        """Initialisieren."""
        super().__init__(device, sub, ClimateEntityDescription(key=key, translation_key=key))
        self._last_target: int = TRUMA_DEFAULT_TARGET

    async def async_added_to_hass(self) -> None:
        """Letzten gewünschten Sollwert wiederherstellen."""
        await super().async_added_to_hass()
        if (state := await self.async_get_last_state()) is not None:
            restored = to_number(state.attributes.get(ATTR_LAST_TARGET))
            if restored is not None and TRUMA_MIN_TEMP <= restored <= TRUMA_MAX_TEMP:
                self._last_target = int(restored)

    @property
    def available(self) -> bool:
        """Nur bedienbar, wenn Display sendet und die Heizung verbunden ist."""
        return super().available and self.device.heater_alive(self.heater) == 2

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Befehl unterwegs, letzter Sollwert."""
        return {
            "command_pending": self.heater in self.device.pending,
            ATTR_LAST_TARGET: self._last_target,
        }

    def _check_target(self, value: float) -> int:
        target = int(round(value))
        if not TRUMA_MIN_TEMP <= target <= TRUMA_MAX_TEMP:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="target_out_of_range",
                translation_placeholders={"min": str(TRUMA_MIN_TEMP), "max": str(TRUMA_MAX_TEMP)},
            )
        return target


class TrumaClimate(_HeaterClimate):
    """Truma Combi: aus/heizen, Stufen eco/high (optional VarioHeat/Boost), Raum-Soll."""

    heater = KEY_TRUMA
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, device: BlueBatteryDevice, sub: SubDevice, extended: bool) -> None:
        """Initialisieren."""
        super().__init__(device, sub, "truma_heater")
        self._attr_preset_modes = (
            list(TRUMA_HEATING_MODES.values()) if extended else list(TRUMA_BASIC_PRESETS)
        )
        self._last_mode: int = 1

    def _field(self, name: str) -> float | None:
        block = self.block
        return to_number(block.get(name)) if block else None

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Aus, wenn `heating_mode` 0 ist."""
        mode = self._field("heating_mode")
        if mode is None:
            return None
        return HVACMode.OFF if mode == 0 else HVACMode.HEAT

    @property
    def preset_mode(self) -> str | None:
        """Heizstufe."""
        mode = self._field("heating_mode")
        if mode is None or mode == 0:
            return None
        return TRUMA_HEATING_MODES.get(int(mode))

    @property
    def current_temperature(self) -> float | None:
        """Raum-Ist."""
        return self._field("current_room")

    @property
    def target_temperature(self) -> float | None:
        """Raum-Soll; bei 0 (aus bzw. pausiert) der zuletzt gewünschte Wert."""
        target = self._field("target_room")
        if target is not None and target > 0:
            self._last_target = int(target)
            return target
        return self._last_target

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Zusätzlich: Raumheizung pausiert (z. B. während Boiler-Boost)."""
        attrs = super().extra_state_attributes
        mode = self._field("heating_mode")
        target = self._field("target_room")
        attrs["room_heating_paused"] = bool(mode) and target == 0
        return attrs

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Ein-/Ausschalten. Einschalten sendet Stufe UND Soll (Reihenfolge wichtig)."""
        if hvac_mode == HVACMode.OFF:
            await self.device.async_send(self.heater, {"heating_mode": 0})
            return
        await self._async_turn_on(self._current_or_last_mode())

    async def async_turn_on(self) -> None:
        """Einschalten."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Ausschalten."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Heizstufe wählen (schaltet bei Bedarf ein)."""
        code = next((c for c, name in TRUMA_HEATING_MODES.items() if name == preset_mode), None)
        if code is None:
            raise ServiceValidationError(f"Unbekannte Heizstufe: {preset_mode}")
        self._last_mode = code
        if self.hvac_mode == HVACMode.OFF:
            await self._async_turn_on(code)
        else:
            await self.device.async_send(self.heater, {"heating_mode": code})

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Raum-Soll setzen. Bei ausgeschalteter Heizung nur merken (nicht einschalten)."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
            self._last_target = self._check_target(temp)
        if kwargs.get(ATTR_HVAC_MODE) == HVACMode.OFF:
            await self.async_set_hvac_mode(HVACMode.OFF)
            return
        if kwargs.get(ATTR_HVAC_MODE) == HVACMode.HEAT or self.hvac_mode == HVACMode.HEAT:
            if self.hvac_mode == HVACMode.OFF:
                await self._async_turn_on(self._current_or_last_mode())
            elif temp is not None:
                await self.device.async_send(self.heater, {"target_room": self._last_target})
            return
        # Heizung aus: Wert wird beim nächsten Einschalten mitgeschickt
        self.async_write_ha_state()

    def _current_or_last_mode(self) -> int:
        mode = self._field("heating_mode")
        if mode:
            self._last_mode = int(mode)
        return self._last_mode

    async def _async_turn_on(self, mode: int) -> None:
        # Das Display merkt sich das Soll nur aus MQTT-Befehlen (Start 20 °C) –
        # deshalb immer beides senden, Stufe zuerst.
        await self.device.async_send(
            self.heater, {"heating_mode": mode, "target_room": self._last_target}
        )


class AldeZoneClimate(_HeaterClimate):
    """Alde-Zone (experimentell): Ein/Aus gilt für die ganze Heizung."""

    heater = KEY_ALDE
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, device: BlueBatteryDevice, sub: SubDevice, zone: int) -> None:
        """Initialisieren."""
        super().__init__(device, sub, f"alde_zone{zone}")
        self._zone = zone

    def _field(self, name: str) -> float | None:
        block = self.block
        return to_number(block.get(name)) if block else None

    @property
    def hvac_mode(self) -> HVACMode | None:
        """`alde_on` 0/1."""
        on = self._field("alde_on")
        if on is None:
            return None
        return HVACMode.HEAT if on else HVACMode.OFF

    @property
    def current_temperature(self) -> float | None:
        """Zonen-Ist (fehlt bei ungültigem Messwert)."""
        return self._field(f"current_zone{self._zone}_C")

    @property
    def target_temperature(self) -> float | None:
        """Zonen-Soll."""
        target = self._field(f"target_zone{self._zone}")
        if target is not None and target > 0:
            self._last_target = int(target)
            return target
        return self._last_target

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Alde ein/aus (betrifft alle Zonen)."""
        await self.device.async_send(self.heater, {"alde_on": 0 if hvac_mode == HVACMode.OFF else 1})

    async def async_turn_on(self) -> None:
        """Einschalten."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Ausschalten."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Zonen-Soll (Firmware begrenzt selbst auf 5–30 °C)."""
        payload: dict[str, int] = {}
        if kwargs.get(ATTR_HVAC_MODE) is not None:
            payload["alde_on"] = 0 if kwargs[ATTR_HVAC_MODE] == HVACMode.OFF else 1
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
            self._last_target = self._check_target(temp)
            payload[f"target_zone{self._zone}"] = self._last_target
        if payload:
            await self.device.async_send(self.heater, payload)
