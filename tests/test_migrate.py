"""Tests für den Umstieg von der Firmware-Discovery."""

from __future__ import annotations

import json

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_mqtt_message

import custom_components.bluebattery as integration
from custom_components.bluebattery.const import DOMAIN
from custom_components.bluebattery.migrate import async_apply, async_plan, plan_to_options

from .conftest import NODE, PREFIX

NODE_MAC = NODE.split("_", 1)[1]


@pytest.fixture
def expected_lingering_timers() -> bool:
    """Timer der MQTT-Nachbildung."""
    return True


@pytest.fixture(autouse=True)
async def fast_setup(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch):
    """Nicht auf den ersten Status warten; Einträge nach dem Test entladen."""
    monkeypatch.setattr(integration, "FIRST_STATUS_WAIT", 0.01)
    yield
    for entry in hass.config_entries.async_entries(DOMAIN):
        await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


OLD = {
    # unique_id der Firmware-Discovery -> bisherige entity_id
    ("sensor", "bb_battery_voltage_v_A1B2C3"): "sensor.bluebattery_a1b2c3_aufbaubatterie_v",
    ("sensor", "bb_metering_land_A1B2C3"): "sensor.bluebattery_a1b2c3_land_energy_wh",
    ("binary_sensor", "bb_relais_status_A1B2C3"): "binary_sensor.bluebattery_a1b2c3_relais_status",
    ("climate", f"tin_truma_heater_{NODE_MAC}"): "climate.tin_adapter_heizung",
    ("select", f"truma_boiler_{NODE_MAC}"): "select.tin_adapter_boiler",
    ("sensor", f"truma_error_code_{NODE_MAC}"): "sensor.tin_adapter_fehlercode",
    ("sensor", f"bbd_ambient_temp_{NODE_MAC}"): "sensor.bb_display_umgebungstemperatur",
    ("sensor", "bbtank_F1E2D3C4B5A6_S1_level"): "sensor.fischwasser_s1_fullstand",
    ("sensor", "bluelevel_level_SSBT0002"): "sensor.bluelevel_ssbt0002_fullstand",
    ("sensor", "bluelevel_pitch_SSBT0001"): "sensor.bb_tank_ssbt0001_langsneigung",
    ("sensor", "mi_temp_000001"): "sensor.kuhlschrank_temperatur_alt",
    # passt nicht: anderes Gerät bzw. andere Domain
    ("sensor", "bb_battery_voltage_v_FFFFFF"): "sensor.fremde_batterie",
    ("binary_sensor", "bb_booster_limit_status_A1B2C3"): "binary_sensor.bluebattery_a1b2c3_booster_limit",
}


async def test_migration(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Vorbereiten -> alte Einträge weg -> abschließen: neue tragen die alten IDs."""
    ent_reg = er.async_get(hass)
    for (domain, uid), entity_id in OLD.items():
        ent_reg.async_get_or_create(domain, "mqtt", uid, suggested_object_id=entity_id.split(".", 1)[1])
    entry = MockConfigEntry(**entry_data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    async_fire_mqtt_message(hass, f"{PREFIX}/info", json.dumps(info), retain=True)
    async_fire_mqtt_message(hass, f"{PREFIX}/status", json.dumps(status))
    await hass.async_block_till_done()

    plan = async_plan(hass, entry.runtime_data.device, entry.options["selected"])
    old_ids = {i.old_entity_id for i in plan}
    assert "sensor.fremde_batterie" not in old_ids
    assert "binary_sensor.bluebattery_a1b2c3_booster_limit" not in old_ids  # Domain passt nicht
    assert old_ids == set(OLD.values()) - {"sensor.fremde_batterie", "binary_sensor.bluebattery_a1b2c3_booster_limit"}

    stored = plan_to_options(plan)
    # Discovery noch aktiv -> alles blockiert, nichts umbenannt
    result = async_apply(hass, stored, force_remove=False)
    assert result["renamed"] == [] and len(result["blocked"]) == len(plan)

    # Display-Discovery aus -> HA entfernt die alten Einträge
    for item in plan:
        ent_reg.async_remove(item.old_entity_id)
    result = async_apply(hass, stored, force_remove=False)
    assert sorted(result["renamed"]) == sorted(old_ids)
    for item in plan:
        reg_entry = ent_reg.async_get(item.old_entity_id)
        assert reg_entry is not None and reg_entry.platform == DOMAIN
        assert reg_entry.unique_id == item.new_unique_id
    await hass.async_block_till_done()
    assert hass.states.get("sensor.bluebattery_a1b2c3_aufbaubatterie_v").state == "13.08"
    assert hass.states.get("climate.tin_adapter_heizung").state == "heat"


async def test_migration_via_options_menu(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Menü: vorbereiten speichert den Plan, abschließen benennt um und räumt ihn weg."""
    ent_reg = er.async_get(hass)
    ent_reg.async_get_or_create("sensor", "mqtt", "bb_battery_voltage_v_A1B2C3", suggested_object_id="alt_spannung")
    entry = MockConfigEntry(**entry_data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    async_fire_mqtt_message(hass, f"{PREFIX}/status", json.dumps(status))
    await hass.async_block_till_done()

    flow = await hass.config_entries.options.async_init(entry.entry_id)
    assert flow["type"] == "menu" and "migrate_apply" not in flow["menu_options"]
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"next_step_id": "migrate_prepare"})
    assert flow["step_id"] == "migrate_prepare" and flow["description_placeholders"]["count"] == "1"
    await hass.config_entries.options.async_configure(flow["flow_id"], {})
    await hass.async_block_till_done()
    assert entry.options["migration_plan"][0]["old"] == "sensor.alt_spannung"

    ent_reg.async_remove("sensor.alt_spannung")  # Discovery im Display aus
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    assert "migrate_apply" in flow["menu_options"]
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"next_step_id": "migrate_apply"})
    assert flow["description_placeholders"]["still_there"] == "0"
    result = await hass.config_entries.options.async_configure(flow["flow_id"], {"force_remove": False})
    assert result["reason"] == "migration_done" and result["description_placeholders"]["renamed"] == "1"
    await hass.async_block_till_done()
    assert ent_reg.async_get("sensor.alt_spannung").platform == DOMAIN
    assert "migration_plan" not in entry.options
