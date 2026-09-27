"""Tests der Datenschicht (ohne Home Assistant)."""

from __future__ import annotations

from custom_components.bluebattery.data import (
    find_block,
    find_subdevices,
    split_info_topic,
    to_number,
    unknown_fields,
)


def test_to_number() -> None:
    """Zahlen, Texte mit Vorzeichen/Einheit und Platzhalter."""
    assert to_number(12) == 12.0
    assert to_number("+0.7") == 0.7
    assert to_number("-0.2") == -0.2
    assert to_number("12.6V") == 12.6
    assert to_number("--") is None
    assert to_number("") is None
    assert to_number(None) is None
    assert to_number(True) is None


def test_split_info_topic() -> None:
    """Basis und Geräte-ID aus dem info-Topic."""
    assert split_info_topic("BlueBattery/BB-Display/BB-D_X/info") == ("BlueBattery/BB-Display", "BB-D_X")
    assert split_info_topic("a/b/status") is None


def test_find_subdevices_uses_stable_keys(status) -> None:
    """Untergeräte werden über Hardware-IDs identifiziert, nicht über Positionen."""
    subs = find_subdevices(status)
    assert set(subs) == {
        "bb:A1B2C3",
        "truma",
        "tankctl:F1E2D3C4B5A6",
        "tank:F1E2D3C4B5A6:0",
        "tank:F1E2D3C4B5A6:1",
        "tank:F1E2D3C4B5A7:0",
        "tank:F1E2D3C4B5A8:0",
        "ble:AABBCC000001",
        "ble:AABBCC000002",
    }
    assert subs["tank:F1E2D3C4B5A6:1"].parent == "tankctl:F1E2D3C4B5A6"
    # BlueLevel+ ohne exportierten Controller hängt direkt am Display
    assert subs["tank:F1E2D3C4B5A7:0"].parent == "display"


def test_block_survives_index_shift(status) -> None:
    """Fällt ein Kanal weg und rutschen die Nummern, bleibt die Zuordnung korrekt."""
    grey = find_block(status, "tank:F1E2D3C4B5A8:0")
    shifted = {k: v for k, v in status.items() if k != "BlueLevel_0"}
    shifted["BlueLevel_0"] = shifted.pop("BlueLevel_3")
    assert find_block(shifted, "tank:F1E2D3C4B5A8:0") == grey
    assert find_block(shifted, "tank:F1E2D3C4B5A6:0") is None  # fehlt -> nicht verfügbar


def test_unknown_fields(status) -> None:
    """Neue Firmware-Felder werden erkannt."""
    assert unknown_fields(status) == set()
    status["truma"]["new_field"] = 1
    status["something"] = 2
    assert unknown_fields(status) == {"truma.new_field", "something"}
