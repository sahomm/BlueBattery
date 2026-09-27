"""Gemeinsame Test-Fixtures."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from custom_components.bluebattery.const import (
    CONF_BASE_TOPIC,
    CONF_NODE,
    CONF_PRODUCT,
    DOMAIN,
    OPT_IGNORED,
    OPT_SELECTED,
    OPT_TIMEOUT,
)

FIXTURES = Path(__file__).parent / "fixtures"
NODE = "BB-D_A1B2C3D4E5F6"
BASE = "BlueBattery/BB-Display"
PREFIX = f"{BASE}/{NODE}"

SELECTED = [
    "bb:A1B2C3",
    "truma",
    "tankctl:F1E2D3C4B5A6",
    "tank:F1E2D3C4B5A6:0",
    "tank:F1E2D3C4B5A6:1",
    "tank:F1E2D3C4B5A7:0",
    "ble:AABBCC000001",
]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Custom Integrations in allen Tests laden."""


@pytest.fixture
def status() -> dict[str, Any]:
    """Anonymisierter Status aus einem echten Mitschnitt (Truma Combi 6)."""
    return copy.deepcopy(json.loads((FIXTURES / "status.json").read_text()))


@pytest.fixture
def info() -> dict[str, Any]:
    """`info` des Displays."""
    return json.loads((FIXTURES / "info.json").read_text())


@pytest.fixture
def entry_data() -> dict[str, Any]:
    """Daten und Optionen eines eingerichteten Displays."""
    return {
        "domain": DOMAIN,
        "unique_id": NODE,
        "title": "BB-Display D4E5F6",
        "data": {CONF_NODE: NODE, CONF_BASE_TOPIC: BASE, CONF_PRODUCT: "BB-Display"},
        "options": {
            OPT_SELECTED: SELECTED,
            OPT_IGNORED: ["tank:F1E2D3C4B5A8:0", "ble:AABBCC000002"],
            OPT_TIMEOUT: 90,
            "labels": {},
        },
    }
