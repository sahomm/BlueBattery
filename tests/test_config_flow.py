"""Tests des Einrichtungsassistenten."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

import pytest
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import SOURCE_MQTT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from custom_components.bluebattery.config_flow import match_product
from custom_components.bluebattery.const import DOMAIN

from .conftest import BASE, NODE, PREFIX


@pytest.fixture
def expected_lingering_timers() -> bool:
    """Timer der MQTT-Nachbildung."""
    return True


def _info_msg(topic: str, payload: dict) -> MqttServiceInfo:
    return MqttServiceInfo(
        topic=topic, payload=json.dumps(payload), qos=0, retain=True,
        subscribed_topic="+/+/+/info", timestamp=time.time(),
    )


def test_match_product(info) -> None:
    """Fingerabdruck erkennt nur echte BlueBattery-Geräte – bei jedem Topic."""
    payload = json.dumps(info)
    assert match_product(f"{PREFIX}/info", payload) == (BASE, NODE, "BB-Display")
    assert match_product(f"camper/bb/{NODE}/info", payload) == ("camper/bb", NODE, "BB-Display")
    assert match_product("zigbee2mqtt/bridge/info", json.dumps({"version": "2.0"})) is None
    assert match_product(f"{BASE}/NOT-A-NODE/info", payload) is None


async def test_mqtt_discovery_flow(hass: HomeAssistant, info, status) -> None:
    """Erkennung -> Bestätigen -> Geräteauswahl -> Eintrag."""
    async def fake_collect(_hass, topic, _wait, stop_after_first=False):
        if topic.endswith("/status"):
            return [ReceiveMessage(topic, json.dumps(status), 0, True, topic, time.time())]
        return []

    async def fake_live(_hass, _node, base, wait=0):
        return base

    with patch("custom_components.bluebattery.config_flow._collect", fake_collect), patch(
        "custom_components.bluebattery.config_flow.find_live_base", fake_live
    ), patch("custom_components.bluebattery.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_MQTT}, data=_info_msg(f"{PREFIX}/info", info)
        )
        assert result["type"] is FlowResultType.FORM and result["step_id"] == "confirm"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["step_id"] == "select"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"selected": ["bb:A1B2C3", "truma"]}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["node"] == NODE
    assert result["options"]["selected"] == ["bb:A1B2C3", "truma"]
    assert "ble:AABBCC000001" in result["options"]["ignored"]


async def test_mqtt_discovery_rejects_foreign_device(hass: HomeAssistant) -> None:
    """Fremde info-Nachrichten werden still verworfen."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_MQTT}, data=_info_msg("zigbee2mqtt/bridge/info", {"version": "2"})
    )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "not_bluebattery"


async def test_find_live_base_ignores_stale_topic(hass: HomeAssistant, mqtt_mock, status) -> None:
    """Alte retained Nachrichten unter früherem Topic werden nicht genommen."""
    import asyncio

    from pytest_homeassistant_custom_component.common import async_fire_mqtt_message

    from custom_components.bluebattery import config_flow

    task = hass.async_create_task(config_flow.find_live_base(hass, NODE, "BB", wait=5))
    await asyncio.sleep(0.5)
    async_fire_mqtt_message(hass, f"BB/{NODE}/status", json.dumps(status), retain=True)
    async_fire_mqtt_message(hass, f"{PREFIX}/status", json.dumps(status), retain=False)
    assert await task == BASE


async def test_find_live_base_none_when_only_stale(hass: HomeAssistant, mqtt_mock, status) -> None:
    """Nur retained Status -> kein Live-Topic."""
    import asyncio

    from pytest_homeassistant_custom_component.common import async_fire_mqtt_message

    from custom_components.bluebattery import config_flow

    task = hass.async_create_task(config_flow.find_live_base(hass, NODE, BASE, wait=1.5))
    await asyncio.sleep(0.5)
    async_fire_mqtt_message(hass, f"{PREFIX}/status", json.dumps(status), retain=True)
    assert await task is None
