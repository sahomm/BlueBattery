# BlueBattery für Home Assistant

🇩🇪 Deutsch | [🇬🇧 English](https://github.com/sahomm/BlueBattery/blob/main/README.en.md)

<p align="center">
  <img src="https://raw.githubusercontent.com/sahomm/BlueBattery/main/custom_components/bluebattery/brand/icon.png" alt="BlueBattery" width="96">
  &nbsp;&nbsp;
  <img src="https://raw.githubusercontent.com/sahomm/BlueBattery/main/images/produkt-bb-display.png" alt="BB-Display mit WLAN und MQTT" width="260">
</p>

Bring dein Wohnmobil oder deinen Wohnwagen in **Home Assistant**: Batterie und Solar, Tanks, Temperaturen und die **Heizung (Truma/Alde)** – alles über das **[BB-Display](https://www.blue-battery.com/product-page/bb-display)** von [BlueBattery](https://www.blue-battery.com). Die Integration findet dein BB-Display automatisch und übernimmt alle Geräte, die dort gekoppelt sind.

<p align="center">
  <img src="https://raw.githubusercontent.com/sahomm/BlueBattery/main/images/integration-geraete.png" alt="BlueBattery in Home Assistant: BB-Display mit allen gekoppelten Geräten" width="560">
  <br><em>Ein BB-Display mit Batteriecomputer, Tanks, Temperatursensoren und Truma</em>
</p>

> **Voraussetzung: ein BB-Display.** Die Integration bindet BlueBattery-Geräte ausschließlich **über das BB-Display** ein – Batteriecomputer, BlueLevel/BB-Tank, Temperatursensoren und Truma/Alde über den TIN-Adapter. **Ohne BB-Display funktioniert die Integration (noch) nicht.**

## Was du damit machen kannst

Die BlueBattery-App zeigt dir alles an. Mit Home Assistant **reagiert dein Fahrzeug** – auch wenn niemand an Bord ist. Für jedes Beispiel gibt es eine fertige Vorlage zum Import mit einem Klick.

| | Anwendung | Du brauchst |
|---|---|---|
| 🔥 | **[Push bei Heizungsstörung](https://github.com/sahomm/BlueBattery/blob/main/docs/de/beispiele.md#heizungsstörung-melden)** – mit Fehlercode, auch wenn das Display ausfällt | BB-Display + [TIN-Adapter](https://www.blue-battery.com/product-page/tin-adapter) |
| ❄️ | **[Frostschutz](https://github.com/sahomm/BlueBattery/blob/main/docs/de/beispiele.md#frostschutz)** – Warnung und Heizung schaltet automatisch ein | BB-Display + TIN-Adapter |
| ♨️ | **[Vorheizen](https://github.com/sahomm/BlueBattery/blob/main/docs/de/beispiele.md#vorheizen)** – zu einer Uhrzeit oder per Knopf von unterwegs | BB-Display + TIN-Adapter |
| 🧊 | **[Kühlschrank & Gefrierfach](https://github.com/sahomm/BlueBattery/blob/main/docs/de/beispiele.md#kühlschrank-und-gefrierfach)** – Warnung, bevor etwas auftaut | BB-Display + Temperatursensor (Xiaomi, RuuviTag) |
| 🚰 | **[Tankwarnung](https://github.com/sahomm/BlueBattery/blob/main/docs/de/beispiele.md#tankwarnung)** – Grauwasser voll, Frischwasser knapp | BB-Display + [BlueLevel / BB-Tank](https://www.blue-battery.com/product-page/bluelevel) |
| 📐 | **[Wasserwaage](https://github.com/sahomm/BlueBattery/blob/main/docs/de/beispiele.md#wasserwaage)** – Libelle und cm-Angabe je Rad beim Einparken | BB-Display + BlueLevel / BB-Tank |
| 🔋 | **[Batteriewarnung](https://github.com/sahomm/BlueBattery/blob/main/docs/de/beispiele.md#batteriewarnung)** – Bord- und Starterbatterie im Blick | BB-Display + [Batteriecomputer](https://www.blue-battery.com/produkte) |
| ☀️ | **[Energie-Dashboard](https://github.com/sahomm/BlueBattery/blob/main/docs/de/beispiele.md#energie-dashboard)** – Solarertrag und Verbrauch über Wochen | BB-Display + Batteriecomputer |

Alle Beispiele: **[Praxisbeispiele](https://github.com/sahomm/BlueBattery/blob/main/docs/de/beispiele.md)**

## Was du brauchst

- ✅ ein **BB-Display** im WLAN deines Fahrzeugs, deine BlueBattery-Geräte darin gekoppelt
- ✅ **Home Assistant** (am einfachsten Home Assistant OS, z. B. auf einem Raspberry Pi im Fahrzeug)
- ✅ **HACS** – der Community-Store für Home Assistant ([so installierst du HACS](https://hacs.xyz/docs/use/))
- ✅ etwa **30 Minuten**

> **Internet:** Für die **Einrichtung** brauchst du Internet (Apps, HACS und Integration herunterladen). Im **Betrieb** läuft alles lokal im Netz deines Fahrzeugs – ohne Internet. Nur Fernzugriff von unterwegs und Push-Nachrichten brauchen eine Verbindung.

## Einrichtung in 7 Schritten

Ausführlich mit allen Details: **[Einrichtung Schritt für Schritt](https://github.com/sahomm/BlueBattery/blob/main/docs/de/einrichtung.md)**.

> **Tipp:** Hinter einigen Schritten steht ein Link **„Direkt öffnen ↗“**. Er öffnet die passende Seite in deinem Home Assistant über [my.home-assistant.io](https://my.home-assistant.io). Beim ersten Mal fragt die Seite einmalig nach der Adresse deines Home Assistant (z. B. `http://homeassistant.local:8123`) und danach jedes Mal kurz „Open link“ – das ist eine Sicherheitsabfrage. Der Weg über das Menü führt immer ans selbe Ziel.

**1. Geräte im BB-Display koppeln** – Batteriecomputer auswählen, Tanksensoren und Temperatursensoren koppeln und benennen, TIN-Adapter einrichten. Home Assistant sieht nur, was das Display kennt.

**2. Mosquitto-Broker installieren** – Einstellungen → Apps → App-Store → „Mosquitto broker“ suchen → Installieren → Starten, „Beim Booten starten“ und „Watchdog“ einschalten. Mosquitto ist eine offizielle App und im App-Store bereits enthalten. [Direkt öffnen ↗](https://my.home-assistant.io/redirect/supervisor_addon/?addon=core_mosquitto)

**3. Benutzer für das Display anlegen** – Einstellungen → Personen → Person hinzufügen → „Anmeldung erlauben“ → Benutzername und sicheres Passwort notieren → „Nur lokaler Zugriff“, kein Administrator → Erstellen. [Direkt öffnen ↗](https://my.home-assistant.io/redirect/people/)

**4. MQTT-Integration einrichten** – Einstellungen → Geräte & Dienste → unter „Entdeckt“ **MQTT** → Konfigurieren → bestätigen. [Direkt öffnen ↗](https://my.home-assistant.io/redirect/config_flow_start/?domain=mqtt)

**5. BB-Display mit Home Assistant verbinden** – in der Web-Oberfläche des Displays unter Fernzugriff → MQTT: Server = IP-Adresse deines Home Assistant, Port `1883`, Benutzer und Passwort aus Schritt 3, Topic unverändert lassen, Schalter **„Home Assistant“ aus**. Nach dem Speichern erscheint im Display das Symbol ⇄.

**6. BlueBattery über HACS installieren** – am einfachsten mit diesem Knopf: Er öffnet BlueBattery direkt in HACS und trägt das Repository nach einer Rückfrage selbst ein. Dann **Herunterladen** → Home Assistant neu starten.

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sahomm&repository=BlueBattery&category=integration)

*Von Hand:* HACS → ⋮ (oben rechts) → Benutzerdefinierte Repositories → `https://github.com/sahomm/BlueBattery`, Typ **Integration** → Hinzufügen. Dann **BlueBattery** suchen → Herunterladen → Home Assistant neu starten.

**7. BlueBattery einrichten** – Einstellungen → Geräte & Dienste → unter „Entdeckt“ **BlueBattery – BB-Display** → Konfigurieren → Geräte auswählen → Fertig. [Direkt öffnen ↗](https://my.home-assistant.io/redirect/config_flow_start/?domain=bluebattery)

**Geschafft!** Neue Geräte koppelst du später einfach im Display – Home Assistant meldet sie dann zum Hinzufügen.

## Unterstützte Geräte

Alle Geräte kommen **über das BB-Display**.

| Gerät | Anbindung am BB-Display | Status |
|---|---|---|
| BB-Display selbst (Innentemperatur, Luftfeuchte, Taupunkt) | – | ✅ |
| Batteriecomputer (BBX200/400 Pro, D1/D2, X200/X300, BBX400, Basic) | Bluetooth, im Display ausgewählt | ✅ |
| BlueLevel / BlueLevel+, BB-Tank | Bluetooth, im Display gekoppelt | ✅ |
| Temperatursensoren Xiaomi LYWSD03MMC, RuuviTag | Bluetooth, im Display gekoppelt | ✅ |
| Truma Combi (CP plus iNet ready) | TIN-Adapter | ✅ |
| Alde Compact 3020 HE / 3030 | TIN-Adapter | 🧪 experimentell |

## Mehr erfahren

- **[Praxisbeispiele](https://github.com/sahomm/BlueBattery/blob/main/docs/de/beispiele.md)** – Vorlagen zum Import
- **[Einrichtung Schritt für Schritt](https://github.com/sahomm/BlueBattery/blob/main/docs/de/einrichtung.md)** – ausführlich, mit allen Einstellungen
- **[Heizung steuern](https://github.com/sahomm/BlueBattery/blob/main/docs/de/heizung.md)** – Truma und Alde
- **[Fragen & Antworten](https://github.com/sahomm/BlueBattery/blob/main/docs/de/faq.md)** – auch zur Fehlersuche
- **[Umstieg von der eingebauten Anbindung](https://github.com/sahomm/BlueBattery/blob/main/docs/de/umstieg.md)** – Verlauf behalten
- **[Was ist BlueBattery?](https://www.blue-battery.com)** – Produkte und Forum des Herstellers

## Mitwirken

- Fehler und Wünsche: [GitHub Issues](https://github.com/sahomm/BlueBattery/issues) – am besten mit **Diagnose-Export** (Geräte & Dienste → BlueBattery → ⋮ → Diagnose herunterladen; Adressen sind geschwärzt).
- **Alde-Besitzer gesucht:** Wer eine Alde mit TIN-Adapter hat, hilft sehr mit einem Diagnose-Export.
- Technische Grundlage: [Architektur](https://github.com/sahomm/BlueBattery/blob/main/docs/ARCHITEKTUR.md)

Dieses Projekt wird von [sahomm](https://github.com/sahomm) in Abstimmung mit dem BlueBattery-Entwickler und mit Unterstützung von Claude (Anthropic) entwickelt.

## Rechtliche Hinweise

- **Community-Projekt:** Die Integration entsteht in Abstimmung mit dem BlueBattery-Entwickler, ist aber kein offizielles Produkt der BlueBattery. BlueBattery-Logo und Produktbilder © BlueBattery, verwendet mit freundlicher Genehmigung. Für Fragen zu den Geräten selbst: [blue-battery.com](https://www.blue-battery.com) und das [BlueBattery-Forum](https://www.blue-battery.com/groups).
- **Keine Verbindung zu Heizungs- und Geräteherstellern:** Dieses Projekt steht in **keinerlei Verbindung** zur Truma Gerätetechnik GmbH & Co. KG, zur Alde International Systems AB oder zu anderen hier genannten Herstellern (u. a. Xiaomi, Ruuvi). Es wird von ihnen weder unterstützt, geprüft noch empfohlen.
- **Markennamen nur zur Beschreibung:** Namen wie *Truma*, *Combi*, *CP plus*, *iNet*, *Alde*, *Xiaomi*, *RuuviTag*, *Home Assistant* oder *Raspberry Pi* sind Marken bzw. Produktbezeichnungen ihrer jeweiligen Inhaber. Sie werden ausschließlich verwendet, um zu beschreiben, **mit welchen Geräten** die Integration zusammenarbeitet. Es werden **keine Logos** dieser Hersteller verwendet.
- **Steuerung der Heizung:** Die Heizung wird über das BB-Display und den TIN-Adapter von BlueBattery angesprochen, nicht über Schnittstellen oder Software der Heizungshersteller. Nutzung auf eigene Verantwortung. Für Fragen zu Garantie, Gewährleistung und Betrieb der Heizung ist ausschließlich deren Hersteller bzw. Händler zuständig; Störungen der Heizung bitte zuerst am Bedienteil der Heizung prüfen.
- **Haftung:** Die Software wird ohne Gewähr bereitgestellt (siehe [Lizenz](#lizenz)). Sie ersetzt keine Überwachung vor Ort – insbesondere nicht beim Frostschutz.

## Lizenz

[MIT](https://github.com/sahomm/BlueBattery/blob/main/LICENSE)
