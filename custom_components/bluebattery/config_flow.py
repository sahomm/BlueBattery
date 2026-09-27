"""Einrichtung: automatische Erkennung über MQTT, manuelle Eingabe, Geräteauswahl."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from .const import (
    CONF_BASE_TOPIC,
    CONF_NODE,
    CONF_PRODUCT,
    DEFAULT_BASE_TOPIC,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_TIMEOUT,
    MIN_TIMEOUT,
    OPT_IGNORED,
    OPT_REMOVE_DESELECTED,
    OPT_SELECTED,
    OPT_TIMEOUT,
    OPT_TRUMA_COMBI_E,
    OPT_TRUMA_EXTENDED_MODES,
    PRODUCT_NODE_PATTERNS,
)
from .data import SubDevice, find_subdevices, parse_json, split_info_topic

_LOGGER = logging.getLogger(__name__)

OPT_LABELS = "labels"
STATUS_WAIT = 8.0
SCAN_WAIT = 6.0
# Firmware-Standardintervall ist 60 s – so lange plus Reserve auf einen frischen Status warten
LIVE_WAIT = 75.0
MAX_BASE_DEPTH = 3


def match_product(topic: str, payload: Any) -> tuple[str, str, str] | None:
    """Fingerabdruck: (basis, node, produkt), wenn das Topic zu einem BlueBattery-Gerät gehört."""
    parts = split_info_topic(topic)
    info = parse_json(payload)
    if parts is None or info is None:
        return None
    base, node = parts
    product = info.get("ProductName")
    pattern = PRODUCT_NODE_PATTERNS.get(product) if isinstance(product, str) else None
    if pattern is None or not pattern.match(node) or not base:
        return None
    return base, node, product


async def _collect(
    hass: HomeAssistant, topic: str, wait: float, stop_after_first: bool = False
) -> list[ReceiveMessage]:
    """Nachrichten auf `topic` für `wait` Sekunden sammeln (retained kommen sofort)."""
    messages: list[ReceiveMessage] = []
    got = asyncio.Event()

    @callback
    def on_message(msg: ReceiveMessage) -> None:
        messages.append(msg)
        got.set()

    unsub = await mqtt.async_subscribe(hass, topic, on_message)
    try:
        if stop_after_first:
            async with asyncio.timeout(wait):
                await got.wait()
            await asyncio.sleep(0.2)  # weitere retained Nachrichten mitnehmen
        else:
            await asyncio.sleep(wait)
    except TimeoutError:
        pass
    finally:
        unsub()
    return messages


async def find_live_base(
    hass: HomeAssistant, node: str, known_base: str, wait: float = LIVE_WAIT
) -> str | None:
    """Unter welchem Basis-Topic sendet das Gerät gerade wirklich?

    Alte Firmware-Stände lassen retained `info`/`status` unter früheren Topics im
    Broker liegen (werden nicht aufgeräumt). Deshalb alle Basis-Topics mit dieser
    Geräte-ID sammeln und das nehmen, auf dem ein NICHT-retained Status ankommt.
    """
    bases = {known_base}
    for depth in range(MAX_BASE_DEPTH):
        pattern = "/".join(["+"] * (depth + 1) + [node, "info"])
        for msg in await _collect(hass, pattern, 0.5):
            if (match := match_product(msg.topic, msg.payload)) and match[1] == node:
                bases.add(match[0])

    live = asyncio.get_running_loop().create_future()
    unsubs = []
    for base in bases:

        @callback
        def on_status(msg: ReceiveMessage, base: str = base) -> None:
            if not msg.retain and not live.done():
                live.set_result(base)

        unsubs.append(await mqtt.async_subscribe(hass, f"{base}/{node}/status", on_status))
    try:
        async with asyncio.timeout(wait):
            return await live
    except TimeoutError:
        _LOGGER.debug("%s: kein frischer Status unter %s", node, sorted(bases))
        return None
    finally:
        for unsub in unsubs:
            unsub()


class BlueBatteryConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config-Flow für BlueBattery-Hauptgeräte."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialisieren."""
        self._base: str | None = None
        self._node: str | None = None
        self._product: str | None = None
        self._found: dict[str, tuple[str, str, str]] = {}
        self._subdevices: dict[str, SubDevice] = {}
        self._firmware_discovery = False
        self._live = False

    # --- automatisch -------------------------------------------------------------

    async def async_step_mqtt(self, discovery_info: MqttServiceInfo) -> ConfigFlowResult:
        """Gerät über seine retained `info`-Nachricht erkannt."""
        match = match_product(discovery_info.topic, discovery_info.payload)
        if match is None:
            return self.async_abort(reason="not_bluebattery")
        self._base, self._node, self._product = match
        await self.async_set_unique_id(self._node)
        live = await find_live_base(self.hass, self._node, self._base)
        if live is not None:
            # Topic geändert? -> bestehenden Eintrag aktualisieren statt Duplikat
            self._abort_if_unique_id_configured(updates={CONF_BASE_TOPIC: live})
            self._base, self._live = live, True
        else:
            # Nie auf Basis einer (evtl. veralteten) retained Nachricht umstellen
            self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {"name": self._title()}
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Bestätigen (erst, wenn unter dem Topic wirklich aktuelle Daten ankommen)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._live:
                live = await find_live_base(self.hass, self._node, self._base)
                if live is not None:
                    self._base, self._live = live, True
            if self._live:
                return await self.async_step_select()
            errors["base"] = "no_fresh_data"
        self._set_confirm_only()
        return self.async_show_form(
            step_id="confirm",
            errors=errors,
            description_placeholders={"name": self._title(), "topic": f"{self._base}/{self._node}"},
        )

    # --- manuell -------------------------------------------------------------------

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Basis-Topic eingeben und danach suchen."""
        errors: dict[str, str] = {}
        if user_input is not None:
            base = user_input[CONF_BASE_TOPIC].strip().strip("/")
            if not base or any(c in base for c in "+#"):
                errors[CONF_BASE_TOPIC] = "invalid_topic"
            else:
                messages = await _collect(self.hass, f"{base}/+/info", SCAN_WAIT)
                configured = self._async_current_ids(include_ignore=False)
                self._found = {}
                for msg in messages:
                    if (match := match_product(msg.topic, msg.payload)) and match[1] not in configured:
                        self._found[match[1]] = match
                if not self._found:
                    errors["base"] = "no_devices"
                elif len(self._found) == 1:
                    return await self._async_pick(next(iter(self._found)))
                else:
                    return await self.async_step_pick()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_BASE_TOPIC, default=DEFAULT_BASE_TOPIC): str}
            ),
            errors=errors,
        )

    async def async_step_pick(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Mehrere Geräte unter dem Topic gefunden."""
        if user_input is not None:
            return await self._async_pick(user_input[CONF_NODE])
        return self.async_show_form(
            step_id="pick",
            data_schema=vol.Schema(
                {vol.Required(CONF_NODE): vol.In({node: f"{m[2]} {node}" for node, m in self._found.items()})}
            ),
        )

    async def _async_pick(self, node: str) -> ConfigFlowResult:
        self._base, self._node, self._product = self._found[node]
        await self.async_set_unique_id(self._node)
        self._abort_if_unique_id_configured()
        live = await find_live_base(self.hass, self._node, self._base)
        if live is not None:
            self._base, self._live = live, True
        return await self.async_step_select()

    # --- Geräteauswahl -----------------------------------------------------------

    async def async_step_select(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Untergeräte auswählen."""
        if user_input is not None:
            selected = list(user_input.get(OPT_SELECTED, []))
            return self.async_create_entry(
                title=self._title(),
                data={CONF_NODE: self._node, CONF_BASE_TOPIC: self._base, CONF_PRODUCT: self._product},
                options={
                    OPT_SELECTED: selected,
                    OPT_IGNORED: [k for k in self._subdevices if k not in selected],
                    OPT_LABELS: {k: s.label for k, s in self._subdevices.items()},
                    OPT_TIMEOUT: DEFAULT_TIMEOUT,
                    OPT_TRUMA_EXTENDED_MODES: False,
                    OPT_TRUMA_COMBI_E: False,
                },
            )

        prefix = f"{self._base}/{self._node}"
        status_msgs = await _collect(self.hass, f"{prefix}/status", STATUS_WAIT, stop_after_first=True)
        status = parse_json(status_msgs[-1].payload) if status_msgs else None
        self._subdevices = find_subdevices(status) if status else {}
        legacy = await _collect(self.hass, f"homeassistant/+/{self._node}/#", 1.0)
        self._firmware_discovery = any(msg.payload for msg in legacy)

        options = {key: sub.label for key, sub in sorted(self._subdevices.items(), key=lambda i: i[1].kind)}
        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema(
                {vol.Optional(OPT_SELECTED, default=list(options)): cv.multi_select(options)}
            ),
            description_placeholders={
                "name": self._title(),
                "count": str(len(options)),
                "warning": "⚠️" if self._firmware_discovery else "",
                "firmware_discovery": "yes" if self._firmware_discovery else "no",
            },
        )

    def _title(self) -> str:
        return f"{self._product or 'BlueBattery'} {(self._node or '')[-6:]}".strip()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Optionen."""
        return BlueBatteryOptionsFlow()


class BlueBatteryOptionsFlow(OptionsFlow):
    """Neukonfiguration: Geräte hinzufügen/abwählen, Zeitlimit, Heizungsoptionen."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Formular."""
        entry = self.config_entry
        labels: dict[str, str] = dict(entry.options.get(OPT_LABELS, {}))
        current = entry.runtime_data.device.subdevices() if hasattr(entry, "runtime_data") else {}
        for key, sub in current.items():
            labels[key] = sub.label
        selected_before = list(entry.options.get(OPT_SELECTED, []))
        all_keys = sorted(set(labels) | set(selected_before))
        choices = {key: labels.get(key, key) for key in all_keys}

        if user_input is not None:
            selected = list(user_input.get(OPT_SELECTED, []))
            return self.async_create_entry(
                data={
                    **entry.options,
                    OPT_SELECTED: selected,
                    OPT_IGNORED: [k for k in all_keys if k not in selected],
                    OPT_LABELS: labels,
                    OPT_TIMEOUT: int(user_input[OPT_TIMEOUT]),
                    OPT_REMOVE_DESELECTED: bool(user_input.get(OPT_REMOVE_DESELECTED, False)),
                    OPT_TRUMA_EXTENDED_MODES: bool(user_input.get(OPT_TRUMA_EXTENDED_MODES, False)),
                    OPT_TRUMA_COMBI_E: bool(user_input.get(OPT_TRUMA_COMBI_E, False)),
                }
            )

        new = [k for k in current if k not in selected_before and k not in entry.options.get(OPT_IGNORED, [])]
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(OPT_SELECTED, default=selected_before): cv.multi_select(choices),
                    vol.Optional(OPT_REMOVE_DESELECTED, default=False): bool,
                    vol.Required(
                        OPT_TIMEOUT, default=entry.options.get(OPT_TIMEOUT, DEFAULT_TIMEOUT)
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_TIMEOUT, max=MAX_TIMEOUT)),
                    vol.Optional(
                        OPT_TRUMA_EXTENDED_MODES,
                        default=entry.options.get(OPT_TRUMA_EXTENDED_MODES, False),
                    ): bool,
                    vol.Optional(
                        OPT_TRUMA_COMBI_E, default=entry.options.get(OPT_TRUMA_COMBI_E, False)
                    ): bool,
                }
            ),
            description_placeholders={
                "new": ", ".join(labels.get(k, k) for k in new) if new else "–",
            },
        )
