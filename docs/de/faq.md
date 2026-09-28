# Fragen & Antworten

🇩🇪 Deutsch | [🇬🇧 English](../en/faq.md) · [← zurück zur Übersicht](../../README.md)

**Allgemein**
- [Brauche ich Internet?](#brauche-ich-internet)
- [Brauche ich ein BB-Display?](#brauche-ich-ein-bb-display)
- [Welche Daten kommen in Home Assistant an?](#welche-daten-kommen-in-home-assistant-an)
- [Warum sehe ich nur einen Batteriecomputer?](#warum-sehe-ich-nur-einen-batteriecomputer)
- [Wie genau ist die Landstrom-Energie?](#wie-genau-ist-die-landstrom-energie)
- [Was passiert nach einem Neustart?](#was-passiert-nach-einem-neustart)

**Fehlersuche**
- [Oben im Display fehlt das Symbol ⇄](#oben-im-display-fehlt-das-symbol-)
- [BlueBattery erscheint nicht unter „Entdeckt“](#bluebattery-erscheint-nicht-unter-entdeckt)
- [Ein Gerät fehlt in der Auswahl](#ein-gerät-fehlt-in-der-auswahl)
- [Alle Werte stehen auf „nicht verfügbar“](#alle-werte-stehen-auf-nicht-verfügbar)
- [Ich sehe alle Werte doppelt](#ich-sehe-alle-werte-doppelt)
- [Nach dem Ausschalten der eingebauten Anbindung bleiben alte Geräte stehen](#nach-dem-ausschalten-der-eingebauten-anbindung-bleiben-alte-geräte-stehen)
- [HACS meldet „Failed to download … 404“](#hacs-meldet-failed-to-download--404)
- [Die Knöpfe „My Home Assistant“ funktionieren nicht](#die-knöpfe-my-home-assistant-funktionieren-nicht)
- [Wie melde ich einen Fehler?](#wie-melde-ich-einen-fehler)

**Für Fortgeschrittene**
- [Home Assistant Container oder Core](#home-assistant-container-oder-core)
- [MQTT-Nachrichten mitlesen](#mqtt-nachrichten-mitlesen)
- [Wie kommen die Daten zu Home Assistant?](#wie-kommen-die-daten-zu-home-assistant)

---

## Allgemein

### Brauche ich Internet?

Für die **Einrichtung** ja – Home Assistant lädt die Mosquitto-App, HACS und diese Integration aus dem Internet. Im **Betrieb** läuft alles lokal im Netz deines Fahrzeugs, ganz ohne Internet. Eine Verbindung brauchst du nur für den Fernzugriff von unterwegs und für Push-Nachrichten aufs Handy.

### Brauche ich ein BB-Display?

Ja. Die Integration bindet BlueBattery-Geräte über das BB-Display ein – es sammelt die Daten aller gekoppelten Geräte und schickt sie an Home Assistant. Ohne BB-Display funktioniert die Integration (noch) nicht.

### Welche Daten kommen in Home Assistant an?

Alles, was das BB-Display von den gekoppelten Geräten weiterreicht:

- **Batteriecomputer:** Ladezustand, Spannung, Strom, Leistung, Solar, Booster, Starterbatterie, Ladephasen, Energiezähler
- **Tanks:** Füllstand in % und Litern, Kapazität, Tankart, Neigung (längs und seitlich)
- **Temperatursensoren:** Temperatur, Luftfeuchte, Batterie
- **BB-Display selbst:** Innentemperatur, Luftfeuchte, Taupunkt, Verbindung
- **Heizung:** siehe [Heizung steuern](heizung.md)

### Warum sehe ich nur einen Batteriecomputer?

Das BB-Display reicht genau **einen** Batteriecomputer weiter – den, der im Display ausgewählt ist.

### Wie genau ist die Landstrom-Energie?

Das Display berechnet sie aus Batterie-, Solar- und Boosterstrom – ein guter Richtwert, auch ohne eigenen Landstromzähler. Alle Energiezähler beginnen jeden Tag neu; Home Assistant führt sie im [Energie-Dashboard](beispiele.md#energie-dashboard) fortlaufend weiter.

### Was passiert nach einem Neustart?

- **Home Assistant neu gestartet:** Die zuletzt bekannten Werte stehen sofort bereit. Als *verbunden* gilt das Display, sobald es wieder frische Daten sendet.
- **Display neu gestartet:** Die Heizung bekommt 1–2 Minuten Zeit, sich wieder zu verbinden, bevor eine Störung gemeldet wird.
- **Temperatursensor ausgefallen:** Meldet das Display keinen gültigen Wert mehr, zeigt die Integration „unbekannt“ statt eines veralteten Werts.

---

## Fehlersuche

### Oben im Display fehlt das Symbol ⇄

Das Display ist nicht mit dem Broker verbunden. Prüfe in der Web-Oberfläche des Displays unter Fernzugriff → MQTT:
- **Server** = IP-Adresse deines Home Assistant, **Port** `1883`,
- **Benutzer und Passwort** wie in [Schritt 3](einrichtung.md#schritt-3--benutzer-für-das-display-anlegen) angelegt,
- läuft die **Mosquitto-App** (Einstellungen → Apps → Mosquitto broker)?

Wurde der Benutzer gerade erst angelegt und die Anmeldung scheitert, die **Mosquitto-App einmal neu starten**.

### BlueBattery erscheint nicht unter „Entdeckt“

- Zeigt das Display das Symbol ⇄? Wenn nicht: siehe oben.
- Ist die Integration über HACS installiert und Home Assistant danach **neu gestartet**?
- Einrichtung von Hand: Einstellungen → Geräte & Dienste → **Integration hinzufügen** → „BlueBattery“ → das Topic aus dem Display eingeben (Werkseinstellung `BlueBattery/BB-Display`).

### Ein Gerät fehlt in der Auswahl

Die Integration zeigt nur Geräte, die **im BB-Display gekoppelt** sind und von dort gerade gemeldet werden. Gerät im Display koppeln (bzw. als Batteriecomputer auswählen), Reichweite prüfen, dann in Home Assistant **Konfigurieren** erneut öffnen.

### Alle Werte stehen auf „nicht verfügbar“

Das Display sendet gerade keine Daten – z. B. weil es ausgeschaltet oder außer WLAN-Reichweite ist. Sobald es wieder sendet, erscheinen die Werte von selbst. Die Integration zeigt bewusst „nicht verfügbar“ statt alter Werte, damit du dich auf die Anzeige verlassen kannst.

### Ich sehe alle Werte doppelt

Die eingebaute Home-Assistant-Anbindung des Displays ist noch eingeschaltet. Schalte im Display unter MQTT den Schalter **„Home Assistant“** aus – siehe [Umstieg](umstieg.md).

### Nach dem Ausschalten der eingebauten Anbindung bleiben alte Geräte stehen

Manche Geräte (beobachtet bei BB-Tank und BlueLevel) räumen ihre alten Einträge im Broker nicht selbst auf. Abhilfe: mit dem [MQTT Explorer](https://mqtt-explorer.com) unter `homeassistant/…` die Einträge des Geräts löschen – danach verschwinden die Geräte aus Home Assistant.

### HACS meldet „Failed to download … 404“

Beim Herunterladen wurde statt einer Version eine Kennung wie `21ff56e` gewählt. **HACS → BlueBattery → ⋮ → Erneut herunterladen** und die neueste Version `v…` auswählen.

### Die Knöpfe „My Home Assistant“ funktionieren nicht

Siehe [Wenn die Knöpfe nicht funktionieren](einrichtung.md#wenn-die-knöpfe-nicht-funktionieren). Unter jedem Knopf steht außerdem der Weg von Hand.

### Wie melde ich einen Fehler?

**Einstellungen → Geräte & Dienste → BlueBattery → ⋮ → Diagnose herunterladen** (Adressen sind geschwärzt) und die Datei an ein [Issue auf GitHub](https://github.com/sahomm/BlueBattery/issues) anhängen.

---

## Für Fortgeschrittene

### Home Assistant Container oder Core

Dort gibt es keine Apps. Du brauchst einen eigenen MQTT-Broker (z. B. Mosquitto als Docker-Container) und richtest die MQTT-Integration mit dessen Adresse ein. Benutzer und Passwort legst du im Broker an.

### MQTT-Nachrichten mitlesen

In der MQTT-Integration: **Konfigurieren → Auf ein Topic hören** → `BlueBattery/#` → Zuhören. Alle 30 Sekunden (je nach Einstellung im Display) sollte eine Nachricht kommen. Übersichtlicher geht es mit dem [MQTT Explorer](https://mqtt-explorer.com).

### Wie kommen die Daten zu Home Assistant?

```
Batteriecomputer ──┐
BlueLevel/BB-Tank ─┼─ Bluetooth ──► BB-Display ◄── WLAN / MQTT ──► Home Assistant
Xiaomi/RuuviTag ───┘                    ▲                          (Mosquitto + BlueBattery)
                                        │ Kabel
                  Truma/Alde ── TIN-Adapter
```

Die Geräte funken per Bluetooth zum BB-Display bzw. sind über den TIN-Adapter angeschlossen. Das Display schickt alles gebündelt per WLAN/MQTT an Home Assistant und nimmt von dort Heizungsbefehle entgegen. Bei Tanks kommen Füllstand, Inhalt, Neigung und Signal; Diagnosewerte der Tanksensoren selbst (z. B. Abstand zur Wasseroberfläche) reicht das Display nicht weiter.

Technische Details: [Architektur](../ARCHITEKTUR.md)
