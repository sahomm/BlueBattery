# BlueBattery for Home Assistant

[🇩🇪 Deutsch](README.md) | 🇬🇧 English

<p align="center">
  <img src="custom_components/bluebattery/brand/icon.png" alt="BlueBattery" width="96">
  &nbsp;&nbsp;
  <img src="images/produkt-bb-display.png" alt="BB-Display with Wi-Fi and MQTT" width="260">
</p>

Home Assistant integration for **[BlueBattery](https://www.blue-battery.com)** devices – battery and solar computers, BB-Display, tank sensors and heater control (Truma/Alde via the TIN adapter) for motorhomes and caravans.

The integration finds your **BB-Display** in the MQTT broker **automatically** and takes over all devices paired with the display – you choose which ones, and you can add new devices later without losing existing entities or their history.

> **Requirement: a BB-Display.** The integration connects BlueBattery devices exclusively **via the BB-Display**. It takes over all devices paired with the display – battery computer, BlueLevel/BB-Tank, temperature sensors and Truma/Alde via the TIN adapter. **Without a BB-Display the integration does not work (yet).**

This project is developed by [sahomm](https://github.com/sahomm) in coordination with the BlueBattery developer and with support from Claude (Anthropic).

> **Note:** Private community project, not an official BlueBattery product and **not affiliated with Truma, Alde or any other manufacturer mentioned** – see [Legal notice](#legal-notice). For questions about the devices themselves: [blue-battery.com](https://www.blue-battery.com) and the [BlueBattery forum](https://www.blue-battery.com/groups).

## Contents

- [What is BlueBattery?](#what-is-bluebattery)
- [Features](#features)
- [Supported devices](#supported-devices)
- [How does the data reach Home Assistant?](#how-does-the-data-reach-home-assistant)
- [Prerequisites](#prerequisites)
- [Step-by-step setup](#step-by-step-setup)
- [Adding devices later](#adding-devices-later)
- [Migrating from the display's built-in Home Assistant support](#migrating-from-the-displays-built-in-home-assistant-support)
- [Heater control](#heater-control)
- [Good to know](#good-to-know)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Legal notice](#legal-notice)
- [License](#license)

## What is BlueBattery?

[BlueBattery](https://www.blue-battery.com) (Kai Scheffer, Zurich) builds energy and comfort electronics for RVs:

- **Battery and solar computers** (e.g. BBX200 Pro, BBX400 Pro, D2, Basic) use a shunt to measure current, voltage, state of charge (SOC), solar, booster and shore power of the leisure battery.
- The **[BB-Display](https://www.blue-battery.com/product-page/bb-display)** is the central hub: it receives data from the battery computer, tank sensors (BlueLevel/BB-Tank) and temperature sensors (Xiaomi, RuuviTag) via Bluetooth, measures indoor temperature and humidity itself, and publishes everything via **Wi-Fi and MQTT**.
- With the **[TIN adapter](https://www.blue-battery.com/product-page/tin-adapter)** the BB-Display reads and controls **Truma** heaters (Combi with CP plus iNet ready) and **Alde** heaters (Compact 3020 HE / 3030).
- **[BlueLevel](https://www.blue-battery.com/product-page/bluelevel)** / BB-Tank measure tank levels contact-free and show the vehicle's tilt.

| [BB-Display](https://www.blue-battery.com/product-page/bb-display) | [TIN adapter](https://www.blue-battery.com/product-page/tin-adapter) | [BlueLevel+](https://www.blue-battery.com/product-page/bluelevel) | [BBX400 Pro](https://www.blue-battery.com/product-page/bbx400-pro) |
|:---:|:---:|:---:|:---:|
| <img src="images/produkt-bb-display.png" alt="BB-Display" width="170"> | <img src="images/produkt-tin-adapter.png" alt="TIN adapter" width="170"> | <img src="images/produkt-bluelevel.png" alt="BlueLevel+" width="170"> | <img src="images/produkt-bbx400-pro.png" alt="BBX400 Pro" width="170"> |
| central hub, Wi-Fi + MQTT | Truma/Alde on the BB-Display | tank level + tilt | battery and solar computer |

**How it fits together:** battery computer, tank sensors and temperature sensors send via Bluetooth to the BB-Display; the heater is connected via the TIN adapter. The BB-Display sends everything via Wi-Fi to the MQTT broker in Home Assistant – and receives heater commands from there.

```
Battery computer ──┐
BlueLevel/BB-Tank ─┼─ Bluetooth ──► BB-Display ◄── Wi-Fi / MQTT ──► Home Assistant
Xiaomi/RuuviTag ───┘                    ▲                           (Mosquitto + BlueBattery)
                                        │ cable
                  Truma/Alde ── TIN adapter
```

## Features

<p align="center">
  <img src="images/integration-geraete.png" alt="BlueBattery in Home Assistant: BB-Display with all paired devices" width="480">
  <br><em>One BB-Display with battery computer, tanks, temperature sensors and Truma</em>
</p>

- **Automatic discovery** of the BB-Display in the MQTT broker – regardless of the MQTT topic configured on the display (fallback: manual entry).
- **Device selection** during setup: all devices paired with the display – battery computer, heater, each tank, each temperature sensor individually.
- **New devices:** as soon as a device is newly paired with the display, Home Assistant reports it; it is added via reconfiguration – existing entities and their history stay untouched.
- **Battery & energy:** state of charge, voltage, current, solar, booster, starter battery, energy counters (usable in the Energy dashboard).
- **Tanks:** level in % and litres, tank type, tilt.
- **Climate:** indoor temperature, humidity, dew point of the display; external temperature/humidity sensors (e.g. fridge, freezer).
- **Heater:** thermostat with eco/high, room setpoint, boiler, error code, online state – a basis for **frost protection and failure notifications**.
- **Honest availability:** values count as current only while the device is actually publishing – not just because an old message is retained in the broker.
- **Diagnostics export** with redacted addresses for bug reports.

## Supported devices

All devices come **via the BB-Display** – they must be paired with or connected to it.

| Device | Connection to the BB-Display | Status |
|---|---|---|
| BB-Display itself (indoor temperature, humidity, dew point, diagnostics) | – | ✅ supported |
| Battery computers (BBX200/400 Pro, D1/D2, X200/X300, BBX400, Basic) | Bluetooth, selected on the display | ✅ supported |
| BlueLevel / BlueLevel+, BB-Tank (channels) | Bluetooth, paired with the display | ✅ supported |
| Xiaomi LYWSD03MMC, RuuviTag | Bluetooth, paired with the display | ✅ supported |
| Truma Combi (CP plus iNet ready) | TIN adapter | ✅ supported |
| Alde Compact 3020 HE / 3030 | TIN adapter | 🧪 experimental |

## How does the data reach Home Assistant?

The devices send via Bluetooth to the BB-Display or are connected through the TIN adapter. The display forwards everything via Wi-Fi/MQTT to Home Assistant and receives heater commands from there.

**The BB-Display is the hub – with limits:**
- It forwards **exactly one** battery computer – the one selected on the display. A **second** battery computer (e.g. a BBX400 Pro for a second battery bank) does not appear.
- It only forwards the tanks and sensors **paired with the display**.
- For tanks it forwards level, volume, tilt and signal – **diagnostic values** of the tank sensors (e.g. distance to the water surface, memory) are not included.

**Avoid duplicate values:** Many BlueBattery devices have **built-in Home Assistant support** ("Home Assistant" / "MQTT Discovery" switch). Always switch it off on the BB-Display, and on BB-Tank/BlueLevel as well if they are paired with the display. For devices that do not come via the display – e.g. a second battery computer – **leave it on**.

## Prerequisites

1. **Home Assistant** – easiest with Home Assistant OS (e.g. on a Raspberry Pi in the vehicle). With Home Assistant Container/Core you need your own MQTT broker.
2. **A shared network:** BB-Display and Home Assistant must reach each other – typically the same Wi-Fi in the vehicle (RV router). The BB-Display uses **2.4 GHz Wi-Fi**.
3. **An MQTT broker** – recommended: the **Mosquitto broker** app in Home Assistant (guide below).
4. **The MQTT integration** in Home Assistant, connected to that broker.
5. **HACS** to install this integration ([hacs.xyz](https://hacs.xyz)).
6. **BB-Display** (required) with current firmware, connected to Wi-Fi (see the [BB-Display product page](https://www.blue-battery.com/product-page/bb-display), firmware: [BlueBattery on GitHub](https://github.com/blue-battery-ch/BB-Display/releases)).
7. **Your BlueBattery devices paired with the BB-Display** – see [step 1](#step-1--pair-devices-with-the-bb-display).
8. For heater control: **TIN adapter** connected to the BB-Display and the Truma or Alde, and set up in the display.

## Step-by-step setup

### Step 1 – Pair devices with the BB-Display

Home Assistant only sees what the BB-Display knows. So first set up on the display (on the device or in its web interface) everything you want in Home Assistant:

- **select the battery computer** (the display forwards exactly one),
- **pair and name tank sensors** (BlueLevel/BlueLevel+, BB-Tank),
- **pair and name temperature sensors** (Xiaomi LYWSD03MMC, RuuviTag),
- **connect the TIN adapter** and set up the heater.

The integration takes over the names from the display (e.g. "Fresh water", "Fridge"). Guide: [BB-Display product page](https://www.blue-battery.com/product-page/bb-display).

### Step 2 – Install the Mosquitto broker

1. Home Assistant → **Settings → Apps → App store** → **Mosquitto broker** → **Install**.
2. After installing, **Start** it and enable **Start on boot** and **Watchdog**.

<!-- 📷 TODO: images/01-mosquitto-app.png -->
> 📷 *Image to follow: installing the Mosquitto app*

### Step 3 – Create an MQTT user

The BB-Display logs in to the broker with its own user.

1. **Settings → People → Add person**.
2. Enter a name (e.g. `BB-Display`) and switch on **"Allow login"**.
3. Set a **username** (e.g. `mqtt_user`) and a **strong password** – note both, you will enter them on the display in step 5.
4. Switch on **"Local access only"**, **not an administrator** → **Create**.

> The usernames `homeassistant` and `addons` are reserved by the Mosquitto broker and will not work. Don't use your own Home Assistant login either.

<!-- 📷 TODO: images/02-mqtt-user.png -->
> 📷 *Image to follow: creating the MQTT user*

### Step 4 – Set up the MQTT integration

1. **Settings → Devices & services** – usually **MQTT** already shows up under "Discovered" → **Configure** → confirm.
2. If not: **Add integration → MQTT** and select the Mosquitto broker.

<!-- 📷 TODO: images/03-mqtt-integration.png -->
> 📷 *Image to follow: MQTT integration*

### Step 5 – Connect the BB-Display to the broker

Open the display's web interface in a browser (IP address e.g. from your router's device list) → **Einstellungen (Settings) → Fernzugriff (Remote access) → MQTT**:

| Field | Value |
|---|---|
| Server | IP address of your Home Assistant (e.g. `192.168.1.10`) |
| Client ID | any, e.g. `BBDisplay` |
| Port | `1883` |
| User / Password | from step 3 |
| Topic | **`BlueBattery/BB-Display`** (factory default, recommended) |
| Send data every | `30` seconds |
| Home Assistant | **off** – this integration takes over (see [Migrating](#migrating-from-the-displays-built-in-home-assistant-support)) |

After saving, the display restarts. The connection symbol ⇄ appears at the top of the screen.

> **Fixed IP address:** give Home Assistant a fixed IP address in your router (DHCP reservation). Otherwise the display loses the broker if the address changes.

<!-- 📷 TODO: images/04-bb-display-mqtt.png -->
> 📷 *Image to follow: MQTT settings on the BB-Display*

> **Any topic works:** the integration also detects BlueBattery devices under other topics (up to three levels, e.g. `camper/bb/display`). The factory default is still recommended.

### Step 6 – Install the integration via HACS

1. **HACS → Integrations → ⋮ → Custom repositories** → `https://github.com/sahomm/BlueBattery`, category **Integration**.
2. Search for **BlueBattery** → **Download** – choose the **latest version** (`v…`), not an identifier like `21ff56e`.
3. **Restart** Home Assistant.

### Step 7 – Set up BlueBattery

1. **Settings → Devices & services**: **BlueBattery – BB-Display** appears under "Discovered" → **Configure**.
   *Not found?* → **Add integration → BlueBattery → Manual** and enter the topic from step 5.
2. The integration lists all devices paired with the display – **select** what to add:

   | ☑ | Device |
   |---|---|
   | ☑ | Battery computer A1B2C3 |
   | ☑ | Truma (TIN adapter) |
   | ☑ | Tank "Fresh water" (BB-Tank, channel 1) |
   | ☐ | Temperature sensor "Fridge" |

3. **Done** – entities are created per device, with the BB-Display as parent device. This is what the result looks like:

<p align="center">
  <img src="images/integration-geraete.png" alt="BlueBattery in Home Assistant: BB-Display with all paired devices" width="700">
  <br><em>One BB-Display with battery computer, tanks, temperature sensors and Truma</em>
</p>

<!-- 📷 TODO: images/06-config-flow-auswahl.png -->

## Adding devices later

When a device is added (new tank, another temperature sensor, TIN adapter):

1. **Pair the device with the BB-Display** (see [step 1](#step-1--pair-devices-with-the-bb-display)).
2. Wait a moment – Home Assistant reports under **Settings → Repairs**: *"New BlueBattery device found"*.
3. **Devices & services → BlueBattery → Configure** → tick the new device → save.

- Existing entities are not changed – **history and statistics are kept**.
- A deselected device is only **disabled** by default (history kept); it can be removed on request.
- A device that is temporarily unreachable (e.g. tank out of range) is shown as **unavailable**, not removed.

## Migrating from the display's built-in Home Assistant support

The BB-Display has its own Home Assistant support (switch **"Home Assistant"** in the MQTT settings). This integration replaces it. **Running both results in duplicate entities.**

**Fresh start (recommended if previous history doesn't matter):** switch off "Home Assistant" on the display – the old entities disappear – and set up this integration.

**Keep history:** the integration can take over the existing entity IDs so dashboards, automations and history keep working:
1. Set up the integration (entities appear twice for a while).
2. **Devices & services → BlueBattery → Configure → Migration: prepare** – check the list and save.
3. On the display, switch off **"Home Assistant"** under MQTT and wait a minute.
4. **Configure → Migration: finish.**

Entities that exist as a different type in the integration (e.g. "Booster limit" now a sensor instead of a binary sensor) are not taken over.

## Heater control

<p align="center">
  <img src="images/produkt-bb-display-heizung-wohnmobil.jpg" alt="Heater control via BB-Display with TIN adapter" width="560">
</p>

**Truma** (Combi with CP plus iNet ready, via TIN adapter)
- Thermostat: off / heat, level **eco** or **high**, room setpoint 5–30 °C
- Boiler: Off / Eco (40 °C) / High (55 °C) / Boost (60 °C)
- Display: room and water temperature, fan level, error code/text, connection
- Energy source (gas / mix / electric) only on **Combi E** – can be enabled in the options

**Alde** (Compact 3020 HE / 3030) – 🧪 *experimental*
- Thermostat zone 1 (and zone 2 if present), hot water, gas, electric level 1–3 kW, priority, outdoor temperature

**How control works**
- **Commands with verification:** the integration checks every command against the next status of the BB-Display and shows while it is pending. Depending on the heater it is applied within a few seconds up to about 30 seconds – with the Truma Combi in our test after about 6 seconds.
- **Boiler boost detected:** during Truma boiler boost the Truma briefly holds back room heating so the water heats up faster. The integration shows this as *"room heating paused"*.
- **Faults at a glance:** a fault (e.g. E212H when gas is missing) is reported within seconds with error code and text – ideal for notifications, e.g. for frost protection. The heater is still shown as *connected*. As intended by the heater, the fault is reset directly on the control panel (e.g. CP plus); the heater then continues with its previous settings.

## Good to know

- **Energy counters straight from the display** (`… Wh`): the display calculates them and starts fresh every day; Home Assistant continues them seamlessly in the Energy dashboard. The display derives **shore power energy** from battery, solar and booster current – a good guide value, even without a dedicated shore power meter.
- **Temperature sensors with failure detection:** if the display no longer reports a valid value for a sensor, the integration shows "unknown" instead of an outdated value.
- **After a Home Assistant restart** the last known values are available immediately. The display counts as *connected* as soon as it sends fresh data again – so the connection indicator stays reliable.
- **After a display restart** the integration gives the heater 1–2 minutes to establish its connection before reporting a fault – so there are no false alarms.

## Troubleshooting

- **No devices found:** Is the display publishing? In the MQTT integration use **Configure → Listen to a topic** with `BlueBattery/#` – messages should arrive every 30 s. Alternatively use [MQTT Explorer](https://mqtt-explorer.com).
- **Device missing from the selection:** the integration only lists devices that are paired with the BB-Display and currently reported by it. Pair the device with the display (or select it as battery computer), check the range, then open **Configure** again.
- **⇄ symbol missing on the display:** check server IP, port, user/password; is the Mosquitto app running? If the MQTT user was just created and login fails, **restart the Mosquitto app** once.
- **HACS: "Failed to download … refs/heads/<identifier>.zip" (404):** a commit identifier was selected instead of a version. **HACS → BlueBattery → ⋮ → Redownload** and choose the latest version `v…`.
- **Old BlueBattery devices remain after switching off built-in discovery:** some devices (seen with BB-Tank and BlueLevel) do not delete their discovery entries in the broker. Fix: in [MQTT Explorer](https://mqtt-explorer.com) delete the device's entries under `homeassistant/…` – the devices then disappear from Home Assistant.
- **Duplicate entities:** the "Home Assistant" switch on the display is still on (see [Migrating](#migrating-from-the-displays-built-in-home-assistant-support)).
- **Reporting a bug:** **Devices & services → BlueBattery → ⋮ → Download diagnostics** (addresses are redacted) and attach it to an [issue](https://github.com/sahomm/BlueBattery/issues).

## Contributing

- Bugs and feature requests: [GitHub Issues](https://github.com/sahomm/BlueBattery/issues)
- **Alde owners wanted:** if you have an Alde with TIN adapter, a diagnostics export helps a lot.
- Technical basis: [architecture](docs/ARCHITEKTUR.md) (German)

## Legal notice

- **No affiliation with heater or device manufacturers:** This project is **not affiliated** with Truma Gerätetechnik GmbH & Co. KG, Alde International Systems AB or any other manufacturer mentioned here (including Xiaomi and Ruuvi). It is not supported, reviewed or endorsed by them.
- **Trademarks used descriptively only:** Names such as *Truma*, *Combi*, *CP plus*, *iNet*, *Alde*, *Xiaomi*, *RuuviTag*, *Home Assistant* or *Raspberry Pi* are trademarks or product names of their respective owners. They are used solely to describe **which devices** the integration works with. **No logos** of these manufacturers are used.
- **Relationship with BlueBattery:** The integration is developed in coordination with the BlueBattery developer, but it is a community project and not an official BlueBattery product. BlueBattery logo and product images © BlueBattery, used with kind permission.
- **Heater control:** The heater is controlled via BlueBattery's BB-Display and TIN adapter, not via interfaces or software of the heater manufacturers. Use at your own risk. For warranty, guarantee and operation of the heater, only its manufacturer or dealer is responsible; please check heater faults on the heater's own control panel first.
- **Liability:** The software is provided without warranty (see [License](#license)). It does not replace on-site monitoring – especially not for frost protection.

## License

[MIT](LICENSE)
