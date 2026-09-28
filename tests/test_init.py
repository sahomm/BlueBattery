"""Tests mit Home Assistant und nachgebildetem MQTT."""

from __future__ import annotations

import json
from typing import Any

import pytest
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_mqtt_message,
)

import custom_components.bluebattery as integration
from custom_components.bluebattery.const import DOMAIN

from .conftest import NODE, PREFIX


@pytest.fixture
def expected_lingering_timers() -> bool:
    """Der Wartungs-Timer stammt aus der MQTT-Nachbildung, nicht aus dieser Integration."""
    return True


@pytest.fixture(autouse=True)
async def fast_setup(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch):
    """Nicht auf den ersten Status warten; Einträge nach dem Test entladen."""
    monkeypatch.setattr(integration, "FIRST_STATUS_WAIT", 0.01)
    yield
    for entry in hass.config_entries.async_entries(DOMAIN):
        await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def _setup(hass: HomeAssistant, mqtt_mock, entry_data, info, status, retain=False) -> MockConfigEntry:
    entry = MockConfigEntry(**entry_data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    async_fire_mqtt_message(hass, f"{PREFIX}/info", json.dumps(info), retain=True)
    async_fire_mqtt_message(hass, f"{PREFIX}/truma/alive", "2", retain=True)
    async_fire_mqtt_message(hass, f"{PREFIX}/status", json.dumps(status), retain=retain)
    await hass.async_block_till_done()
    return entry


def _eid(hass: HomeAssistant, platform: str, key: str, field: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{NODE}|{key}|{field}")
    assert entity_id, f"{platform} {key}|{field} fehlt"
    return entity_id


async def test_sensors(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Werte aus dem Status landen in den Sensoren."""
    await _setup(hass, mqtt_mock, entry_data, info, status)
    assert hass.states.get(_eid(hass, "sensor", "bb:A1B2C3", "battery_voltage")).state == "13.08"
    assert hass.states.get(_eid(hass, "sensor", "bb:A1B2C3", "soc")).state == "69"
    assert float(hass.states.get(_eid(hass, "sensor", "bb:A1B2C3", "battery_power")).state) == pytest.approx(-19.0, abs=0.1)
    assert hass.states.get(_eid(hass, "sensor", "display", "ambient_temp")).state == "24.0"
    assert hass.states.get(_eid(hass, "sensor", "tank:F1E2D3C4B5A6:0", "level")).state == "53"
    assert hass.states.get(_eid(hass, "sensor", "tank:F1E2D3C4B5A7:0", "roll")).state == "0.7"
    assert hass.states.get(_eid(hass, "sensor", "ble:AABBCC000001", "temperature")).state == "8.5"
    assert hass.states.get(_eid(hass, "sensor", "truma", "vent_mode")).state == "eco"
    assert hass.states.get(_eid(hass, "binary_sensor", "display", "connected")).state == "on"
    assert hass.states.get(_eid(hass, "binary_sensor", "truma", "heater_problem")).state == "off"


async def test_retained_status_is_not_online(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Ein retained Status zeigt keinen Online-Zustand an."""
    await _setup(hass, mqtt_mock, entry_data, info, status, retain=True)
    assert hass.states.get(_eid(hass, "sensor", "bb:A1B2C3", "battery_voltage")).state == STATE_UNAVAILABLE
    assert hass.states.get(_eid(hass, "binary_sensor", "display", "connected")).state == "off"


async def test_missing_values(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """BLE-Wert "--" -> unbekannt; fehlender Tank-Kanal -> nicht verfügbar."""
    status["bleSensors"]["0"]["temperature"] = "--"
    del status["BlueLevel_0"]
    await _setup(hass, mqtt_mock, entry_data, info, status)
    assert hass.states.get(_eid(hass, "sensor", "ble:AABBCC000001", "temperature")).state == STATE_UNKNOWN
    assert hass.states.get(_eid(hass, "sensor", "tank:F1E2D3C4B5A6:0", "level")).state == STATE_UNAVAILABLE
    assert hass.states.get(_eid(hass, "sensor", "tank:F1E2D3C4B5A6:1", "level")).state == "0"


async def test_truma_turn_on_sends_mode_and_target(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Einschalten sendet Stufe UND Soll, Stufe zuerst."""
    status["truma"].update(heating_mode=0, target_room=0, vent_mode=0)
    await _setup(hass, mqtt_mock, entry_data, info, status)
    climate = _eid(hass, "climate", "truma", "truma_heater")
    assert hass.states.get(climate).state == "off"
    mqtt_mock.async_publish.reset_mock()
    await hass.services.async_call("climate", "set_temperature", {"entity_id": climate, "temperature": 17}, blocking=True)
    mqtt_mock.async_publish.assert_not_called()  # aus: nur merken
    await hass.services.async_call("climate", "set_hvac_mode", {"entity_id": climate, "hvac_mode": "heat"}, blocking=True)
    assert [c.args for c in mqtt_mock.async_publish.call_args_list] == [
        (f"{PREFIX}/set/truma", '{"heating_mode": 1, "target_room": 17}', 0, False)
    ]
    assert hass.states.get(climate).attributes["command_pending"] is True


async def test_truma_preset_and_boiler(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Stufe high und Boiler-Boost."""
    await _setup(hass, mqtt_mock, entry_data, info, status)
    climate = _eid(hass, "climate", "truma", "truma_heater")
    boiler = _eid(hass, "select", "truma", "boiler")
    mqtt_mock.async_publish.reset_mock()
    await hass.services.async_call("climate", "set_preset_mode", {"entity_id": climate, "preset_mode": "high"}, blocking=True)
    await hass.services.async_call("select", "select_option", {"entity_id": boiler, "option": "boost"}, blocking=True)
    assert [c.args for c in mqtt_mock.async_publish.call_args_list] == [
        (f"{PREFIX}/set/truma", '{"heating_mode": 10}', 0, False),
        (f"{PREFIX}/set/truma", '{"target_water": 60}', 0, False),
    ]


async def test_boost_pauses_room_heating(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Während Boiler-Boost ist die Raumheizung pausiert, obwohl heating_mode ≠ 0."""
    status["truma"].update(target_water=60, target_room=0, vent_mode=1)
    await _setup(hass, mqtt_mock, entry_data, info, status)
    state = hass.states.get(_eid(hass, "climate", "truma", "truma_heater"))
    assert state.state == "heat"
    assert state.attributes["room_heating_paused"] is True
    assert hass.states.get(_eid(hass, "sensor", "truma", "vent_mode")).state == "level_1"


async def test_heater_fault(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Fehlercode -> Heizungsstörung."""
    status["truma"]["error"] = 17
    await _setup(hass, mqtt_mock, entry_data, info, status)
    assert hass.states.get(_eid(hass, "binary_sensor", "truma", "heater_problem")).state == "on"


async def test_heater_fault_keeps_entities_but_rejects_commands(
    hass: HomeAssistant, mqtt_mock, entry_data, info, status
) -> None:
    """Störung (alive 3): verbunden bleibt an, Thermostat sichtbar, Befehle werden abgelehnt."""
    status["truma"].update(error=2212, alive=3)
    await _setup(hass, mqtt_mock, entry_data, info, status)
    async_fire_mqtt_message(hass, f"{PREFIX}/truma/alive", "3")  # Nachbildung verwirft 2. retained
    await hass.async_block_till_done()
    climate = _eid(hass, "climate", "truma", "truma_heater")
    assert hass.states.get(climate).state == "heat"
    assert hass.states.get(_eid(hass, "select", "truma", "boiler")).state != STATE_UNAVAILABLE
    assert hass.states.get(_eid(hass, "binary_sensor", "truma", "heater_connected")).state == "on"
    assert hass.states.get(_eid(hass, "binary_sensor", "truma", "heater_problem")).state == "on"
    assert hass.states.get(_eid(hass, "sensor", "truma", "connection_state")).state == "error"
    mqtt_mock.async_publish.reset_mock()
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call("climate", "set_temperature", {"entity_id": climate, "temperature": 18}, blocking=True)
    mqtt_mock.async_publish.assert_not_called()


async def test_new_device_issue(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Unbekanntes Untergerät -> Reparatur-Hinweis, keine automatische Übernahme."""
    await _setup(hass, mqtt_mock, entry_data, info, status)
    issue_id = f"new_devices_{NODE}"
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None
    status["bleSensors"]["2"] = {"index": 2, "name": "Kühlbox", "type": 1, "mac": "AA:BB:CC:00:00:03", "temperature": 5}
    async_fire_mqtt_message(hass, f"{PREFIX}/status", json.dumps(status))
    await hass.async_block_till_done()
    issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    assert issue is not None and "Kühlbox" in issue.translation_placeholders["devices"]
    assert er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{NODE}|ble:AABBCC000003|temperature") is None


async def test_deselect_disables_device(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Abwählen deaktiviert das Gerät; Entitäten (und damit die History) bleiben."""
    entry = await _setup(hass, mqtt_mock, entry_data, info, status)
    temp = _eid(hass, "sensor", "ble:AABBCC000001", "temperature")
    options: dict[str, Any] = dict(entry.options)
    options["selected"] = [k for k in options["selected"] if k != "ble:AABBCC000001"]
    hass.config_entries.async_update_entry(entry, options=options)
    await hass.async_block_till_done()
    assert er.async_get(hass).async_get(temp) is not None
    assert hass.states.get(temp) is None or hass.states.get(temp).state == STATE_UNAVAILABLE


async def test_tank_channel_under_bb_tank(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Kanäle eines BB-Tanks hängen unter dem BB-Tank, BlueLevel+ direkt am Display."""
    from homeassistant.helpers import device_registry as dr

    entry = await _setup(hass, mqtt_mock, entry_data, info, status)
    devices = {
        ident: dev
        for dev in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
        for _domain, ident in dev.identifiers
    }
    ctl = devices[f"{NODE}|tankctl:F1E2D3C4B5A6"]
    display = devices[NODE]
    channel = devices[f"{NODE}|tank:F1E2D3C4B5A6:1"]
    level = devices[f"{NODE}|tank:F1E2D3C4B5A7:0"]
    assert channel.via_device_id == ctl.id
    assert level.via_device_id == display.id


async def test_child_devices_linked_via_device_id(
    hass: HomeAssistant, mqtt_mock, entry_data, info, status, caplog: pytest.LogCaptureFixture
) -> None:
    """Jedes Untergerät hängt per `via_device_id` am Display bzw. BB-Tank."""
    from homeassistant.helpers import device_registry as dr

    entry = await _setup(hass, mqtt_mock, entry_data, info, status)
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    ids = {dev.id for dev in devices}
    display = next(dev for dev in devices if (DOMAIN, NODE) in dev.identifiers)
    children = [dev for dev in devices if dev is not display]
    assert children
    assert display.via_device_id is None
    for dev in children:
        assert dev.via_device_id in ids, dev.name
    assert "via_device" not in caplog.text


async def test_rediscovery_updates_topic_without_duplicate(
    hass: HomeAssistant, mqtt_mock, entry_data, info, status
) -> None:
    """Neues Topic mit frischen Daten -> Eintrag aktualisiert, kein zweiter Eintrag."""
    import asyncio

    from homeassistant.config_entries import SOURCE_MQTT
    from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

    entry = await _setup(hass, mqtt_mock, entry_data, info, status)
    new_base = "camper/bb"
    flow = hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_MQTT},
            data=MqttServiceInfo(
                topic=f"{new_base}/{NODE}/info", payload=json.dumps(info), qos=0, retain=True,
                subscribed_topic="+/+/+/info", timestamp=0,
            ),
        )
    )
    await asyncio.sleep(0.3)
    async_fire_mqtt_message(hass, f"{new_base}/{NODE}/status", json.dumps(status))
    result = await flow
    await hass.async_block_till_done()
    assert result["reason"] == "already_configured"
    assert entry.data["base_topic"] == new_base
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


async def test_firmware_version_kept_and_updated(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Firmware-Version wird nachgetragen, sobald info eintrifft, und nie geleert."""
    from homeassistant.helpers import device_registry as dr

    entry = await _setup(hass, mqtt_mock, entry_data, info, status)
    display = next(
        d for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
        if (DOMAIN, NODE) in d.identifiers
    )
    assert display.sw_version == info["FirmwareVersion"]
    new_info = {**info, "FirmwareVersion": "v2.0.1"}
    # An bestehende Abos liefert der Broker Aktualisierungen ohne Retain-Flag
    async_fire_mqtt_message(hass, f"{PREFIX}/info", json.dumps(new_info), retain=False)
    await hass.async_block_till_done()
    assert dr.async_get(hass).async_get(display.id).sw_version == "v2.0.1"


async def test_pending_target_shown_until_confirmed(hass: HomeAssistant, mqtt_mock, entry_data, info, status) -> None:
    """Nach set_temperature zeigt der Thermostat den gewünschten Wert bis zur Quittung."""
    await _setup(hass, mqtt_mock, entry_data, info, status)
    climate = _eid(hass, "climate", "truma", "truma_heater")
    await hass.services.async_call("climate", "set_temperature", {"entity_id": climate, "temperature": 24}, blocking=True)
    state = hass.states.get(climate)
    assert state.attributes["temperature"] == 24
    assert state.attributes["command_pending"] is True
    status["truma"]["target_room"] = 24
    async_fire_mqtt_message(hass, f"{PREFIX}/status", json.dumps(status))
    await hass.async_block_till_done()
    state = hass.states.get(climate)
    assert state.attributes["temperature"] == 24
    assert state.attributes["command_pending"] is False
