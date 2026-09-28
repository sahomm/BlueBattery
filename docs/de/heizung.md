# Heizung steuern

🇩🇪 Deutsch | [🇬🇧 English](../en/heating.md) · [← zurück zur Übersicht](../../README.md)

<p align="center">
  <img src="../../images/produkt-bb-display-heizung-wohnmobil.jpg" alt="Heizungssteuerung über BB-Display mit TIN-Adapter" width="560">
</p>

Mit dem **[TIN-Adapter](https://www.blue-battery.com/product-page/tin-adapter)** am BB-Display steuerst du die Heizung aus Home Assistant – vom Sofa, von unterwegs oder automatisch (siehe [Frostschutz](beispiele.md#frostschutz) und [Vorheizen](beispiele.md#vorheizen)).

## Truma

Combi mit CP plus iNet ready, über den TIN-Adapter:

- **Thermostat:** aus / heizen, Stufe **eco** oder **high**, Raum-Soll 5–30 °C
- **Boiler:** Aus / Eco (40 °C) / High (55 °C) / Boost (60 °C)
- **Anzeige:** Raum- und Wassertemperatur, Lüfterstufe, Fehlercode und -text, Verbindung
- **Energieart** (Gas / Mix / Elektro) bei **Combi E** – in den Optionen der Integration einschalten
- Weitere Heizstufen (VarioHeat, Boost) lassen sich in den Optionen einschalten

## Alde – 🧪 experimentell

Compact 3020 HE / 3030: Thermostat Zone 1 (und Zone 2, falls vorhanden), Warmwasser, Gas, Elektrostufe 1–3 kW, Priorität, Außentemperatur.

Du hast eine Alde mit TIN-Adapter? Ein [Diagnose-Export](faq.md#wie-melde-ich-einen-fehler) hilft sehr, die Unterstützung zu vervollständigen.

## So arbeitet die Steuerung

- **Befehle mit Kontrolle:** Die Integration prüft jeden Befehl am nächsten Status des BB-Displays und zeigt an, solange er unterwegs ist. Je nach Heizung ist er nach wenigen Sekunden bis etwa 30 Sekunden übernommen – mit der Truma Combi im Test nach rund 6 Sekunden.
- **Boiler-Boost erkannt:** Beim Truma-Boiler-Boost stellt die Truma die Raumheizung kurz zurück, damit das Wasser schneller heiß wird. Die Integration zeigt das als *„Raumheizung pausiert“*.
- **Störungen sofort im Blick:** Eine Störung (z. B. E212H bei fehlendem Gas) meldet die Integration innerhalb von Sekunden mit Fehlercode und -text – ideal für [Benachrichtigungen](beispiele.md#heizungsstörung-melden). Die Heizung bleibt dabei als *verbunden* angezeigt. Zurückgesetzt wird die Störung, wie von der Heizung vorgesehen, direkt am Bedienteil (z. B. CP plus); danach läuft die Heizung mit den bisherigen Einstellungen weiter.
- **Nach einem Neustart des Displays** gibt die Integration der Heizung 1–2 Minuten Zeit, die Verbindung aufzubauen, bevor sie eine Störung meldet – so entstehen keine Fehlalarme.
