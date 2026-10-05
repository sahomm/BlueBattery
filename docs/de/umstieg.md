# Umstieg von der eingebauten Home-Assistant-Anbindung

🇩🇪 Deutsch | [🇬🇧 English](../en/migration.md) · [← zurück zur Übersicht](../../README.md)

Das BB-Display bringt eine eigene, einfache Anbindung an Home Assistant mit (Schalter **„Home Assistant“** im Display unter Einstellungen → Fernzugriff → MQTT). Diese Integration ersetzt sie. **Beides gleichzeitig führt zu doppelten Werten** – schalte die eingebaute Anbindung deshalb aus.

## Neu einsteigen (empfohlen)

Wenn der bisherige Verlauf keine Rolle spielt:

1. Im Display unter **Einstellungen → Fernzugriff → MQTT** den Schalter **„Home Assistant“ ausschalten** – die alten Einträge verschwinden aus Home Assistant.
2. Die Integration nach der [Einrichtung](einrichtung.md) installieren.

## Verlauf behalten

Die Integration kann die bisherigen Entitäts-IDs übernehmen – Dashboards, Automationen und Verlauf laufen dann einfach weiter:

1. Integration einrichten (die Werte erscheinen vorübergehend doppelt).
2. **Einstellungen → Geräte & Dienste → BlueBattery → Konfigurieren → Umstieg: vorbereiten** – die Liste prüfen und speichern.
3. Im Display unter **Einstellungen → Fernzugriff → MQTT** den Schalter **„Home Assistant“** ausschalten, eine Minute warten.
4. **Konfigurieren → Umstieg: abschließen.**

Werte, die es in der Integration als andere Art gibt (z. B. „Booster-Limit“ jetzt als Sensor statt als Ein/Aus-Wert), werden nicht übernommen.

## Weitere BlueBattery-Geräte mit eigener Anbindung

Auch BB-Tank und BlueLevel haben einen Schalter „Home Assistant“ bzw. „MQTT Discovery“. Schalte ihn aus, wenn das Gerät am BB-Display gekoppelt ist – sonst erscheinen die Werte doppelt. Bei Geräten, die **nicht** über das Display kommen (z. B. ein zweiter Batteriecomputer), lass ihn an.

Bleiben nach dem Ausschalten alte Geräte in Home Assistant stehen, hilft die [FAQ](faq.md#nach-dem-ausschalten-der-eingebauten-anbindung-bleiben-alte-geräte-stehen).
