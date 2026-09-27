# Architektur – BlueBattery-Integration für Home Assistant

Stand: 2026-09-27 · Grundlage: interne, mit BlueBattery abgestimmte Schnittstellenbeschreibung (nicht öffentlich)

## 1. Ziele und Nicht-Ziele

**Ziele**
- BlueBattery-Geräte über MQTT **automatisch finden**, unabhängig vom Topic, das der Kunde eingestellt hat.
- Bei der Einrichtung **auswählen**, welche Geräte übernommen werden; später **neue Geräte hinzufügen**, ohne bestehende Entitäten oder deren History zu verändern.
- Die Pflege der HA-Anbindung aus der Firmware herausnehmen: Neue JSON-Felder = neue Zeile in einer Zuordnungstabelle.
- Heizung (Truma, Alde) sicher steuern – ehrlich gegenüber dem, was die Firmware zurückmeldet.

**Nicht-Ziele (vorerst)**
- Kein eigener MQTT-Client: Die Integration nutzt die HA-MQTT-Integration (Broker-Verbindung, Anmeldedaten).
- Keine Nutzung der Firmware-Discovery-Topics (`homeassistant/…`) als Datenquelle.
- Direkt sendende Geräte (BBX400 Pro, BB-Tank, BlueLevel direkt) erst in einer späteren Phase (Architektur ist dafür vorbereitet).

## 2. Begriffe

| Begriff | Bedeutung | Beispiel |
|---|---|---|
| **Hauptgerät** | Gerät mit eigenem MQTT-Präfix `<basis>/<node>` und eigener `info` | BB-Display `BB-D_A1B2C3D4E5F6` |
| **Untergerät** | Block im `status` des Hauptgeräts | Batteriecomputer, Truma, Tank-Kanal, BLE-Sensor |
| **Schlüssel** | stabile, hardwarebasierte ID eines Untergeräts | `tank:F1E2D3C4B5A6:0` |

## 3. Datenfluss

```
BB-Display ──MQTT──► Broker (Mosquitto) ──► HA-MQTT-Integration ──► bluebattery
   <basis>/<node>/info          (retained)           │
   <basis>/<node>/status        (retained + Intervall)│  subscribe
   <basis>/<node>/truma|alde/alive (retained, LWT)    │
   <basis>/<node>/set/truma|alde ◄────────────────────┘  publish (nicht retained)
```

Die Integration abonniert je Hauptgerät genau: `info`, `status`, `truma/alive`, `alde/alive`. Sie veröffentlicht nur auf `set/truma` bzw. `set/alde`.

## 4. Erkennung (Discovery)

### 4.1 Automatisch – unabhängig vom Kunden-Topic
- `manifest.json` → `"mqtt": ["+/+/info", "+/+/+/info", "+/+/+/+/info"]` deckt Basis-Topics mit 1–3 Ebenen ab:

  | Basis-Topic | vollständiges Topic | Muster |
  |---|---|---|
  | `BlueBattery` | `BlueBattery/<node>/info` | `+/+/info` |
  | `BlueBattery/BB-Display` | `BlueBattery/BB-Display/<node>/info` | `+/+/+/info` |
  | `camper/bb/display` | `camper/bb/display/<node>/info` | `+/+/+/+/info` |

- `info` ist retained → nach HA-Start wird jedes vorhandene Gerät sofort gemeldet.
- **Fingerabdruck** im Config-Flow (`async_step_mqtt`): Payload ist JSON, `ProductName` ∈ bekannte Produkte **und** vorletztes Topic-Segment passt zum Produktmuster:

  | ProductName | Node-Muster | Phase |
  |---|---|---|
  | `BB-Display` | `^BB-D_[0-9A-F]{12}$` | 1 |
  | `BB-Tank` | `^BB-T_[0-9A-F]{12}$` | später |
  | `BBX400 Pro` | `^BBX400Pro_[0-9A-F]{12}$` | später |

  Passt es nicht → Flow wird still abgebrochen (`not_bluebattery`), keine Meldung für den Nutzer.
- **Unique-ID des Config-Entries = `<node>`.** Ändert der Kunde später sein Topic, wird das Gerät erneut gefunden → bestehender Eintrag wird mit dem neuen Basis-Topic **aktualisiert** (kein Duplikat, History bleibt).
- Kommt von Kai ein **BB-Identifier** bzw. Ankündigungs-Topic (offene Frage an BlueBattery: F1), wird er als zusätzlicher, vorrangiger Weg ergänzt. Bestehende Einträge bleiben unverändert.

### 4.2 Manuell (Fallback)
Nutzer gibt das Basis-Topic ein (z. B. bei > 3 Ebenen). Die Integration lauscht 10 s auf `<basis>/+/info`, zeigt gefundene Geräte zur Auswahl und prüft denselben Fingerabdruck.

### 4.3 Hinweise während der Einrichtung
- **Firmware-Discovery noch aktiv?** Gibt es retained `homeassistant/+/<node>/#`, weist der Flow darauf hin (Doppelte Entitäten, siehe Kap. 9).
- **Retained Altlasten** unter anderen Präfixen mit gleichem `<node>` (z. B. `BB/<node>/…`) werden erkannt und im Diagnose-Export aufgeführt.

## 5. Config-Entries und Untergeräte

### 5.1 Ein Eintrag je Hauptgerät
`data`: `node`, `base_topic`, `product`. `options`: ausgewählte Untergeräte, Zeitlimits, Zusatzoptionen.

### 5.2 Untergeräte und stabile Schlüssel

| Untergerät | Quelle im `status` | Schlüssel | Hinweis |
|---|---|---|---|
| Display selbst | Wurzel | `display` | immer vorhanden, nicht abwählbar |
| Batteriecomputer | `BB_<id6>` | `bb:<id6>` | nur der im Display ausgewählte |
| Truma | `truma` | `truma` | nie zusammen mit Alde |
| Alde | `alde` | `alde` | Zone 2 nur bei `has2Zones` |
| BB-Tank-Controller | `tankDevices.<bda>` | `tankctl:<bda>` | |
| Tank-Kanal | `BlueLevel_<n>` | `tank:<bda>:<slot>` | **nie** `<n>` verwenden |
| BLE-Sensor | `bleSensors.<i>` | `ble:<mac>` | **nie** `<i>` verwenden |

### 5.3 Geräte-Registry
- Display: `identifiers = {("bluebattery", <node>)}`, Hersteller „BlueBattery“, Modell aus `ProductName`, Firmware aus `FirmwareVersion`, `configuration_url` aus `url`.
- Untergeräte: `identifiers = {("bluebattery", "<node>|<schlüssel>")}`, `via_device` = Display (Tank-Kanal → via Tank-Controller, falls vorhanden).

### 5.4 Entitäten-IDs
`unique_id = <node>|<schlüssel>|<feld>` – z. B. `BB-D_A1B2C3D4E5F6|tank:F1E2D3C4B5A6:0|level`. Unabhängig von Index, Name, Topic und Auswahlreihenfolge → **History bleibt bei jeder Neukonfiguration erhalten**.

### 5.5 Auswahl und spätere Erweiterung
1. **Einrichtung:** Nach Erkennung wartet der Flow auf einen `status` (retained → sofort) und zeigt alle gefundenen Untergeräte als Mehrfachauswahl (vorausgewählt: alle).
2. **Laufzeit:** Jeder `status` wird mit `ausgewählt ∪ abgelehnt` verglichen. Neue Schlüssel → **Reparatur-Hinweis** „Neues BlueBattery-Gerät gefunden: …“ (behebbar → öffnet die Optionen). Keine automatische Übernahme.
3. **Optionen (Neukonfiguration):** gleiche Mehrfachauswahl; Hinzufügen erzeugt nur neue Entitäten. **Abwählen** fragt: *deaktivieren* (Entitäten bleiben mit History, Standard) oder *entfernen*.
4. Fehlt ein ausgewähltes Untergerät im `status` (Tank nicht verfügbar, BLE-Sensor weg) → Entitäten **nicht verfügbar**, Gerät bleibt bestehen.

## 6. Datenverarbeitung

- **Ein Datenobjekt je Hauptgerät** (`BlueBatteryData`): letzter `info`, letzter `status`, Zeitstempel des letzten **frischen** (nicht retained) `status`, Heizungs-`alive`, anstehender Befehl.
- Eingang über `mqtt.async_subscribe` → JSON parsen → Untergeräte ermitteln → Dispatcher-Signal an Entitäten (push, `iot_class: local_push`).
- **Zuordnungstabellen** (`EntityDescription` je Block): Feldpfad, Plattform, Einheit, `device_class`, `state_class`, Anzeigegenauigkeit, Kategorie (Diagnose), `value_fn` für Umwandlungen:
  - `"--"`, `""`, `null` → kein Wert
  - Truma `voltage` `"12.6V"` → `12.6`
  - `roll`/`pitch` als Text → Zahl
  - Enums (`type`, Ladephasen, `vent_mode`, `heating_mode`) → übersetzte Zustände
- **Unbekannte Felder:** einmal je Feld ins Log (Debug/Info) und als **deaktivierte Diagnose-Entität** (roher Wert). So fällt eine neue Firmware sofort auf, ohne Fehler.
- Energiezähler `*_Wh`: `state_class: total_increasing` (täglicher Reset wird von HA als neuer Zyklus erkannt). `land_Wh` in Name/Doku als **geschätzt** gekennzeichnet.

## 7. Erreichbarkeit

| Ebene | Regel |
|---|---|
| Display | verfügbar, solange ein **frischer** `status` (Retain-Flag = 0) nicht älter als das Zeitlimit ist. Zeitlimit = Option „Sendeintervall“ (Standard 30 s) × 3, mind. 90 s. Retained `status` nach HA-Start füllt Werte, zählt aber **nicht** als online. |
| Heizung | `alive == 2` → verfügbar; zusätzlich Display verfügbar. Nach Display-Neustart (`uptime_s` < 180 s) keine Problem-Meldung für `alive` 0/1 (Schonfrist). |
| Tank-Kanal | vorhanden im aktuellen `status` **und** `available` ≠ false |
| Tank-Controller | `available` |
| BLE-Sensor | Objekt vorhanden; Einzelwert `"--"` → unbekannt (keine Frische-Info in der Firmware) |
| Batteriecomputer | Block vorhanden |

Zusätzliche Entitäten am Display: `binary_sensor` **Verbindung** (Konnektivität), Sensor **letzte Aktualisierung**, Diagnose **Reset-Ursache** (Code + Text), **Firmware**.

## 8. Steuerung

### 8.1 Grundsätze (laut Firmware)
- Befehle nicht retained, JSON mit Zahlen.
- **Keine Quittung** von der Firmware → die Integration wartet auf den passenden `status`. Bis dahin Attribut `pending` am Gerät; nach 90 s ohne passenden Wert → Warnung im Log und Reparatur-Hinweis bei Wiederholung.
- Keine Mehrfachsendung bei schnellem Klicken (Entprellung 2 s, gleicher Befehl wird nicht erneut gesendet, solange `pending`).
- Kurze Zwischenzustände vom CP plus (z. B. Boiler kurz 60) werden nicht entprellt angezeigt, aber lösen keine Befehle aus.

### 8.2 Truma
| Entität | Abbildung |
|---|---|
| `climate` Heizung | HVAC `off`/`heat`; Presets aus `heating_mode` (eco, high; night/auto/boost nur mit Option „erweiterte Heizmodi“); Soll 5–30 °C (Integration begrenzt, Firmware nicht); Ist = `current_room`. **Einschalten** sendet `{"heating_mode": m, "target_room": letzter Sollwert}` (Reihenfolge wichtig). HVAC-Aktion: `heating`, bzw. `idle` + Attribut „Raumheizung pausiert (Boiler-Boost)“, wenn `heating_mode ≠ 0` und `target_room == 0`. |
| `select` Boiler | Aus / Eco / High / Boost ↔ 0/40/55/60 |
| `select` Energieart | nur mit Option „Combi E“ (keine Fähigkeitserkennung in der Firmware) |
| `sensor` Lüfter | Enum 0 aus, 1–10 Stufe n, 11 eco, 13 high – nur lesend |
| `sensor` Wasser-Ist, Raum-Ist, Spannung, Fehlercode, Fehlertext | |
| `binary_sensor` Problem | `error ≠ 0` oder `alive == 3` (bzw. `alive ≠ 2` nach Schonfrist) – Grundlage für Frost-/Ausfall-Automationen |
| Klimaanlage | vorbereitet, aktiv sobald Werte bekannt (offene Frage an BlueBattery: F4) |

### 8.3 Alde (experimentell, ungetestet)
`climate` Zone 1 (+ Zone 2 bei `has2Zones`) mit `alde_on`/`target_zoneN`; `select` Warmwasser 0/50/65; `switch` Gas; `select` Elektro 0–3 kW; `select` Priorität; Sensoren Außen (`current_zone3_C`), Boiler, Zonenstatus, Fehlertext. In README und UI als **experimentell** gekennzeichnet.

## 9. Umstieg von der Firmware-Discovery

Ziel: **History und Statistiken behalten.** HA verknüpft beides mit der `entity_id`; eine Entität der Plattform `mqtt` kann nicht an `bluebattery` übergeben werden.

1. Einrichtung erkennt aktive Firmware-Discovery (Kap. 4.3) und bietet den Schritt **„Bestehende Entitäten übernehmen“** an.
2. Nutzer schaltet Discovery am Display aus. Die Firmware löscht `homeassistant/+/<node>/#`; ältere Layouts (z. B. `homeassistant/sensor/BL_…`) bleiben → Integration listet sie und bietet an, sie zu löschen (leere retained Nachricht, nur nach Bestätigung).
3. Die Integration ordnet alte Entitäten über bekannte Discovery-`unique_id`-Muster (z. B. `bb_battery_voltage_v_<id6>`, `tin_truma_heater_<mac>`, `mi_temp_<mac6>`) den neuen Feldern zu, entfernt die alten Registry-Einträge und legt die neuen mit **derselben `entity_id`** an.
4. Voraussetzung für durchgehende Statistiken: gleiche Einheit und gleiche `state_class`.

Wird zuerst im WoMo erprobt (mit Backup), bevor er in die README kommt.

## 10. Diagnose und Datenschutz
- `diagnostics.py`: letzter `info`/`status`, Optionen, erkannte Untergeräte, unbekannte Felder, Altlasten-Topics. **Geschwärzt:** MAC/`bda`, `<node>`, `url`/IP, Namen der BLE-Sensoren.
- Keine Anmeldedaten in der Integration (MQTT läuft über die HA-MQTT-Integration).

## 11. Projektstruktur

```
custom_components/bluebattery/
  __init__.py          Setup/Unload, Subscriptions, Datenobjekt
  manifest.json        domain bluebattery, dependencies [mqtt], mqtt-Topics, iot_class local_push
  config_flow.py       MQTT-Discovery, manuell, Geräteauswahl, Optionen, Umstieg
  const.py
  data.py              BlueBatteryData: Parsing, Untergeräte, Erreichbarkeit
  descriptions/        Zuordnungstabellen je Block (display, battery, tank, ble, truma, alde)
  entity.py            Basisklasse (Gerät, Verfügbarkeit, Dispatcher)
  sensor.py  binary_sensor.py  climate.py  select.py  switch.py
  repairs.py           „Neues Gerät gefunden“, Befehl ohne Wirkung, Altlasten
  diagnostics.py
  strings.json  translations/de.json  translations/en.json
  brand/               Logo (nur mit Zustimmung von BlueBattery)
tests/
  fixtures/            anonymisierte Mitschnitte (status/info je Szenario)
  test_config_flow.py  test_parsing.py  test_availability.py  test_climate_truma.py …
docs/  images/  README.md  README.en.md  LICENSE  hacs.json
.github/workflows/     hassfest, HACS-Validierung, Tests
```

## 12. Tests
- Fixtures aus den Mitschnitten, anonymisiert: Grundzustand, Boost, Heizung aus, Tank fehlt, BLE `"--"`, Display-Neustart (`alive` 0), retained-only nach HA-Start.
- Fälle: Fingerabdruck (positiv/negativ), Topic-Wechsel ohne Duplikat, Auswahl/Neukonfiguration ohne ID-Änderung, Index-Verschiebung `BlueLevel_<n>`, Befehlsreihenfolge beim Einschalten, Pending/Timeout.
- Werkzeug: `pytest-homeassistant-custom-component`.

## 13. Phasen

| Phase | Inhalt | Ergebnis |
|---|---|---|
| 1 | README (DE/EN), Architektur | diese Dokumente |
| 2 | Display nur lesend: Erkennung, Auswahl, Sensoren, Erreichbarkeit, Diagnose, Tests | erste Vorabversion |
| 3 | Truma-Steuerung; Alde experimentell | Steuerung |
| 4 | Umstieg im WoMo, History prüfen | Umstiegsanleitung |
| 5 | Direkt sendende Geräte, bebilderte Anleitungen | Ausbau |

## 14. Offene Punkte
- **Zwei Wege, ein Gerät:** Sobald direkt sendende Geräte unterstützt werden, kann z. B. ein BB-Tank über das Display **und** direkt kommen. Die Integration muss das erkennen (gleiche Hardware-ID) und pro Gerät einen Weg wählen lassen, statt doppelte Entitäten anzulegen.
- **Display reicht nur einen Batteriecomputer weiter** – ein zweiter nur direkt (siehe README).
- Offene Fragen an BlueBattery: BB-Identifier, Mindest-Firmware, Bedeutung `booster_limit_status`, Werte der Klimaanlage, Fähigkeiten der Heizung.
- Zustimmung BlueBattery zu Name/Logo.
- Mindest-HA-Version (wird bei Phase 2 anhand der genutzten APIs festgelegt).
