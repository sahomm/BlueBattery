"""Klartexte zu den Fehlercodes der Truma Combi (Gas), selbst formuliert.

Die Firmware liefert `error` mit vorangestellter Ziffer (2202), das Bedienteil zeigt
die letzten drei Stellen mit Buchstabe (E202H).
"""

from __future__ import annotations

from typing import Final

NO_FAULT: Final = {"de": "Keine Störung gemeldet", "en": "No fault reported"}
UNKNOWN: Final = {
    "de": "Unbekannter Fehler {number} – siehe Truma-Anleitung",
    "en": "Unknown fault {number} – see Truma manual",
}

# (Buchstabe, Nummern, Deutsch, Englisch)
_TABLE: Final = (
    ("W", (17, 401), "Warmwasserbetrieb mit leerem Boiler – abkühlen lassen, Wasser füllen",
     "Water heating with empty boiler – let it cool down, fill water"),
    ("W", (18, 402), "Warmluft zu heiß – Luftrohre, Auslässe und Ansaugung prüfen",
     "Warm air too hot – check ducts, outlets and intake"),
    ("W", (21,), "Raumfühler oder Kabel defekt", "Room sensor or cable faulty"),
    ("W", (24, 303, 411), "Batteriespannung wird knapp – Batterie laden",
     "Battery voltage getting low – charge the battery"),
    ("W", (29,), "Kurzschluss am FrostControl-Heizelement", "Short circuit at FrostControl heating element"),
    ("W", (42, 412), "Fenster über dem Kamin offen – Fenster schließen", "Window above flue open – close it"),
    ("W", (43, 301, 417), "Überspannung – Ladegerät und Spannungsquellen prüfen",
     "Overvoltage – check charger and power sources"),
    ("W", (44, 302, 418), "Unterspannung – Batterie laden oder ersetzen",
     "Undervoltage – charge or replace the battery"),
    ("W", (45,), "230 V fehlen – Netz, Sicherung und Überhitzungsschutz prüfen",
     "No 230 V – check supply, fuse and overheat protection"),
    ("W", (407,), "230 V fehlen – Netz und Sicherung prüfen", "No 230 V – check supply and fuse"),
    ("E", (112, 121, 122, 202, 211, 212, 507, 516, 517),
     "Flamme/Gas gestört – Gasflasche, Ventile, Regler und Kamin prüfen",
     "Flame/gas fault – check cylinder, valves, regulator and flue"),
    ("W", (408,), "Kein Gas im Mischbetrieb (Elektro heizt weiter) – Gaszufuhr prüfen",
     "No gas in mixed mode (electric keeps heating) – check gas supply"),
    ("W", (255,), "Keine 12 V oder keine Verbindung zum Bedienteil", "No 12 V or no connection to control panel"),
    ("E", (607,), "Zu oft zurückgesetzt – 15 Minuten warten, dann erneut zurücksetzen",
     "Too many resets – wait 15 minutes, then reset again"),
    ("E", (621,), "Raumfühler oder Kabel defekt", "Room sensor or cable faulty"),
    ("E", (624,), "Kurzschluss am FrostControl-Heizelement", "Short circuit at FrostControl heating element"),
    ("E", (632,), "Überhitzungsschutz ausgelöst – an der Heizung zurückstellen",
     "Overheat protection tripped – reset it at the heater"),
)

FAULTS: Final = {
    number: (f"{letter}{number}H", {"de": de, "en": en})
    for letter, numbers, de, en in _TABLE
    for number in numbers
}


def language(code: str | None) -> str:
    """Deutsch bei deutscher Systemsprache, sonst Englisch."""
    return "de" if (code or "").lower().startswith("de") else "en"


def panel_code(error: int) -> str | None:
    """Anzeige am Bedienteil, z. B. E202H – nur für bekannte Codes."""
    fault = FAULTS.get(error % 1000)
    return fault[0] if fault else None


def describe(error: int, lang: str) -> str:
    """Klartext zu `error` (0 = keine Störung gemeldet)."""
    if error == 0:
        return NO_FAULT[lang]
    fault = FAULTS.get(error % 1000)
    if fault is None:
        return UNKNOWN[lang].format(number=error)
    return f"{fault[0]}: {fault[1][lang]}"
