"""Tests des Einrichtungsassistenten."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import SOURCE_MQTT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from custom_components.bluebattery.config_flow import match_product
from custom_components.bluebattery.const import DOMAIN

from .conftest import BASE, NODE, PREFIX


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

    with patch("custom_components.bluebattery.config_flow._collect", fake_collect), patch(
        "custom_components.bluebattery.async_setup_entry", return_value=True
    ):
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
