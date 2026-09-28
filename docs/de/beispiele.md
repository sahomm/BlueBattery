# Praxisbeispiele

🇩🇪 Deutsch | [🇬🇧 English](../en/examples.md) · [← zurück zur Übersicht](../../README.md)

Die BlueBattery-App zeigt dir, was in deinem Fahrzeug los ist. Mit Home Assistant **handelt dein Fahrzeug selbst**: Es meldet sich, wenn etwas nicht stimmt, heizt vor, wenn du kommst, und schützt vor Frost – auch wenn niemand an Bord ist.

Für die meisten Beispiele gibt es eine **fertige Vorlage**. Du musst nichts programmieren: Vorlage mit einem Klick übernehmen, deine Geräte auswählen, fertig. Alle Vorlagen sind im Wohnmobil des Autors eingerichtet.

**Inhalt**
- [So nutzt du eine Vorlage](#so-nutzt-du-eine-vorlage) – einmal lesen, gilt für alle
- [Nachrichten aufs Handy](#nachrichten-aufs-handy) – einmalig vorab
- [Heizungsstörung melden](#heizungsstörung-melden)
- [Frostschutz](#frostschutz)
- [Vorheizen](#vorheizen)
- [Kühlschrank und Gefrierfach](#kühlschrank-und-gefrierfach)
- [Tankwarnung](#tankwarnung)
- [Batteriewarnung](#batteriewarnung)
- [Wasserwaage](#wasserwaage)
- [Energie-Dashboard](#energie-dashboard)
- [Alles auf einer Seite](#alles-auf-einer-seite)

---

## So nutzt du eine Vorlage

Bei jedem Beispiel steht ein blauer Knopf **„Vorlage importieren“**.

1. Auf den Knopf klicken. Beim ersten Mal fragt die Seite nach der Adresse deines Home Assistant (z. B. `http://homeassistant.local:8123`) → eintragen → **Save**.
2. **Open link** klicken. Home Assistant zeigt die Vorlage → **Blueprint importieren**.
3. **Automation erstellen** klicken.
4. Die Felder ausfüllen – welche das sind, steht bei jedem Beispiel in einer Tabelle. Meist wählst du nur dein Gerät aus einer Liste aus.
5. Unten rechts **Speichern** → einen Namen vergeben (z. B. „Frostschutz“) → **Speichern**.

✅ Fertig – die Vorlage arbeitet ab jetzt im Hintergrund.

**Später einen Wert ändern** (z. B. die Frostgrenze): **Einstellungen** → **Automationen & Szenen** → deine Automation anklicken → Wert ändern → **Speichern**.

<details>
<summary>Knopf klappt nicht? So geht es von Hand</summary>

1. **Einstellungen** → **Automationen & Szenen** → oben **Blueprints**.
2. Unten rechts **Blueprint importieren**.
3. Diese Adresse einfügen und den Dateinamen am Ende durch den der gewünschten Vorlage ersetzen:
   ```
   https://github.com/sahomm/BlueBattery/blob/main/blueprints/automation/bluebattery/frostschutz.yaml
   ```
   Vorlagen: `heizungsstoerung.yaml`, `frostschutz.yaml`, `vorheizen.yaml`, `temperaturwarnung.yaml`, `tankwarnung.yaml`, `batteriewarnung.yaml`
4. **Vorschau** → **Blueprint importieren** → weiter ab Punkt 3 oben.

**Vorlage aktualisieren**, wenn es eine neue Version gibt: **Einstellungen** → **Automationen & Szenen** → **Blueprints** → **⋮** bei der Vorlage → **Blueprint erneut importieren**. Deine Einstellungen bleiben erhalten.
</details>

---

## Nachrichten aufs Handy

Damit die Vorlagen dir Nachrichten schicken können, brauchst du einmalig die **Home-Assistant-App** auf dem Handy ([iPhone](https://apps.apple.com/app/home-assistant/id1099568401), [Android](https://play.google.com/store/apps/details?id=io.homeassistant.companion.android)):

1. App installieren und mit deinem Home Assistant anmelden.
2. In Home Assistant die **Entwicklerwerkzeuge** öffnen (links in der Seitenleiste) → Reiter **Aktionen** → ins Suchfeld **notify.mobile** eintippen.
3. Es erscheint ein Name wie `notify.mobile_app_mein_handy`. **Diesen Namen aufschreiben.**

In jeder Vorlage trägst du ihn im Feld **„Benachrichtigungsdienst“** ein.

*Andere Wege* (z. B. Pushover oder Telegram) funktionieren genauso – dann steht dort deren Name.

---

## Heizungsstörung melden

**Nutzen:** Fällt die Heizung aus – z. B. weil die Gasflasche leer ist –, bekommst du sofort eine Nachricht mit Fehlercode und Fehlertext. Zusätzlich meldet die Vorlage, wenn das BB-Display selbst keine Daten mehr sendet, denn dann ist die Heizung nicht mehr überwacht.

> Aus der Praxis: Gashahn zugedreht, Heizung eingeschaltet – eine Minute später kam die Nachricht *„WoMo – Heizungsstörung: Die Heizung meldet eine Störung … (Code 2212). Zurücksetzen am Bedienteil der Heizung.“*

**Du brauchst:** BB-Display + [TIN-Adapter](https://www.blue-battery.com/product-page/tin-adapter) an Truma oder Alde

[![Vorlage importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Fheizungsstoerung.yaml)

| Einstellung | Beispiel | Hinweis |
|---|---|---|
| Störungsmelder | Truma Heizungsstörung | |
| Fehlertext / Fehlercode | Truma Fehlertext / Truma Fehlercode | optional, macht die Nachricht aussagekräftiger |
| Störung melden nach | 1 Minute | kurze Aussetzer werden ignoriert |
| Display-Verbindung | BB-Display … Verbindung | optional, für die Meldung „Display offline“ |
| Offline melden nach | 10 Minuten | |

Eine Störung wird am Bedienteil der Heizung zurückgesetzt (z. B. CP plus) – so ist es von der Heizung vorgesehen.

---

## Frostschutz

**Nutzen:** Sinkt die Innentemperatur unter eine Grenze, bekommst du eine Nachricht – und auf Wunsch schaltet sich die Heizung automatisch ein. Ideal für die Standzeit im Winter oder wenn die Heizung versehentlich aus ist.

**Du brauchst:** BB-Display (misst selbst die Innentemperatur) + TIN-Adapter für das automatische Einschalten

[![Vorlage importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Ffrostschutz.yaml)

| Einstellung | Beispiel | Hinweis |
|---|---|---|
| Innentemperatur | BB-Display … Innentemperatur | oder ein anderer Temperatursensor |
| Frostgrenze | 5 °C | |
| Unterschritten für | 10 Minuten | |
| Heizung einschalten | an | schaltet nur ein, wenn die Heizung aus ist |
| Heizung / Zieltemperatur | Truma Heizung / 12 °C | |

> Die Heizung arbeitet nach dem automatischen Einschalten ohne Rückfrage. Achte auf ausreichend Gas bzw. Strom.

---

## Vorheizen

**Nutzen:** Das Fahrzeug ist warm, wenn du ankommst. Einmalig zu einer Uhrzeit (z. B. „morgen ab 13 Uhr“), sofort per Knopf von unterwegs oder jede Woche nach Zeitplan.

**Du brauchst:** BB-Display + TIN-Adapter

**Vorab einmalig zwei Helfer anlegen:**

**Im Menü:** Einstellungen → Geräte & Dienste → Helfer → Helfer erstellen · [Direkt öffnen ↗](https://my.home-assistant.io/redirect/helpers/)
1. **Datum und/oder Uhrzeit** → Name „Vorheizen ab“ → „Datum und Uhrzeit“ auswählen.
2. **Taste** → Name „Jetzt vorheizen“.

[![Vorlage importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Fvorheizen.yaml)

| Einstellung | Beispiel | Hinweis |
|---|---|---|
| Heizung | Truma Heizung | |
| Zieltemperatur | 20 °C | |
| Heizstufe | `eco` | bei Truma `eco` oder `high`; leer = zuletzt genutzte Stufe |
| Heizdauer | 2 Stunden | danach schaltet die Heizung wieder aus; 0 = bleibt an |
| Einmalig zu Datum und Uhrzeit | Vorheizen ab | |
| Knopf „Jetzt vorheizen“ | Jetzt vorheizen | |
| Wöchentlicher Zeitplan | – | optional, Helfer „Zeitplan“ |

**Tipp:** Lege „Vorheizen ab“ und „Jetzt vorheizen“ auf dein Dashboard – dann stellst du die Startzeit mit zwei Fingertipps ein, auch unterwegs in der Home-Assistant-App.

---

## Kühlschrank und Gefrierfach

**Nutzen:** Eine Nachricht, bevor Lebensmittel verderben – z. B. wenn der Kühlschrank bei Landstromausfall nicht mehr kühlt.

**Du brauchst:** BB-Display + Temperatursensor im Kühlschrank bzw. Gefrierfach (Xiaomi LYWSD03MMC oder RuuviTag, im Display gekoppelt)

[![Vorlage importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Ftemperaturwarnung.yaml)

Für jeden Sensor eine eigene Automation aus derselben Vorlage anlegen:

| | Kühlschrank | Gefrierfach |
|---|---|---|
| Höchstwert | 10 °C | −10 °C |
| Überschritten für | 30 Minuten | 30 Minuten |

---

## Tankwarnung

**Nutzen:** Grauwasser fast voll? Frischwasser fast leer? Du erfährst es rechtzeitig – ohne nachzuschauen.

**Du brauchst:** BB-Display + [BlueLevel / BlueLevel+ oder BB-Tank](https://www.blue-battery.com/product-page/bluelevel)

[![Vorlage importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Ftankwarnung.yaml)

Für jeden Tank eine eigene Automation anlegen:

| | Grauwasser | Frischwasser |
|---|---|---|
| Tank-Füllstand | dein Grauwassertank (Füllstand in %) | dein Frischwassertank (Füllstand in %) |
| Melden, wenn der Füllstand … | über dem Grenzwert liegt | unter dem Grenzwert liegt |
| Grenzwert | 80 % | 15 % |
| Für | 5 Minuten | 5 Minuten |

---

## Batteriewarnung

**Nutzen:** Die Bordbatterie wird knapp oder die Starterbatterie schwächelt? Du kannst reagieren, bevor der Kühlschrank ausgeht oder der Motor nicht anspringt.

**Du brauchst:** BB-Display + [BlueBattery-Batteriecomputer](https://www.blue-battery.com/produkte)

[![Vorlage importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Fbatteriewarnung.yaml)

| Einstellung | Beispiel |
|---|---|
| Bordbatterie – Ladezustand | BlueBattery … Batterie |
| Mindest-Ladezustand | 30 % |
| Starterbatterie – Spannung | BlueBattery … Starterbatterie (optional) |
| Mindestspannung | 12,0 V |
| Unterschritten für | 10 Minuten |

---

## Wasserwaage

**Nutzen:** Beim Einparken siehst du auf dem Handy, **welches Rad wie viele Zentimeter** unterlegt werden muss – dazu eine Libelle wie bei einer echten Wasserwaage.

**Du brauchst:** BB-Display + [BlueLevel / BlueLevel+ oder BB-Tank](https://www.blue-battery.com/product-page/bluelevel) – sie messen neben dem Füllstand auch die Neigung des Fahrzeugs.

Für die Anzeige gibt es die Community-Karte **[RV Level Card](https://github.com/othorg/rv-level-ha-lovelace-card)** (nicht Teil dieses Projekts):

1. HACS → Suche „RV Level“ → **RV Level Lovelace Card** → Herunterladen → Browser neu laden.
2. Dashboard bearbeiten → Karte hinzufügen → „RV Level“.
3. **Pitch** = Längsneigung, **Roll** = Seitenneigung deines Tanksensors auswählen.
4. Für die cm-Angabe je Rad: **Radstand** und **Spurweite** vorne/hinten eintragen (COC-Bescheinigung oder nachmessen: Radnabe vorne bis hinten, Reifenmitte links bis rechts).
5. Zeigt die Karte eine Seite spiegelverkehrt? In der Karte „Pitch umkehren“ bzw. „Roll umkehren“ einschalten – das hängt davon ab, wie der Sensor eingebaut ist.

Beispiel (YAML):

```yaml
type: custom:rv-ha-lovelace-card
title: Wasserwaage
entities:
  pitch: sensor.mein_tank_langsneigung
  roll: sensor.mein_tank_seitenneigung
geometry:
  wheelbase_mm: 4050
  track_front_mm: 1770
  track_rear_mm: 2000
display:
  mode: rv_top          # Draufsicht; "round_compass" = Libelle
  max_tilt_deg: 5
  level_tolerance_cm: 0.5
```

---

## Energie-Dashboard

**Nutzen:** Wie viel hat die Solaranlage heute gebracht, wie viel habe ich verbraucht, wie lange reicht die Batterie? Home Assistant zeigt es als Tages-, Wochen- und Monatsübersicht.

**Du brauchst:** BB-Display + BlueBattery-Batteriecomputer

**Im Menü:** Einstellungen → Dashboards → Energie · [Direkt öffnen ↗](https://my.home-assistant.io/redirect/config_energy/)

| Bereich im Energie-Dashboard | BlueBattery-Sensor |
|---|---|
| Stromnetz → Netzbezug | … Landstrom-Energie (geschätzt) |
| Sonnenkollektoren → Solarproduktion | … Solarenergie |
| Batteriespeicher → Energie in die Batterie | … Batterie-Energie geladen |
| Batteriespeicher → Energie aus der Batterie | … Batterie-Energie entnommen |

Die Landstrom-Energie berechnet das Display aus Batterie-, Solar- und Boosterstrom – ein guter Richtwert, auch ohne eigenen Landstromzähler.

---

## Alles auf einer Seite

Home Assistant bringt die Werte von BlueBattery mit allem anderen im Fahrzeug zusammen: Solarregler anderer Hersteller, Lithium-Batterien mit Bluetooth, Bewegungsmelder, Wassersensoren, Kameras, GPS-Position. Ein Dashboard statt vieler Apps – und alle Werte lassen sich in Automationen miteinander verknüpfen.
