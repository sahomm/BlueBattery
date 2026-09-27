# BlueBattery für Home Assistant

🇩🇪 Deutsch | [🇬🇧 English](README.en.md)

<p align="center">
  <img src="custom_components/bluebattery/brand/icon.png" alt="BlueBattery" width="96">
  &nbsp;&nbsp;
  <img src="images/produkt-bb-display.png" alt="BB-Display mit WLAN und MQTT" width="260">
</p>

Home-Assistant-Integration für die Geräte von **[BlueBattery](https://www.blue-battery.com)** – Batterie- und Solarcomputer, BB-Display, Tanksensoren und Heizungssteuerung (Truma/Alde über den TIN-Adapter) für Wohnmobile und Wohnwagen.

Die Integration findet dein **BB-Display** im MQTT-Broker **automatisch** und übernimmt alle Geräte, die im Display gekoppelt sind – du wählst aus, welche, und kannst später neue Geräte hinzufügen, ohne dass bestehende Entitäten oder deren Verlauf verloren gehen.

> **Voraussetzung: ein BB-Display.** Die Integration bindet BlueBattery-Geräte ausschließlich **über das BB-Display** ein. Übernommen werden alle Geräte, die im Display gekoppelt sind – Batteriecomputer, BlueLevel/BB-Tank, Temperatursensoren und Truma/Alde über den TIN-Adapter. **Ohne BB-Display funktioniert die Integration (noch) nicht.**

Dieses Projekt wird von [sahomm](https://github.com/sahomm) in Abstimmung mit dem BlueBattery-Entwickler und mit Unterstützung von Claude (Anthropic) entwickelt.

> **Hinweis:** Privates Community-Projekt, kein offizielles Produkt der BlueBattery und **ohne Verbindung zu Truma, Alde oder anderen genannten Herstellern** – siehe [Rechtliche Hinweise](#rechtliche-hinweise). Für Fragen zu den Geräten selbst: [blue-battery.com](https://www.blue-battery.com) und das [BlueBattery-Forum](https://www.blue-battery.com/groups).

## Inhalt

- [Was ist BlueBattery?](#was-ist-bluebattery)
- [Was kann die Integration?](#was-kann-die-integration)
- [Unterstützte Geräte](#unterstützte-geräte)
- [Wie kommen die Daten zu Home Assistant?](#wie-kommen-die-daten-zu-home-assistant)
- [Voraussetzungen](#voraussetzungen)
- [Einrichtung Schritt für Schritt](#einrichtung-schritt-für-schritt)
- [Geräte später hinzufügen](#geräte-später-hinzufügen)
- [Umstieg von der bisherigen Home-Assistant-Anbindung im Display](#umstieg-von-der-bisherigen-home-assistant-anbindung-im-display)
- [Heizung steuern](#heizung-steuern)
- [Gut zu wissen](#gut-zu-wissen)
- [Fehlersuche](#fehlersuche)
- [Mitwirken](#mitwirken)
- [Rechtliche Hinweise](#rechtliche-hinweise)
- [Lizenz](#lizenz)

## Was ist BlueBattery?

[BlueBattery](https://www.blue-battery.com) (Kai Scheffer, Zürich) entwickelt Energie- und Komfortelektronik für Reisemobile:

- **Batterie- und Solarcomputer** (z. B. BBX200 Pro, BBX400 Pro, D2, Basic) messen über einen Shunt Strom, Spannung, Ladezustand (SOC), Solar-, Booster- und Landstrom der Aufbaubatterie.
- Das **[BB-Display](https://www.blue-battery.com/product-page/bb-display)** ist der zentrale Knoten: Es empfängt per Bluetooth die Daten des Batteriecomputers, von Tanksensoren (BlueLevel/BB-Tank) und Temperatursensoren (Xiaomi, RuuviTag), misst selbst Innentemperatur und Luftfeuchte und stellt alles per **WLAN und MQTT** bereit.
- Mit dem **[TIN-Adapter](https://www.blue-battery.com/product-page/tin-adapter)** liest und steuert das BB-Display **Truma**-Heizungen (Combi mit CP plus iNet ready) und **Alde**-Heizungen (Compact 3020 HE / 3030).
- **[BlueLevel](https://www.blue-battery.com/product-page/bluelevel)** / BB-Tank messen Tankfüllstände berührungslos und zeigen die Neigung des Fahrzeugs.

| [BB-Display](https://www.blue-battery.com/product-page/bb-display) | [TIN-Adapter](https://www.blue-battery.com/product-page/tin-adapter) | [BlueLevel+](https://www.blue-battery.com/product-page/bluelevel) | [BBX400 Pro](https://www.blue-battery.com/product-page/bbx400-pro) |
|:---:|:---:|:---:|:---:|
| <img src="images/produkt-bb-display.png" alt="BB-Display" width="170"> | <img src="images/produkt-tin-adapter.png" alt="TIN-Adapter" width="170"> | <img src="images/produkt-bluelevel.png" alt="BlueLevel+" width="170"> | <img src="images/produkt-bbx400-pro.png" alt="BBX400 Pro" width="170"> |
| zentraler Knoten, WLAN + MQTT | Truma/Alde am BB-Display | Tankfüllstand + Neigung | Batterie- und Solarcomputer |

**So hängt alles zusammen:** Batteriecomputer, Tanksensoren und Temperatursensoren funken per Bluetooth zum BB-Display; die Heizung ist über den TIN-Adapter angeschlossen. Das BB-Display schickt alles per WLAN an den MQTT-Broker in Home Assistant – und nimmt von dort Heizungsbefehle entgegen.

```
Batteriecomputer ──┐
BlueLevel/BB-Tank ─┼─ Bluetooth ──► BB-Display ◄── WLAN / MQTT ──► Home Assistant
Xiaomi/RuuviTag ───┘                    ▲                          (Mosquitto + BlueBattery)
                                        │ Kabel
                  Truma/Alde ── TIN-Adapter
```

## Was kann die Integration?

- **Automatische Erkennung** des BB-Displays im MQTT-Broker – unabhängig davon, welches MQTT-Topic im Display eingestellt ist (Fallback: manuelle Eingabe).
- **Geräteauswahl** bei der Einrichtung: alle im Display gekoppelten Geräte – Batteriecomputer, Heizung, jeder Tank, jeder Temperatursensor einzeln.
- **Neue Geräte:** Sobald ein Gerät im Display neu gekoppelt ist, meldet Home Assistant es; per Neukonfiguration wird es hinzugefügt – bestehende Entitäten und ihr Verlauf bleiben unverändert.
- **Batterie & Energie:** Ladezustand, Spannung, Strom, Solar, Booster, Starterbatterie, Energiezähler (geeignet für das Energie-Dashboard).
- **Tanks:** Füllstand in % und Litern, Tankart, Neigung.
- **Klima:** Innentemperatur, Luftfeuchte, Taupunkt des Displays; externe Temperatur-/Feuchtesensoren (z. B. Kühlschrank, Gefrierfach).
- **Heizung:** Thermostat mit eco/high, Raum-Soll, Boiler, Fehlercode, Online-Status – als Grundlage für **Frostschutz- und Ausfall-Benachrichtigungen**.
- **Ehrliche Verfügbarkeit:** Werte gelten nur als aktuell, wenn das Gerät wirklich sendet – nicht nur, weil eine alte Nachricht im Broker liegt.
- **Diagnose-Export** mit geschwärzten Adressen für Fehlermeldungen.

## Unterstützte Geräte

Alle Geräte kommen **über das BB-Display** – sie müssen dort gekoppelt bzw. angeschlossen sein.

| Gerät | Anbindung am BB-Display | Status |
|---|---|---|
| BB-Display selbst (Innentemperatur, Luftfeuchte, Taupunkt, Diagnose) | – | ✅ unterstützt |
| Batteriecomputer (BBX200/400 Pro, D1/D2, X200/X300, BBX400, Basic) | Bluetooth, im Display ausgewählt | ✅ unterstützt |
| BlueLevel / BlueLevel+, BB-Tank (Kanäle) | Bluetooth, im Display gekoppelt | ✅ unterstützt |
| Xiaomi LYWSD03MMC, RuuviTag | Bluetooth, im Display gekoppelt | ✅ unterstützt |
| Truma Combi (CP plus iNet ready) | TIN-Adapter | ✅ unterstützt |
| Alde Compact 3020 HE / 3030 | TIN-Adapter | 🧪 experimentell |

## Wie kommen die Daten zu Home Assistant?

Die Geräte funken per Bluetooth zum BB-Display bzw. sind über den TIN-Adapter angeschlossen. Das Display schickt alles gebündelt per WLAN/MQTT an Home Assistant und nimmt von dort Heizungsbefehle entgegen.

**Das BB-Display ist die Spinne im Netz – mit Grenzen:**
- Es reicht **genau einen** Batteriecomputer weiter – den, der im Display ausgewählt ist. Ein **zweiter** Batteriecomputer (z. B. ein BBX400 Pro für eine zweite Batteriebank) erscheint nicht.
- Es reicht nur die **im Display gekoppelten** Tanks und Sensoren weiter.
- Bei Tanks kommen Füllstand, Inhalt, Neigung und Signal – **Diagnosewerte** der Tanksensoren (z. B. Abstand zur Wasseroberfläche, Speicher) nicht.

**Doppelte Werte vermeiden:** Viele BlueBattery-Geräte haben eine **eingebaute Home-Assistant-Anbindung** (Schalter „Home Assistant“ bzw. „MQTT Discovery“). Schalte sie beim BB-Display immer aus, bei BB-Tank/BlueLevel ebenfalls, wenn sie am Display gekoppelt sind. Bei Geräten, die nicht über das Display kommen – z. B. einem zweiten Batteriecomputer – **lass sie an**.

## Voraussetzungen

Bevor du die Integration einrichtest, muss Folgendes vorhanden sein:

1. **Home Assistant** – am einfachsten Home Assistant OS (z. B. auf einem Raspberry Pi im Fahrzeug). Bei Home Assistant Container/Core brauchst du einen eigenen MQTT-Broker.
2. **Ein gemeinsames Netzwerk:** BB-Display und Home Assistant müssen sich erreichen können – typischerweise dasselbe WLAN im Fahrzeug (Router im Wohnmobil). Das BB-Display nutzt **2,4-GHz-WLAN**.
3. **Ein MQTT-Broker** – empfohlen die App **Mosquitto broker** in Home Assistant (Anleitung unten).
4. **Die MQTT-Integration** in Home Assistant, verbunden mit diesem Broker.
5. **HACS** zur Installation dieser Integration ([hacs.xyz](https://hacs.xyz)).
6. **BB-Display** (Pflicht) mit aktueller Firmware und im WLAN angemeldet (Anleitung: [BB-Display-Produktseite](https://www.blue-battery.com/product-page/bb-display), Firmware: [GitHub BlueBattery](https://github.com/blue-battery-ch/BB-Display/releases)).
7. **Deine BlueBattery-Geräte im BB-Display gekoppelt** – siehe [Schritt 1](#schritt-1--geräte-im-bb-display-koppeln).
8. Für die Heizung: **TIN-Adapter** am BB-Display und an der Truma bzw. Alde angeschlossen und im Display eingerichtet.

## Einrichtung Schritt für Schritt

### Schritt 1 – Geräte im BB-Display koppeln

Home Assistant sieht nur, was das BB-Display kennt. Richte deshalb zuerst im Display (Bedienung am Gerät bzw. in der Web-Oberfläche) alles ein, was du in Home Assistant haben möchtest:

- **Batteriecomputer** auswählen (das Display reicht genau einen weiter),
- **Tanksensoren** (BlueLevel/BlueLevel+, BB-Tank) koppeln und benennen,
- **Temperatursensoren** (Xiaomi LYWSD03MMC, RuuviTag) koppeln und benennen,
- **TIN-Adapter** anschließen und die Heizung einrichten.

Die Namen aus dem Display (z. B. „Frischwasser“, „Kühlschrank“) übernimmt die Integration. Anleitung: [BB-Display-Produktseite](https://www.blue-battery.com/product-page/bb-display).

### Schritt 2 – Mosquitto-Broker installieren

1. Home Assistant → **Einstellungen → Apps → App-Store** → **Mosquitto broker** → **Installieren**.
2. Nach der Installation **Starten** und **Beim Booten starten** sowie **Watchdog** aktivieren.

<!-- 📷 TODO: images/01-mosquitto-app.png – Mosquitto im App-Store / Info-Seite -->
> 📷 *Bild folgt: Mosquitto-App installieren*

### Schritt 3 – MQTT-Benutzer anlegen

Das BB-Display meldet sich mit einem eigenen Benutzer am Broker an.

1. **Einstellungen → Personen → Benutzer** (ggf. „Erweiterter Modus“ im Profil aktivieren) → **Benutzer hinzufügen**.
2. Name z. B. `mqtt_user`, ein **sicheres Passwort** vergeben, „Kann sich nur aus dem lokalen Netzwerk anmelden“ aktivieren, kein Administrator.

<!-- 📷 TODO: images/02-mqtt-user.png -->
> 📷 *Bild folgt: Benutzer für MQTT anlegen*

### Schritt 4 – MQTT-Integration einrichten

1. **Einstellungen → Geräte & Dienste** – meist erscheint **MQTT** bereits unter „Entdeckt“ → **Konfigurieren** → bestätigen.
2. Falls nicht: **Integration hinzufügen → MQTT** und den Mosquitto-Broker auswählen.

<!-- 📷 TODO: images/03-mqtt-integration.png -->
> 📷 *Bild folgt: MQTT-Integration*

### Schritt 5 – BB-Display mit dem Broker verbinden

Web-Oberfläche des Displays im Browser öffnen (IP-Adresse z. B. aus der Geräteliste des Routers) → **Einstellungen → Fernzugriff → MQTT**:

| Feld | Eintrag |
|---|---|
| Server | IP-Adresse deines Home Assistant (z. B. `192.168.1.10`) |
| Client ID | frei, z. B. `BBDisplay` |
| Port | `1883` |
| Benutzer / Passwort | aus Schritt 3 |
| Topic | **`BlueBattery/BB-Display`** (Werkseinstellung, empfohlen) |
| Daten senden alle | `30` Sekunden |
| Home Assistant | **aus** – die Anbindung übernimmt diese Integration (siehe [Umstieg](#umstieg-von-der-bisherigen-home-assistant-anbindung-im-display)) |

Nach dem Speichern startet das Display neu. Oben in der Anzeige erscheint das Verbindungssymbol ⇄.

<!-- 📷 TODO: images/04-bb-display-mqtt.png – Fernzugriff/MQTT-Seite (Passwort verdeckt) -->
> 📷 *Bild folgt: MQTT-Einstellungen im BB-Display*

> **Topic frei wählbar:** Die Integration erkennt BlueBattery-Geräte auch unter anderen Topics (bis zu drei Ebenen, z. B. `camper/bb/display`). Empfohlen ist trotzdem die Werkseinstellung.

### Schritt 6 – Integration über HACS installieren

1. **HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories** → `https://github.com/sahomm/BlueBattery`, Kategorie **Integration**.
2. **BlueBattery** suchen → **Herunterladen** – als Version die **neueste Version** (`v…`) auswählen, nicht eine Kennung wie `21ff56e`.
3. Home Assistant **neu starten**.

### Schritt 7 – BlueBattery einrichten

1. **Einstellungen → Geräte & Dienste**: Unter „Entdeckt“ erscheint **BlueBattery – BB-Display** → **Konfigurieren**.
   *Nicht gefunden?* → **Integration hinzufügen → BlueBattery → Manuell** und das Topic aus Schritt 5 eingeben.
2. Die Integration zeigt alle Geräte, die im Display gekoppelt sind – **auswählen**, was übernommen werden soll:

   | ☑ | Gerät |
   |---|---|
   | ☑ | Batteriecomputer A1B2C3 |
   | ☑ | Truma (TIN-Adapter) |
   | ☑ | Tank „Frischwasser“ (BB-Tank, Kanal 1) |
   | ☐ | Temperatursensor „Kühlschrank“ |

3. **Fertig** – je Gerät entstehen Entitäten, das BB-Display ist das übergeordnete Gerät.

<!-- 📷 TODO: images/06-config-flow-auswahl.png -->

## Geräte später hinzufügen

Kommt ein Gerät dazu (neuer Tank, weiterer Temperatursensor, TIN-Adapter):

1. Gerät **im BB-Display koppeln** (siehe [Schritt 1](#schritt-1--geräte-im-bb-display-koppeln)).
2. Kurz warten – Home Assistant meldet unter **Einstellungen → Reparaturen**: *„Neues BlueBattery-Gerät gefunden“*.
3. **Geräte & Dienste → BlueBattery → Konfigurieren** → neues Gerät anhaken → speichern.

- Bereits vorhandene Entitäten bleiben unverändert – **Verlauf und Statistiken bleiben erhalten**.
- Ein abgewähltes Gerät wird standardmäßig nur **deaktiviert** (Verlauf bleibt); auf Wunsch kann es entfernt werden.
- Ist ein Gerät vorübergehend nicht erreichbar (z. B. Tank außer Reichweite), wird es **nicht verfügbar** angezeigt, aber nicht entfernt.

## Umstieg von der bisherigen Home-Assistant-Anbindung im Display

Das BB-Display bringt eine eigene Anbindung mit (Schalter **„Home Assistant“** in den MQTT-Einstellungen). Diese Integration ersetzt sie. **Beides gleichzeitig führt zu doppelten Entitäten.**

**Neu einsteigen (empfohlen, wenn der bisherige Verlauf keine Rolle spielt):** Schalter „Home Assistant“ im Display ausschalten – die alten Entitäten verschwinden – und diese Integration einrichten.

**Verlauf behalten:** Die Integration kann die bisherigen Entitäts-IDs übernehmen, damit Dashboards, Automationen und Verlauf weiterlaufen:
1. Integration einrichten (die Entitäten erscheinen vorübergehend doppelt).
2. **Geräte & Dienste → BlueBattery → Konfigurieren → Umstieg: vorbereiten** – die Liste prüfen und speichern.
3. Im Display unter MQTT **„Home Assistant“ ausschalten**, eine Minute warten.
4. **Konfigurieren → Umstieg: abschließen.**

Entitäten, die es in der Integration als andere Art gibt (z. B. „Booster-Limit“ jetzt als Sensor statt Binärsensor), werden nicht übernommen.

## Heizung steuern

<p align="center">
  <img src="images/produkt-bb-display-heizung-wohnmobil.jpg" alt="Heizungssteuerung über BB-Display mit TIN-Adapter" width="560">
</p>

**Truma** (Combi mit CP plus iNet ready, über TIN-Adapter)
- Thermostat: aus / heizen, Stufe **eco** oder **high**, Raum-Soll 5–30 °C
- Boiler: Aus / Eco (40 °C) / High (55 °C) / Boost (60 °C)
- Anzeige: Raum- und Wassertemperatur, Lüfterstufe, Fehlercode/-text, Verbindung
- Energieart (Gas / Mix / Elektro) nur bei **Combi E** – in den Optionen aktivierbar

**Alde** (Compact 3020 HE / 3030) – 🧪 *experimentell*
- Thermostat Zone 1 (und Zone 2, falls vorhanden), Warmwasser, Gas, Elektrostufe 1–3 kW, Priorität, Außentemperatur

**Wichtig zu wissen**
- Die Heizung reagiert **nicht sofort**: Änderungen erscheinen je nach Heizung erst nach einigen Sekunden bis ca. 30 Sekunden. Bitte nicht mehrfach tippen – die Integration zeigt an, dass ein Befehl unterwegs ist.
- Das BB-Display meldet nicht zurück, ob ein Befehl angenommen wurde. Die Integration prüft das am nachfolgenden Status.
- **Truma-Boiler-Boost** schaltet die Raumheizung vorübergehend ab; die Integration zeigt das als *„Raumheizung pausiert“*.
- **Störung** (z. B. E212H bei fehlendem Gas): Die Integration meldet sie sofort mit Fehlercode und -text (Störungsmelder), die Heizung bleibt als *verbunden* angezeigt. Eine Störung lässt sich **nicht aus der Ferne zurücksetzen** – das ist von der Heizung so vorgesehen; zurücksetzen am Bedienteil (z. B. CP plus). Bis dahin nimmt die Heizung keine Befehle an.

## Gut zu wissen

- **Energiezähler** (`… Wh`) werden im Display berechnet und täglich zurückgesetzt. **Landstrom-Energie ist ein Schätzwert** (Batteriestrom minus Solar- und Boosterstrom), keine Messung.
- **Temperatursensoren** über das Display liefern keinen Zeitstempel; fällt ein Sensor aus, zeigt die Integration „unbekannt“, sobald das Display keinen gültigen Wert mehr meldet.
- Nach einem **Neustart von Home Assistant** werden die zuletzt bekannten Werte angezeigt; als *verbunden* gilt das Display erst, wenn es wieder aktiv sendet.
- Nach einem **Neustart des Displays** braucht die Heizungsverbindung 1–2 Minuten; in dieser Zeit wird kein Heizungsfehler gemeldet.

## Fehlersuche

- **Keine Geräte gefunden:** Sendet das Display? In der MQTT-Integration unter **Konfigurieren → Auf ein Topic hören** `BlueBattery/#` abonnieren – es sollten alle 30 s Nachrichten kommen. Alternativ [MQTT Explorer](https://mqtt-explorer.com).
- **Gerät fehlt in der Auswahl:** Die Integration zeigt nur Geräte, die im BB-Display gekoppelt sind und von dort gerade gemeldet werden. Gerät im Display koppeln (bzw. beim Batteriecomputer auswählen), Reichweite prüfen, dann **Konfigurieren** erneut öffnen.
- **Symbol ⇄ fehlt im Display:** Server-IP, Port, Benutzer/Passwort prüfen; läuft die Mosquitto-App?
- **HACS: „Failed to download … refs/heads/<Kennung>.zip“ (404):** Beim Herunterladen wurde statt einer Version eine Commit-Kennung gewählt. **HACS → BlueBattery → ⋮ → Erneut herunterladen** und die neueste Version `v…` auswählen.
- **Alte BlueBattery-Geräte bleiben nach dem Abschalten der eingebauten Anbindung stehen:** Manche Geräte (beobachtet bei BB-Tank und BlueLevel) löschen ihre Discovery-Einträge im Broker nicht. Abhilfe: im [MQTT Explorer](https://mqtt-explorer.com) unter `homeassistant/…` die Einträge des Geräts löschen – danach verschwinden die Geräte in Home Assistant.
- **Doppelte Entitäten:** Schalter „Home Assistant“ im Display ist noch aktiv (siehe [Umstieg](#umstieg-von-der-bisherigen-home-assistant-anbindung-im-display)).
- **Fehler melden:** **Geräte & Dienste → BlueBattery → ⋮ → Diagnose herunterladen** (Adressen sind geschwärzt) und als [Issue](https://github.com/sahomm/BlueBattery/issues) anhängen.

## Mitwirken

- Fehler und Wünsche: [GitHub Issues](https://github.com/sahomm/BlueBattery/issues)
- **Alde-Besitzer gesucht:** Wer eine Alde mit TIN-Adapter hat, hilft sehr mit einem Diagnose-Export.
- Technische Grundlage: [Architektur](docs/ARCHITEKTUR.md)

## Rechtliche Hinweise

- **Keine Verbindung zu Heizungs- und Geräteherstellern:** Dieses Projekt steht in **keinerlei Verbindung** zur Truma Gerätetechnik GmbH & Co. KG, zur Alde International Systems AB oder zu anderen hier genannten Herstellern (u. a. Xiaomi, Ruuvi). Es wird von ihnen weder unterstützt, geprüft noch empfohlen.
- **Markennamen nur zur Beschreibung:** Namen wie *Truma*, *Combi*, *CP plus*, *iNet*, *Alde*, *Xiaomi*, *RuuviTag*, *Home Assistant* oder *Raspberry Pi* sind Marken bzw. Produktbezeichnungen ihrer jeweiligen Inhaber. Sie werden ausschließlich verwendet, um zu beschreiben, **mit welchen Geräten** die Integration zusammenarbeitet. Es werden **keine Logos** dieser Hersteller verwendet.
- **Verhältnis zu BlueBattery:** Die Integration entsteht in Abstimmung mit dem BlueBattery-Entwickler, ist aber ein Community-Projekt und kein offizielles Produkt der BlueBattery. BlueBattery-Logo und Produktbilder © BlueBattery, verwendet mit freundlicher Genehmigung.
- **Steuerung der Heizung:** Die Heizung wird über das BB-Display und den TIN-Adapter von BlueBattery angesprochen, nicht über Schnittstellen oder Software der Heizungshersteller. Nutzung auf eigene Verantwortung. Für Fragen zu Garantie, Gewährleistung und Betrieb der Heizung ist ausschließlich deren Hersteller bzw. Händler zuständig; Störungen der Heizung bitte zuerst am Bedienteil der Heizung prüfen.
- **Haftung:** Die Software wird ohne Gewähr bereitgestellt (siehe [Lizenz](#lizenz)). Sie ersetzt keine Überwachung vor Ort – insbesondere nicht beim Frostschutz.

## Lizenz

[MIT](LICENSE)
