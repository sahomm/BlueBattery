# Practical examples

[🇩🇪 Deutsch](../de/beispiele.md) | 🇬🇧 English · [← back to overview](../../README.en.md)

The BlueBattery app shows you what is going on in your vehicle. With Home Assistant **your vehicle acts on its own**: it tells you when something is wrong, pre-heats before you arrive and protects against frost – even when nobody is on board.

For most examples there is a **ready-made template (blueprint)**. One click on the button imports it into your Home Assistant; then you just pick your devices and adjust the limits – no programming needed. All templates are set up in the author's motorhome.

**Contents**
- [Set up notifications](#set-up-notifications) – once, beforehand
- [Heater fault notification](#heater-fault-notification)
- [Frost protection](#frost-protection)
- [Pre-heating](#pre-heating)
- [Fridge and freezer](#fridge-and-freezer)
- [Tank warning](#tank-warning)
- [Battery warning](#battery-warning)
- [Spirit level](#spirit-level)
- [Energy dashboard](#energy-dashboard)
- [Everything on one page](#everything-on-one-page)
- [Import a template and change limits](#import-a-template-and-change-limits)

> The templates' texts (names, settings, notifications) are in German. Notification texts can be adjusted after "Take control" in the automation if needed.

---

## Set up notifications

The templates send messages to your phone. The easiest way is the **Home Assistant app** ([iOS](https://apps.apple.com/app/home-assistant/id1099568401), [Android](https://play.google.com/store/apps/details?id=io.homeassistant.companion.android)): install the app, log in – done. You then have a notification service such as `notify.mobile_app_my_phone`.

**What is my service called?** Developer tools → Actions → type "notify.". Enter the name shown (e.g. `notify.mobile_app_my_phone`) in each template under "Benachrichtigungsdienst" (notification service). Other services such as Pushover or Telegram work the same way.

---

## Heater fault notification

**Benefit:** If the heater fails – e.g. because the gas bottle is empty – you immediately get a message with error code and error text. The template also reports when the BB-Display itself stops sending data, because then the heater is no longer monitored.

> From practice: gas valve closed, heater switched on – one minute later the message arrived: *"WoMo – Heizungsstörung: Die Heizung meldet eine Störung … (Code 2212). Zurücksetzen am Bedienteil der Heizung."*

**You need:** BB-Display + [TIN adapter](https://www.blue-battery.com/product-page/tin-adapter) on Truma or Alde

[![Import template](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Fheizungsstoerung.yaml)

| Setting | Example | Note |
|---|---|---|
| Fault sensor | Truma heater fault | |
| Error text / error code | Truma error text / Truma error code | optional, makes the message more informative |
| Report fault after | 1 minute | short glitches are ignored |
| Display connection | BB-Display … connection | optional, for the "display offline" message |
| Report offline after | 10 minutes | |

A fault is reset on the heater's control panel (e.g. CP plus) – as intended by the heater.

---

## Frost protection

**Benefit:** If the indoor temperature drops below a limit, you get a message – and if you like, the heater switches on automatically. Ideal while the vehicle is parked in winter or when the heater was switched off by mistake.

**You need:** BB-Display (measures the indoor temperature itself) + TIN adapter for switching on automatically

[![Import template](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Ffrostschutz.yaml)

| Setting | Example | Note |
|---|---|---|
| Indoor temperature | BB-Display … indoor temperature | or another temperature sensor |
| Frost limit | 5 °C | |
| Below for | 10 minutes | |
| Switch heater on | on | only switches on if the heater is off |
| Heater / target temperature | Truma heater / 12 °C | |

> After switching on automatically, the heater runs without asking. Make sure there is enough gas or power.

---

## Pre-heating

**Benefit:** The vehicle is warm when you arrive. Once at a set time (e.g. "tomorrow from 1 pm"), instantly with a button while on the way, or weekly on a schedule.

**You need:** BB-Display + TIN adapter

**Create two helpers once beforehand:**

[![Open helpers](https://my.home-assistant.io/badges/helpers.svg)](https://my.home-assistant.io/redirect/helpers/)

*Manually:* Settings → Devices & services → Helpers → Create helper
1. **Date and/or time** → name "Pre-heat from" → select "Date and time".
2. **Button** → name "Pre-heat now".

[![Import template](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Fvorheizen.yaml)

| Setting | Example | Note |
|---|---|---|
| Heater | Truma heater | |
| Target temperature | 20 °C | |
| Heating level | `eco` | for Truma `eco` or `high`; empty = last used level |
| Heating duration | 2 hours | then the heater switches off again; 0 = stays on |
| Once at date and time | Pre-heat from | |
| "Pre-heat now" button | Pre-heat now | |
| Weekly schedule | – | optional, "Schedule" helper |

**Tip:** Put "Pre-heat from" and "Pre-heat now" on your dashboard – then you set the start time with two taps, even on the way in the Home Assistant app.

---

## Fridge and freezer

**Benefit:** A message before food spoils – e.g. when the fridge stops cooling after a shore power outage.

**You need:** BB-Display + temperature sensor in the fridge or freezer (Xiaomi LYWSD03MMC or RuuviTag, paired with the display)

[![Import template](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Ftemperaturwarnung.yaml)

Create one automation per sensor from the same template:

| | Fridge | Freezer |
|---|---|---|
| Maximum | 10 °C | −10 °C |
| Above for | 30 minutes | 30 minutes |

---

## Tank warning

**Benefit:** Grey water almost full? Fresh water almost empty? You find out in time – without checking.

**You need:** BB-Display + [BlueLevel / BlueLevel+ or BB-Tank](https://www.blue-battery.com/product-page/bluelevel)

[![Import template](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Ftankwarnung.yaml)

Create one automation per tank:

| | Grey water | Fresh water |
|---|---|---|
| Tank level | your grey water tank (level in %) | your fresh water tank (level in %) |
| Report when the level … | is above the limit | is below the limit |
| Limit | 80 % | 15 % |
| For | 5 minutes | 5 minutes |

---

## Battery warning

**Benefit:** House battery running low or starter battery getting weak? You can react before the fridge stops or the engine won't start.

**You need:** BB-Display + [BlueBattery battery computer](https://www.blue-battery.com/produkte)

[![Import template](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fsahomm%2FBlueBattery%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbluebattery%2Fbatteriewarnung.yaml)

| Setting | Example |
|---|---|
| House battery – state of charge | BlueBattery … battery |
| Minimum state of charge | 30 % |
| Starter battery – voltage | BlueBattery … starter battery (optional) |
| Minimum voltage | 12.0 V |
| Below for | 10 minutes |

---

## Spirit level

**Benefit:** When parking, your phone shows **which wheel needs how many centimetres** of levelling block – plus a bubble level like a real spirit level.

**You need:** BB-Display + [BlueLevel / BlueLevel+ or BB-Tank](https://www.blue-battery.com/product-page/bluelevel) – besides the level they also measure the vehicle's tilt.

For the display there is the community card **[RV Level Card](https://github.com/othorg/rv-level-ha-lovelace-card)** (not part of this project):

1. HACS → search "RV Level" → **RV Level Lovelace Card** → Download → reload the browser.
2. Edit dashboard → Add card → "RV Level".
3. Select **pitch** = longitudinal tilt, **roll** = lateral tilt of your tank sensor.
4. For cm per wheel: enter **wheelbase** and **track width** front/rear (vehicle documents, or measure: wheel hub front to rear, tyre centre left to right).
5. Does the card show a side mirrored? Enable "invert pitch" or "invert roll" in the card – this depends on how the sensor is mounted.

Example (YAML):

```yaml
type: custom:rv-ha-lovelace-card
title: Spirit level
entities:
  pitch: sensor.my_tank_longitudinal_tilt
  roll: sensor.my_tank_lateral_tilt
geometry:
  wheelbase_mm: 4050
  track_front_mm: 1770
  track_rear_mm: 2000
display:
  mode: rv_top          # top view; "round_compass" = bubble level
  max_tilt_deg: 5
  level_tolerance_cm: 0.5
```

---

## Energy dashboard

**Benefit:** How much did the solar system produce today, how much did I use, how long will the battery last? Home Assistant shows it as a daily, weekly and monthly overview.

**You need:** BB-Display + BlueBattery battery computer

[![Open energy settings](https://my.home-assistant.io/badges/config_energy.svg)](https://my.home-assistant.io/redirect/config_energy/)

*Manually:* Settings → Dashboards → Energy

| Section in the energy dashboard | BlueBattery sensor |
|---|---|
| Electricity grid → grid consumption | … shore power energy (estimated) |
| Solar panels → solar production | … solar energy |
| Home battery storage → energy going in | … battery energy charged |
| Home battery storage → energy coming out | … battery energy discharged |

The display calculates shore power energy from battery, solar and booster current – a good guide value, even without a dedicated shore power meter.

---

## Everything on one page

Home Assistant brings BlueBattery's values together with everything else in the vehicle: solar chargers from other manufacturers, lithium batteries with Bluetooth, motion detectors, water sensors, cameras, GPS position. One dashboard instead of many apps – and all values can be combined in automations.

---

## Import a template and change limits

**Import:** click the "Import template" button → confirm "Import blueprint" in Home Assistant → **Create automation** → select devices and limits → Save.

*Button not working?* Settings → Automations & scenes → Blueprints → **Import blueprint** → paste this address (file name depending on the template):

```
https://github.com/sahomm/BlueBattery/blob/main/blueprints/automation/bluebattery/frostschutz.yaml
```

Templates: `heizungsstoerung.yaml` (heater fault), `frostschutz.yaml` (frost protection), `vorheizen.yaml` (pre-heating), `temperaturwarnung.yaml` (temperature warning), `tankwarnung.yaml` (tank warning), `batteriewarnung.yaml` (battery warning)

**Change limits:** Settings → Automations & scenes → open the automation → change the value → Save. That's all.

**Update a template:** Settings → Automations & scenes → Blueprints → ⋮ next to the template → "Re-import blueprint". Your settings are kept.
