#!/usr/bin/env python3
"""Erzeugt strings.json sowie translations/en.json und translations/de.json.

Alle Texte stehen hier als Paar (en, de), damit keine Übersetzung fehlt.
Aufruf: tools/gen_translations.py
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "custom_components" / "bluebattery"

T = lambda en, de: {"en": en, "de": de}  # noqa: E731

PHASES = {"bulk": T("Bulk", "Hauptladung"), "absorption": T("Absorption", "Absorption"),
          "float": T("Float", "Erhaltung"), "maintenance": T("Maintenance", "Pflege")}
ALIVE = {"offline": T("Offline", "Offline"), "not_connected": T("Not connected", "Nicht verbunden"),
         "ok": T("OK", "OK"), "error": T("Error", "Fehler")}
VENT = {"off": T("Off", "Aus"), "eco": T("Eco", "Eco"), "high": T("High", "High"),
        **{f"level_{i}": T(f"Level {i}", f"Stufe {i}") for i in range(1, 11)}}
ENERGY = {"gas": T("Gas/Diesel", "Gas/Diesel"), "mix_900": T("Mix 900 W", "Mix 900 W"),
          "mix_1800": T("Mix 1800 W", "Mix 1800 W"), "electric_900": T("Electric 900 W", "Elektro 900 W"),
          "electric_1800": T("Electric 1800 W", "Elektro 1800 W")}

SENSOR = {
    "ambient_temp": (T("Indoor temperature", "Innentemperatur"), None),
    "ambient_dewpoint": (T("Dew point", "Taupunkt"), None),
    "wifi_rssi": (T("Wi-Fi signal", "WLAN-Signal"), None),
    "cpu_temp": (T("CPU temperature", "CPU-Temperatur"), None),
    "heap": (T("Free memory", "Freier Speicher"), None),
    "uptime": (T("Uptime", "Laufzeit"), None),
    "reset_reason": (T("Last reset reason", "Letzter Neustartgrund"), None),
    "battery_voltage": (T("Battery voltage", "Batteriespannung"), None),
    "battery_current": (T("Battery current", "Batteriestrom"), None),
    "battery_power": (T("Battery power", "Batterieleistung"), None),
    "starter_voltage": (T("Starter battery voltage", "Starterbatterie"), None),
    "solar_current": (T("Solar current", "Solarstrom"), None),
    "solar_power": (T("Solar power", "Solarleistung"), None),
    "pv_voltage": (T("Solar voltage", "Solarspannung"), None),
    "pv_peak_power": (T("Solar peak power today", "Solar-Spitzenleistung heute"), None),
    "solar_charge": (T("Solar charge today", "Solarladung heute"), None),
    "pv_charger_phase": (T("Solar charging phase", "Solar-Ladephase"), PHASES),
    "booster_current": (T("Booster current", "Boosterstrom"), None),
    "booster_charge": (T("Booster charge today", "Boosterladung heute"), None),
    "booster_charger_phase": (T("Booster charging phase", "Booster-Ladephase"), PHASES),
    "device_temp": (T("Device temperature", "Gerätetemperatur"), None),
    "solar_energy": (T("Solar energy", "Solarenergie"), None),
    "battery_in_energy": (T("Battery energy in", "Batterie-Energie geladen"), None),
    "battery_out_energy": (T("Battery energy out", "Batterie-Energie entnommen"), None),
    "booster_energy": (T("Booster energy", "Booster-Energie"), None),
    "land_energy": (T("Shore power energy (estimated)", "Landstrom-Energie (geschätzt)"), None),
    "ble_rssi": (T("Bluetooth signal", "Bluetooth-Signal"), None),
    "booster_limit_status": (T("Booster limit (raw)", "Booster-Limit (Rohwert)"), None),
    "snaps": (T("Snapshot restores", "Snapshot-Wiederherstellungen"), None),
    "tank_level": (T("Level", "Füllstand"), None),
    "tank_volume": (T("Volume", "Inhalt"), None),
    "tank_capacity": (T("Capacity", "Kapazität"), None),
    "tank_type": (T("Tank type", "Tankart"), {"fresh": T("Fresh water", "Frischwasser"),
                  "grey": T("Grey water", "Grauwasser"), "black": T("Black water", "Schwarzwasser"),
                  "other": T("Other", "Sonstiges")}),
    "roll": (T("Roll", "Seitenneigung"), None),
    "pitch": (T("Pitch", "Längsneigung"), None),
    "connection_duration": (T("Connection duration", "Verbindungsdauer"), None),
    "connection_count": (T("Connections", "Verbindungen"), None),
    "room_temp": (T("Room temperature", "Raumtemperatur"), None),
    "water_temp": (T("Water temperature", "Wassertemperatur"), None),
    "vent_mode": (T("Fan", "Lüfter"), VENT),
    "error_code": (T("Error code", "Fehlercode"), None),
    "error_text": (T("Error text", "Fehlertext"), None),
    "supply_voltage": (T("Supply voltage", "Versorgungsspannung"), None),
    "energy_mode": (T("Energy source", "Energieart"), ENERGY),
    "heater_connection": (T("Connection status", "Verbindungsstatus"), ALIVE),
    "zone1_temp": (T("Zone 1 temperature", "Temperatur Zone 1"), None),
    "zone2_temp": (T("Zone 2 temperature", "Temperatur Zone 2"), None),
    "outdoor_temp": (T("Outdoor temperature", "Außentemperatur"), None),
}
BINARY = {
    "display_connected": T("Connection", "Verbindung"),
    "relay": T("Relay", "Relais"),
    "heater_connected": T("Heater connected", "Heizung verbunden"),
    "heater_problem": T("Heater fault", "Heizungsstörung"),
    "ac_supply": T("230 V supply", "230-V-Versorgung"),
}
SELECT = {
    "truma_boiler": (T("Boiler", "Boiler"), {"off": T("Off", "Aus"), "eco": T("Eco (40 °C)", "Eco (40 °C)"),
                     "high": T("High (55 °C)", "High (55 °C)"), "boost": T("Boost (60 °C)", "Boost (60 °C)")}),
    "truma_energy": (T("Energy source", "Energieart"), ENERGY),
    "alde_water": (T("Hot water", "Warmwasser"), {"off": T("Off", "Aus"), "on": T("On", "Ein"),
                   "boost": T("Boost", "Boost")}),
    "alde_el_power": (T("Electric power", "Elektroleistung"), {"off": T("Off", "Aus"), "1kw": T("1 kW", "1 kW"),
                      "2kw": T("2 kW", "2 kW"), "3kw": T("3 kW", "3 kW")}),
    "alde_gas_prio": (T("Energy priority", "Energie-Priorität"), {"electric": T("Electric", "Elektro"),
                      "gas": T("Gas", "Gas")}),
}
PRESETS = {"eco": T("Eco", "Eco"), "high": T("High", "High"), "vario_night": T("VarioHeat night", "VarioHeat Nacht"),
           "vario_auto": T("VarioHeat auto", "VarioHeat Auto"), "boost": T("Boost", "Boost")}
CLIMATE_ATTRS = {"command_pending": T("Command pending", "Befehl unterwegs"),
                 "room_heating_paused": T("Room heating paused (e.g. boiler boost)", "Raumheizung pausiert (z. B. Boiler-Boost)"),
                 "last_target_temperature": T("Last requested temperature", "Zuletzt gewünschte Temperatur")}

CONFIG = {
    "flow_title": T("{name}", "{name}"),
    "step": {
        "confirm": {"title": T("BlueBattery device found", "BlueBattery-Gerät gefunden"),
                    "description": T("{name} publishes on `{topic}`. Set it up? (Checking for current data can take up to a minute.)",
                                     "{name} sendet auf `{topic}`. Einrichten? (Die Prüfung auf aktuelle Daten kann bis zu einer Minute dauern.)")},
        "user": {"title": T("Search for BlueBattery devices", "BlueBattery-Geräte suchen"),
                 "description": T("Enter the MQTT topic configured on the device (without the device ID). Factory default: `BlueBattery/BB-Display`.",
                                  "MQTT-Topic eingeben, das im Gerät eingestellt ist (ohne Geräte-ID). Werkseinstellung: `BlueBattery/BB-Display`."),
                 "data": {"base_topic": T("MQTT topic", "MQTT-Topic")}},
        "pick": {"title": T("Several devices found", "Mehrere Geräte gefunden"),
                 "data": {"node": T("Device", "Gerät")}},
        "select": {"title": T("Select devices", "Geräte auswählen"),
                   "description": T("{name} provides {count} devices. Select which ones to add – you can change this later via **Configure**.\n\n{warning} Built-in Home Assistant discovery on the display active: {firmware_discovery}. If yes, entities will appear twice until it is switched off on the display.",
                                    "{name} liefert {count} Geräte. Wähle aus, welche übernommen werden – später jederzeit über **Konfigurieren** änderbar.\n\n{warning} Eingebaute Home-Assistant-Anbindung im Display aktiv: {firmware_discovery}. Falls ja, erscheinen Entitäten doppelt, bis sie im Display abgeschaltet wird."),
                   "data": {"selected": T("Devices", "Geräte")}},
    },
    "error": {"invalid_topic": T("Invalid topic (no + or # allowed).", "Ungültiges Topic (kein + oder # erlaubt)."),
              "no_fresh_data": T("No current data is arriving from this device (only old stored messages). Is the display switched on and connected to MQTT? Try again in a minute.",
                                 "Von diesem Gerät kommen keine aktuellen Daten (nur alte gespeicherte Nachrichten). Ist das Display eingeschaltet und mit MQTT verbunden? In einer Minute erneut versuchen."),
              "no_devices": T("No new BlueBattery device found under this topic. Is the device publishing?",
                              "Kein neues BlueBattery-Gerät unter diesem Topic gefunden. Sendet das Gerät?")},
    "abort": {"not_bluebattery": T("Not a BlueBattery device.", "Kein BlueBattery-Gerät."),
              "already_configured": T("This device is already set up.", "Dieses Gerät ist bereits eingerichtet.")},
}
OPTIONS = {"abort": {
    "nothing_to_migrate": T("No entities of the display's built-in Home Assistant discovery found – nothing to migrate.",
                            "Keine Entitäten der eingebauten Home-Assistant-Anbindung des Displays gefunden – nichts umzustellen."),
    "migration_done": T("Migration finished: {renamed} entities took over their previous IDs (history continues). Still blocked: {blocked} (old entity still exists – is discovery on the display switched off?). Not found: {missing}.",
                        "Umstieg abgeschlossen: {renamed} Entitäten haben ihre bisherigen IDs übernommen (Verlauf läuft weiter). Noch blockiert: {blocked} (alte Entität existiert noch – ist die Anbindung im Display abgeschaltet?). Nicht gefunden: {missing}.")},
  "step": {
  "init": {"title": T("BlueBattery", "BlueBattery"),
           "menu_options": {"settings": T("Devices and settings", "Geräte und Einstellungen"),
                            "migrate_prepare": T("Migration: prepare (take over IDs of the built-in discovery)", "Umstieg: vorbereiten (IDs der eingebauten Anbindung übernehmen)"),
                            "migrate_apply": T("Migration: finish", "Umstieg: abschließen")}},
  "migrate_prepare": {"title": T("Prepare migration", "Umstieg vorbereiten"),
                      "description": T("{count} entities of the display's built-in Home Assistant discovery can be taken over. After finishing, the new entities use these IDs – dashboards, automations and history keep working:\n\n{list}\n\n**Next:** save, then switch off **Home Assistant** in the MQTT settings of the display, wait one minute and choose **Migration: finish**.",
                                       "{count} Entitäten der eingebauten Home-Assistant-Anbindung des Displays können übernommen werden. Nach dem Abschluss tragen die neuen Entitäten diese IDs – Dashboards, Automationen und Verlauf laufen weiter:\n\n{list}\n\n**Danach:** speichern, im Display unter MQTT den Schalter **Home Assistant** ausschalten, eine Minute warten und **Umstieg: abschließen** wählen.")},
  "migrate_apply": {"title": T("Finish migration", "Umstieg abschließen"),
                    "description": T("{count} entities will take over their previous IDs. Old entities still present: {still_there} – if this is not 0, the built-in discovery on the display is probably still switched on.",
                                     "{count} Entitäten übernehmen ihre bisherigen IDs. Noch vorhandene alte Entitäten: {still_there} – ist das nicht 0, ist die eingebaute Anbindung im Display vermutlich noch eingeschaltet."),
                    "data": {"force_remove": T("Remove remaining old entities (only if discovery is already off)", "Verbliebene alte Entitäten entfernen (nur wenn die Anbindung bereits aus ist)")}},
  "settings": {
    "title": T("BlueBattery options", "BlueBattery-Optionen"),
    "description": T("New devices found: {new}\n\nDeselected devices are disabled (history is kept) unless removal is selected.",
                     "Neu gefundene Geräte: {new}\n\nAbgewählte Geräte werden deaktiviert (Verlauf bleibt), außer „Entfernen“ ist gewählt."),
    "data": {"selected": T("Devices", "Geräte"),
             "remove_deselected": T("Remove deselected devices instead of disabling them", "Abgewählte Geräte entfernen statt deaktivieren"),
             "timeout": T("Seconds without data until unavailable", "Sekunden ohne Daten bis „nicht verfügbar“"),
             "truma_extended_modes": T("Truma: offer VarioHeat/boost heating modes", "Truma: Heizmodi VarioHeat/Boost anbieten"),
             "truma_combi_e": T("Truma Combi E: energy source selectable", "Truma Combi E: Energieart wählbar")}}}}
ISSUES = {"new_devices": {"title": T("New BlueBattery device found", "Neues BlueBattery-Gerät gefunden"),
          "description": T("{title} provides new devices: {devices}.\n\nTo add them: **Settings → Devices & services → BlueBattery → Configure**.",
                           "{title} liefert neue Geräte: {devices}.\n\nHinzufügen: **Einstellungen → Geräte & Dienste → BlueBattery → Konfigurieren**.")}}
EXCEPTIONS = {"target_out_of_range": {"message": T("Temperature must be between {min} and {max} °C.",
                                                   "Die Temperatur muss zwischen {min} und {max} °C liegen.")}}


def pick(obj, lang):
    if isinstance(obj, dict) and set(obj) == {"en", "de"}:
        return obj[lang]
    if isinstance(obj, dict):
        return {k: pick(v, lang) for k, v in obj.items()}
    return obj


def build(lang):
    def with_states(items):
        out = {}
        for key, (name, states) in items.items():
            out[key] = {"name": name}
            if states:
                out[key]["state"] = states
        return out
    entity = {
        "sensor": with_states(SENSOR),
        "binary_sensor": {k: {"name": v} for k, v in BINARY.items()},
        "select": with_states(SELECT),
        "switch": {"alde_gas": {"name": T("Gas", "Gas")}},
        "climate": {
            "truma_heater": {"name": T("Heating", "Heizung"), "state_attributes": {
                "preset_mode": {"state": PRESETS}, **{k: {"name": v} for k, v in CLIMATE_ATTRS.items()}}},
            "alde_zone1": {"name": T("Heating zone 1", "Heizung Zone 1"),
                           "state_attributes": {k: {"name": v} for k, v in CLIMATE_ATTRS.items()}},
            "alde_zone2": {"name": T("Heating zone 2", "Heizung Zone 2"),
                           "state_attributes": {k: {"name": v} for k, v in CLIMATE_ATTRS.items()}},
        },
    }
    return pick({"config": CONFIG, "options": OPTIONS, "issues": ISSUES, "exceptions": EXCEPTIONS,
                 "entity": entity}, lang)


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


dump(BASE / "strings.json", build("en"))
dump(BASE / "translations" / "en.json", build("en"))
dump(BASE / "translations" / "de.json", build("de"))
print("ok")
