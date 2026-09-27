"""Sensoren der BlueBattery-Integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfInformation,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import BlueBatteryConfigEntry
from .const import ALIVE_STATES, TRUMA_ENERGY_MODES
from .data import BlueBatteryDevice, SubDevice, to_number
from .entity import BlueBatteryEntity

CHARGER_PHASES = {0: "bulk", 1: "absorption", 2: "float", 3: "maintenance"}
TANK_TYPES = {0: "fresh", 1: "grey", 2: "black", 3: "other"}
BLE_TYPES = {0: "unknown", 1: "xiaomi", 2: "ruuvi"}
LITER_UNITS = {"l", "liter", "litre", "liters", "litres"}


def _vent_mode(value: Any) -> str | None:
    num = to_number(value)
    if num is None:
        return None
    num = int(num)
    if num == 0:
        return "off"
    if num == 11:
        return "eco"
    if num == 13:
        return "high"
    if 1 <= num <= 10:
        return f"level_{num}"
    return None


VENT_OPTIONS = ["off", "eco", "high", *[f"level_{i}" for i in range(1, 11)]]


def _num(field: str) -> Callable[[dict[str, Any], BlueBatteryDevice], float | None]:
    return lambda block, _device: to_number(block.get(field))


def _enum(field: str, mapping: dict[int, str]) -> Callable[[dict[str, Any], BlueBatteryDevice], str | None]:
    def get(block: dict[str, Any], _device: BlueBatteryDevice) -> str | None:
        num = to_number(block.get(field))
        return None if num is None else mapping.get(int(num))

    return get


def _battery_power(block: dict[str, Any], _device: BlueBatteryDevice) -> float | None:
    volt = to_number(block.get("battery_voltage_V"))
    amp = to_number(block.get("battery_current_A"))
    return None if volt is None or amp is None else round(volt * amp, 1)


def _alive(heater: str) -> Callable[[dict[str, Any], BlueBatteryDevice], str | None]:
    def get(_block: dict[str, Any], device: BlueBatteryDevice) -> str | None:
        value = device.heater_alive(heater)
        return None if value is None else ALIVE_STATES.get(value)

    return get


def _is_liters(block: dict[str, Any]) -> bool:
    return str(block.get("unit", "")).strip().lower() in LITER_UNITS


@dataclass(frozen=True, kw_only=True)
class BlueBatterySensorDescription(SensorEntityDescription):
    """Beschreibung eines Sensors: für welche Untergeräte, woher der Wert kommt."""

    kinds: tuple[str, ...]
    value_fn: Callable[[dict[str, Any], BlueBatteryDevice], Any]
    exists_fn: Callable[[dict[str, Any] | None], bool] = lambda block: True
    tank_volume: bool = False


def _has(field: str) -> Callable[[dict[str, Any] | None], bool]:
    """Nur anlegen, wenn das Feld beim Einrichten geliefert wird (Fähigkeiten je Gerät)."""
    return lambda block: block is None or field in block


TEMP = {
    "device_class": SensorDeviceClass.TEMPERATURE,
    "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
    "state_class": SensorStateClass.MEASUREMENT,
    "suggested_display_precision": 1,
}
VOLT = {
    "device_class": SensorDeviceClass.VOLTAGE,
    "native_unit_of_measurement": UnitOfElectricPotential.VOLT,
    "state_class": SensorStateClass.MEASUREMENT,
    "suggested_display_precision": 2,
}
AMP = {
    "device_class": SensorDeviceClass.CURRENT,
    "native_unit_of_measurement": UnitOfElectricCurrent.AMPERE,
    "state_class": SensorStateClass.MEASUREMENT,
    "suggested_display_precision": 2,
}
WATT = {
    "device_class": SensorDeviceClass.POWER,
    "native_unit_of_measurement": UnitOfPower.WATT,
    "state_class": SensorStateClass.MEASUREMENT,
    "suggested_display_precision": 0,
}
WH = {
    "device_class": SensorDeviceClass.ENERGY,
    "native_unit_of_measurement": UnitOfEnergy.WATT_HOUR,
    "state_class": SensorStateClass.TOTAL_INCREASING,
    "suggested_display_precision": 1,
}
AH = {
    "native_unit_of_measurement": "Ah",
    "state_class": SensorStateClass.TOTAL_INCREASING,
    "suggested_display_precision": 1,
}
RSSI = {
    "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
    "native_unit_of_measurement": SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    "state_class": SensorStateClass.MEASUREMENT,
    "entity_category": EntityCategory.DIAGNOSTIC,
    "entity_registry_enabled_default": False,
}
TILT = {
    "native_unit_of_measurement": "°",
    "state_class": SensorStateClass.MEASUREMENT,
    "suggested_display_precision": 1,
    "entity_category": EntityCategory.DIAGNOSTIC,
}

SENSORS: tuple[BlueBatterySensorDescription, ...] = (
    # --- Display ---
    BlueBatterySensorDescription(key="ambient_temp", translation_key="ambient_temp", kinds=("display",), value_fn=_num("ambient_temp_C"), **TEMP),
    BlueBatterySensorDescription(
        key="ambient_humidity", kinds=("display",), value_fn=_num("ambient_humidity_RH"),
        device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0,
    ),
    BlueBatterySensorDescription(key="ambient_dewpoint", translation_key="ambient_dewpoint", kinds=("display",), value_fn=_num("ambient_dewpoint_C"), **TEMP),
    BlueBatterySensorDescription(key="wifi_rssi", translation_key="wifi_rssi", kinds=("display",), value_fn=_num("rssi_dBm"), **RSSI),
    BlueBatterySensorDescription(
        key="cpu_temp", translation_key="cpu_temp", kinds=("display",), value_fn=_num("CPU_temp_C"),
        entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, **TEMP,
    ),
    BlueBatterySensorDescription(
        key="heap", translation_key="heap", kinds=("display",), value_fn=_num("heap_B"),
        device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.BYTES,
        state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    BlueBatterySensorDescription(
        key="uptime", translation_key="uptime", kinds=("display",), value_fn=_num("uptime_s"),
        device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.TOTAL_INCREASING, entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    BlueBatterySensorDescription(
        key="reset_reason", translation_key="reset_reason", kinds=("display",),
        value_fn=lambda _block, device: device.info.get("Reset reason"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # --- Batteriecomputer ---
    BlueBatterySensorDescription(
        key="soc", kinds=("battery",), value_fn=_num("battery_SOC_%"), exists_fn=_has("battery_SOC_%"),
        device_class=SensorDeviceClass.BATTERY, native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0,
    ),
    BlueBatterySensorDescription(key="battery_voltage", translation_key="battery_voltage", kinds=("battery",), value_fn=_num("battery_voltage_V"), **VOLT),
    BlueBatterySensorDescription(key="battery_current", translation_key="battery_current", kinds=("battery",), value_fn=_num("battery_current_A"), **AMP),
    BlueBatterySensorDescription(key="battery_power", translation_key="battery_power", kinds=("battery",), value_fn=_battery_power, **WATT),
    BlueBatterySensorDescription(key="starter_voltage", translation_key="starter_voltage", kinds=("battery",), value_fn=_num("car_voltage_V"), exists_fn=_has("car_voltage_V"), **VOLT),
    BlueBatterySensorDescription(key="solar_current", translation_key="solar_current", kinds=("battery",), value_fn=_num("solar_current_A"), exists_fn=_has("solar_current_A"), **AMP),
    BlueBatterySensorDescription(key="solar_power", translation_key="solar_power", kinds=("battery",), value_fn=_num("solar_power_W"), exists_fn=_has("solar_power_W"), **WATT),
    BlueBatterySensorDescription(key="pv_voltage", translation_key="pv_voltage", kinds=("battery",), value_fn=_num("pv_voltage_V"), exists_fn=_has("pv_voltage_V"), **VOLT),
    BlueBatterySensorDescription(key="pv_peak_power", translation_key="pv_peak_power", kinds=("battery",), value_fn=_num("pv_peak_power_W"), exists_fn=_has("pv_peak_power_W"), **WATT),
    BlueBatterySensorDescription(key="solar_charge", translation_key="solar_charge", kinds=("battery",), value_fn=_num("solar_charge_Ah"), exists_fn=_has("solar_charge_Ah"), **AH),
    BlueBatterySensorDescription(
        key="pv_charger_phase", translation_key="pv_charger_phase", kinds=("battery",),
        value_fn=_enum("pv_charger_phase", CHARGER_PHASES), exists_fn=_has("pv_charger_phase"),
        device_class=SensorDeviceClass.ENUM, options=list(CHARGER_PHASES.values()),
    ),
    BlueBatterySensorDescription(key="booster_current", translation_key="booster_current", kinds=("battery",), value_fn=_num("booster_current_A"), exists_fn=_has("booster_current_A"), **AMP),
    BlueBatterySensorDescription(key="booster_charge", translation_key="booster_charge", kinds=("battery",), value_fn=_num("booster_charge_Ah"), exists_fn=_has("booster_charge_Ah"), **AH),
    BlueBatterySensorDescription(
        key="booster_charger_phase", translation_key="booster_charger_phase", kinds=("battery",),
        value_fn=_enum("booster_charger_phase", CHARGER_PHASES), exists_fn=_has("booster_charger_phase"),
        device_class=SensorDeviceClass.ENUM, options=list(CHARGER_PHASES.values()),
    ),
    BlueBatterySensorDescription(key="device_temp", translation_key="device_temp", kinds=("battery",), value_fn=_num("device_temperature_C"), exists_fn=_has("device_temperature_C"), **TEMP),
    BlueBatterySensorDescription(key="solar_energy", translation_key="solar_energy", kinds=("battery",), value_fn=_num("solar_Wh"), exists_fn=_has("solar_Wh"), **WH),
    BlueBatterySensorDescription(key="battery_in_energy", translation_key="battery_in_energy", kinds=("battery",), value_fn=_num("battery_in_Wh"), exists_fn=_has("battery_in_Wh"), **WH),
    BlueBatterySensorDescription(key="battery_out_energy", translation_key="battery_out_energy", kinds=("battery",), value_fn=_num("battery_out_Wh"), exists_fn=_has("battery_out_Wh"), **WH),
    BlueBatterySensorDescription(key="booster_energy", translation_key="booster_energy", kinds=("battery",), value_fn=_num("booster_Wh"), exists_fn=_has("booster_Wh"), **WH),
    BlueBatterySensorDescription(key="land_energy", translation_key="land_energy", kinds=("battery",), value_fn=_num("land_Wh"), exists_fn=_has("land_Wh"), **WH),
    BlueBatterySensorDescription(key="battery_rssi", translation_key="ble_rssi", kinds=("battery",), value_fn=_num("rssi"), **RSSI),
    BlueBatterySensorDescription(
        key="booster_limit_status", translation_key="booster_limit_status", kinds=("battery",),
        value_fn=_num("booster_limit_status"), exists_fn=_has("booster_limit_status"),
        entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False,
    ),
    BlueBatterySensorDescription(
        key="snaps", translation_key="snaps", kinds=("battery",), value_fn=_num("snaps"),
        entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False,
    ),
    # --- Tank-Kanal ---
    BlueBatterySensorDescription(
        key="level", translation_key="tank_level", kinds=("tank",), value_fn=_num("display_level"),
        native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    BlueBatterySensorDescription(
        key="volume", translation_key="tank_volume", kinds=("tank",), value_fn=_num("fill"),
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0, tank_volume=True,
    ),
    BlueBatterySensorDescription(
        key="capacity", translation_key="tank_capacity", kinds=("tank",), value_fn=_num("capacity"),
        suggested_display_precision=0, tank_volume=True, entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BlueBatterySensorDescription(
        key="tank_type", translation_key="tank_type", kinds=("tank",), value_fn=_enum("type", TANK_TYPES),
        device_class=SensorDeviceClass.ENUM, options=list(TANK_TYPES.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BlueBatterySensorDescription(key="roll", translation_key="roll", kinds=("tank", "tank_ctl"), value_fn=_num("roll"), **TILT),
    BlueBatterySensorDescription(key="pitch", translation_key="pitch", kinds=("tank", "tank_ctl"), value_fn=_num("pitch"), **TILT),
    BlueBatterySensorDescription(key="rssi", translation_key="ble_rssi", kinds=("tank", "tank_ctl", "ble"), value_fn=_num("rssi"), **RSSI),
    # --- BLE-Sensor ---
    BlueBatterySensorDescription(key="temperature", kinds=("ble",), value_fn=_num("temperature"), **TEMP),
    BlueBatterySensorDescription(
        key="humidity", kinds=("ble",), value_fn=_num("humidity"),
        device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0,
    ),
    BlueBatterySensorDescription(
        key="battery", kinds=("ble",), value_fn=_num("battery"),
        device_class=SensorDeviceClass.BATTERY, native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BlueBatterySensorDescription(
        key="connection_duration", translation_key="connection_duration", kinds=("ble",), value_fn=_num("uptime"),
        device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False,
    ),
    BlueBatterySensorDescription(
        key="connection_count", translation_key="connection_count", kinds=("ble",), value_fn=_num("connCnt"),
        state_class=SensorStateClass.TOTAL_INCREASING, entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    # --- Truma ---
    BlueBatterySensorDescription(key="room_temp", translation_key="room_temp", kinds=("truma",), value_fn=_num("current_room"), **TEMP),
    BlueBatterySensorDescription(key="water_temp", translation_key="water_temp", kinds=("truma",), value_fn=_num("current_water"), **TEMP),
    BlueBatterySensorDescription(
        key="vent_mode", translation_key="vent_mode", kinds=("truma",),
        value_fn=lambda block, _d: _vent_mode(block.get("vent_mode")),
        device_class=SensorDeviceClass.ENUM, options=VENT_OPTIONS,
    ),
    BlueBatterySensorDescription(
        key="error_code", translation_key="error_code", kinds=("truma",), value_fn=_num("error"),
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BlueBatterySensorDescription(
        key="error_text", translation_key="error_text", kinds=("truma", "alde"),
        value_fn=lambda block, _d: (str(block.get("error_txt")).strip() or None)
        if block.get("error_txt") is not None else None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BlueBatterySensorDescription(
        key="supply_voltage", translation_key="supply_voltage", kinds=("truma",), value_fn=_num("voltage"),
        entity_category=EntityCategory.DIAGNOSTIC, **VOLT,
    ),
    BlueBatterySensorDescription(
        key="energy_mode", translation_key="energy_mode", kinds=("truma",),
        value_fn=_enum("energy_mode", {v: k for k, v in TRUMA_ENERGY_MODES.items()}),
        device_class=SensorDeviceClass.ENUM, options=list(TRUMA_ENERGY_MODES),
        entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False,
    ),
    BlueBatterySensorDescription(
        key="connection_state", translation_key="heater_connection", kinds=("truma",), value_fn=_alive("truma"),
        device_class=SensorDeviceClass.ENUM, options=list(ALIVE_STATES.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # --- Alde (experimentell) ---
    BlueBatterySensorDescription(key="zone1_temp", translation_key="zone1_temp", kinds=("alde",), value_fn=_num("current_zone1_C"), **TEMP),
    BlueBatterySensorDescription(
        key="zone2_temp", translation_key="zone2_temp", kinds=("alde",), value_fn=_num("current_zone2_C"),
        exists_fn=lambda block: block is None or bool(block.get("has2Zones")), **TEMP,
    ),
    BlueBatterySensorDescription(key="outdoor_temp", translation_key="outdoor_temp", kinds=("alde",), value_fn=_num("current_zone3_C"), **TEMP),
    BlueBatterySensorDescription(key="alde_water_temp", translation_key="water_temp", kinds=("alde",), value_fn=_num("current_water_C"), **TEMP),
    BlueBatterySensorDescription(
        key="alde_connection_state", translation_key="heater_connection", kinds=("alde",), value_fn=_alive("alde"),
        device_class=SensorDeviceClass.ENUM, options=list(ALIVE_STATES.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BlueBatteryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Sensoren für alle ausgewählten Untergeräte anlegen."""
    runtime = entry.runtime_data
    device = runtime.device
    entities = []
    for sub in runtime.subdevices:
        block = device.block(sub.key)
        for description in SENSORS:
            if sub.kind in description.kinds and description.exists_fn(block):
                entities.append(BlueBatterySensor(device, sub, description))
    async_add_entities(entities)


class BlueBatterySensor(BlueBatteryEntity, SensorEntity):
    """Messwert eines BlueBattery-Untergeräts."""

    entity_description: BlueBatterySensorDescription

    def __init__(
        self, device: BlueBatteryDevice, sub: SubDevice, description: BlueBatterySensorDescription
    ) -> None:
        """Initialisieren."""
        super().__init__(device, sub, description)
        if description.tank_volume:
            self._update_volume_unit(device.block(sub.key))

    def _update_volume_unit(self, block: dict[str, Any] | None) -> None:
        # Einheit ist im Gerät frei eingebbar; nur Liter werden als Volumen typisiert
        if block is None or _is_liters(block):
            self._attr_native_unit_of_measurement = UnitOfVolume.LITERS
            self._attr_device_class = SensorDeviceClass.VOLUME_STORAGE
        else:
            self._attr_native_unit_of_measurement = str(block.get("unit", "")).strip() or None
            self._attr_device_class = None

    @property
    def native_value(self) -> Any:
        """Aktueller Wert."""
        block = self.block
        if block is None:
            return None
        return self.entity_description.value_fn(block, self.device)

    @property
    def available(self) -> bool:
        """Verbindungsstatus der Heizung bleibt sichtbar, solange das Display sendet."""
        if self.entity_description.key in ("connection_state", "alde_connection_state"):
            return self.device.online
        return super().available

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Zusatzinfos für Tanks und BLE-Sensoren."""
        block = self.block
        if block is None:
            return None
        if self.sub.kind == "tank" and self.entity_description.key == "level":
            return {"tank_name": block.get("name"), "age_s": block.get("age_s")}
        if self.sub.kind == "ble" and self.entity_description.key == "temperature":
            return {"sensor_type": BLE_TYPES.get(int(to_number(block.get("type")) or 0))}
        return None
