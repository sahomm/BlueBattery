"""Diagnose-Export (Adressen und Namen geschwärzt)."""

from __future__ import annotations

import time
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import BlueBatteryConfigEntry
from .const import REDACT_KEYS


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: BlueBatteryConfigEntry
) -> dict[str, Any]:
    """Diagnosedaten eines Hauptgeräts."""
    device = entry.runtime_data.device
    fresh_age = None if device.last_fresh is None else round(time.monotonic() - device.last_fresh)
    return async_redact_data(
        {
            "entry": {"data": dict(entry.data), "options": dict(entry.options)},
            "online": device.online,
            "seconds_since_fresh_status": fresh_age,
            "heater_alive": device.alive,
            "pending_commands": {k: v.payload for k, v in device.pending.items()},
            "unknown_fields": sorted(device.reported_unknown),
            "subdevices_in_status": sorted(device.subdevices()),
            "info": device.info,
            "status": device.status,
        },
        REDACT_KEYS | {"labels"},
    )
