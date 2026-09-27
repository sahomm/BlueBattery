"""Basisklasse der BlueBattery-Entitäten."""

from __future__ import annotations

from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity, EntityDescription

from .const import DOMAIN, KEY_ALDE, KEY_DISPLAY, KEY_TRUMA, MANUFACTURER
from .data import BlueBatteryDevice, SubDevice


def device_identifier(node: str, key: str) -> tuple[str, str]:
    """Identifier eines (Unter-)Geräts in der Geräte-Registry."""
    return (DOMAIN, node if key == KEY_DISPLAY else f"{node}|{key}")


def build_device_info(device: BlueBatteryDevice, sub: SubDevice) -> DeviceInfo:
    """DeviceInfo für Display bzw. Untergerät.

    Ohne Verweis auf das übergeordnete Gerät: `via_device_id` braucht dessen
    Registry-ID und wird in `_register_devices` gesetzt."""
    info = device.info
    if sub.key == KEY_DISPLAY:
        display = DeviceInfo(
            identifiers={device_identifier(device.node, KEY_DISPLAY)},
            manufacturer=MANUFACTURER,
            model=info.get("ProductName", "BB-Display"),
            name=f"{info.get('ProductName', 'BB-Display')} {device.node[-6:]}",
            serial_number=device.node,
        )
        # Nur setzen, wenn bekannt – sonst würde ein früher Start (info noch nicht
        # da) die vorhandene Firmware-Version in der Registry löschen
        if info.get("FirmwareVersion"):
            display["sw_version"] = info["FirmwareVersion"]
        if info.get("url"):
            display["configuration_url"] = info["url"]
        return display
    models = {
        "battery": "Batteriecomputer",
        "truma": "Truma über TIN-Adapter",
        "alde": "Alde über TIN-Adapter",
        "tank_ctl": "BB-Tank",
        "tank": "Tank-Kanal",
        "ble": "BLE-Sensor",
    }
    names = {KEY_TRUMA: "Truma", KEY_ALDE: "Alde"}
    return DeviceInfo(
        identifiers={device_identifier(device.node, sub.key)},
        manufacturer=MANUFACTURER if sub.kind not in ("truma", "alde", "ble") else None,
        model=models.get(sub.kind),
        name=names.get(sub.key, sub.label),
    )


class BlueBatteryEntity(Entity):
    """Gemeinsames Verhalten: Push-Updates, stabile IDs, Verfügbarkeit."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        device: BlueBatteryDevice,
        sub: SubDevice,
        description: EntityDescription,
    ) -> None:
        """Entität für ein Feld eines Untergeräts."""
        self.device = device
        self.sub = sub
        self.entity_description = description
        # Stabil: unabhängig von Index, Name, Topic und Auswahlreihenfolge
        self._attr_unique_id = f"{device.node}|{sub.key}|{description.key}"
        self._attr_device_info = build_device_info(device, sub)

    @property
    def block(self) -> dict[str, Any] | None:
        """Aktueller Datenblock des Untergeräts."""
        return self.device.block(self.sub.key)

    @property
    def available(self) -> bool:
        """Display sendet und das Untergerät ist im Status enthalten."""
        if not self.device.online:
            return False
        block = self.block
        if block is None:
            return False
        return block.get("available", True) is not False

    async def async_added_to_hass(self) -> None:
        """Auf Statusänderungen hören."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, self.device.signal, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
