# Step-by-step setup

[🇩🇪 Deutsch](../de/einrichtung.md) | 🇬🇧 English · [← back to overview](../../README.en.md)

This guide takes you from the BB-Display to the finished integration. Each step names the path through the Home Assistant menu. Often it is followed by a link **"Open directly ↗"** that opens the matching page right away.

> **"Open directly"** goes through [my.home-assistant.io](https://my.home-assistant.io): the first time, the page asks once for the address of your Home Assistant (e.g. `http://homeassistant.local:8123`) → enter it → **Save**. After that you briefly confirm with **"Open link"** each time – a security check. More: [If "Open directly" doesn't work](#if-open-directly-doesnt-work).

**Contents**
- [Before you start](#before-you-start)
- [Step 1 – Pair devices with the BB-Display](#step-1--pair-devices-with-the-bb-display)
- [Step 2 – Install the Mosquitto broker](#step-2--install-the-mosquitto-broker)
- [Step 3 – Create a user for the display](#step-3--create-a-user-for-the-display)
- [Step 4 – Set up the MQTT integration](#step-4--set-up-the-mqtt-integration)
- [Step 5 – Connect the BB-Display to Home Assistant](#step-5--connect-the-bb-display-to-home-assistant)
- [Step 6 – Install BlueBattery via HACS](#step-6--install-bluebattery-via-hacs)
- [Step 7 – Set up BlueBattery](#step-7--set-up-bluebattery)
- [Adding devices later](#adding-devices-later)
- [If "Open directly" doesn't work](#if-open-directly-doesnt-work)

---

## Before you start

- **BB-Display** with current firmware, connected to your vehicle's Wi-Fi ([guide on the product page](https://www.blue-battery.com/product-page/bb-display)). The display uses **2.4 GHz Wi-Fi**.
- **Home Assistant** on the same network – easiest with **Home Assistant OS**, e.g. on a Raspberry Pi in the vehicle.
- **HACS** in Home Assistant ([how to install HACS](https://hacs.xyz/docs/use/)).
- **Internet** during setup. In operation everything runs locally.

<details>
<summary>Home Assistant Container or Core?</summary>

There are no apps there. You need your own MQTT broker (e.g. Mosquitto as a Docker container) and set up the MQTT integration with its address in step 4. Steps 2 and 3 are then omitted; you create user and password in the broker itself.
</details>

---

## Step 1 – Pair devices with the BB-Display

Home Assistant only sees what the BB-Display knows. So first set up on the display (on the device or in its web interface) everything you want in Home Assistant:

- **select the battery computer** – the display forwards exactly one,
- **pair and name tank sensors** (BlueLevel/BlueLevel+, BB-Tank),
- **pair and name temperature sensors** (Xiaomi LYWSD03MMC, RuuviTag),
- **connect the TIN adapter** and set up the heater.

The integration takes over the names from the display (e.g. "Fresh water", "Fridge").

---

## Step 2 – Install the Mosquitto broker

The broker is the "post office" through which the BB-Display sends its data to Home Assistant. Mosquitto is an official app and already included in the app store – nothing needs to be added.

**In the menu:** Settings → **Apps** → **App store** → search "Mosquitto broker". · [Open directly ↗](https://my.home-assistant.io/redirect/supervisor_addon/?addon=core_mosquitto)

1. **Install**.
2. **Start** it and enable **Start on boot** and **Watchdog**.

<!-- 📷 TODO: images/01-mosquitto-app.png -->

---

## Step 3 – Create a user for the display

The BB-Display logs in to the broker with its own user.

**In the menu:** Settings → **People**. · [Open directly ↗](https://my.home-assistant.io/redirect/people/)

1. **Add person**.
2. Enter a name (e.g. `BB-Display`) and switch on **"Allow login"**.
3. Set a **username** (e.g. `mqtt_user`) and a **strong password** – note both, you need them in step 5.
4. Switch on **"Local access only"**, **not an administrator** → **Create**.

> The usernames `homeassistant` and `addons` are reserved by the Mosquitto broker and will not work. Don't use your own Home Assistant login either.

<!-- 📷 TODO: images/02-mqtt-user.png -->

---

## Step 4 – Set up the MQTT integration

**In the menu:** Settings → **Devices & services** – usually **MQTT** already shows up under "Discovered" → **Configure** → confirm. If not: **Add integration** → "MQTT" → select the Mosquitto broker. · [Open directly ↗](https://my.home-assistant.io/redirect/config_flow_start/?domain=mqtt)

<!-- 📷 TODO: images/03-mqtt-integration.png -->

---

## Step 5 – Connect the BB-Display to Home Assistant

Open the display's web interface in a browser (you find its IP address e.g. in your router's device list) → **Settings → Remote access → MQTT**:

| Field | Value |
|---|---|
| Server | IP address of your Home Assistant (e.g. `192.168.1.10`) |
| Client ID | anything, e.g. `BBDisplay` |
| Port | `1883` |
| User / Password | from step 3 |
| Topic | keep the factory default (`BlueBattery/BB-Display`) |
| Send data every | `30` seconds |
| Home Assistant | **off** – this integration takes over |

After saving, the display restarts. The connection symbol **⇄** appears at the top of the screen.

> **Fixed IP address:** give Home Assistant a fixed IP address in your router (DHCP reservation). Otherwise the display loses the broker if the address changes.

<details>
<summary>Use a different topic?</summary>

The integration also finds the BB-Display under a custom topic (up to three levels, e.g. `camper/bb/display`). The factory default is still recommended.
</details>

<!-- 📷 TODO: images/04-bb-display-mqtt.png -->

---

## Step 6 – Install BlueBattery via HACS

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sahomm&repository=BlueBattery&category=integration)

The button opens BlueBattery directly in HACS → **Download** → **restart** Home Assistant (Settings → System → ⏻ → Restart Home Assistant).

*Manually – add the repository:*
1. Open **HACS** → **⋮** (top right) → **Custom repositories**.
2. Repository: `https://github.com/sahomm/BlueBattery`, type: **Integration** → **Add**.
3. Search for **BlueBattery** in HACS → **Download** → confirm the latest version.
4. **Restart** Home Assistant.

---

## Step 7 – Set up BlueBattery

**In the menu:** Settings → **Devices & services** → **BlueBattery – BB-Display** appears under "Discovered" → **Configure**. · [Open directly ↗](https://my.home-assistant.io/redirect/config_flow_start/?domain=bluebattery)

1. Confirm – the integration briefly checks that the display sends current data (up to one minute).
2. **Select the devices** to add – all devices paired with the display are listed.
3. **Done.** Each device appears with its values, with the BB-Display as parent device:

<p align="center">
  <img src="../../images/integration-geraete.png" alt="BlueBattery in Home Assistant: BB-Display with all paired devices" width="700">
</p>

*Not under "Discovered"?* → **Add integration** → "BlueBattery" → enter the topic from step 5. See also [Questions & answers](faq.md).

**What next?** Set up notifications, frost protection and more with the [practical examples](examples.md).

---

## Adding devices later

New tank, another temperature sensor, TIN adapter retrofitted?

1. **Pair the device with the BB-Display**.
2. Wait a moment – Home Assistant reports under **Settings → Repairs**: *"New BlueBattery device found"*.
3. **Settings → Devices & services → BlueBattery → Configure** → tick the new device → save.

- Existing devices, values and their history stay unchanged.
- A deselected device is only **disabled** (history is kept); it can be removed on request.
- If a device is briefly out of range, it is shown as **unavailable**, not removed.

---

## If "Open directly" doesn't work

The "Open directly" links and the HACS button go through [my.home-assistant.io](https://my.home-assistant.io). On the first click the page asks for the address of your Home Assistant (e.g. `http://homeassistant.local:8123` or `http://192.168.1.10:8123`) and remembers it.

Typical reasons when it fails:
- The stored address is no longer correct → on [my.home-assistant.io](https://my.home-assistant.io) click "Change" at the bottom and enter it again.
- You opened the link in the Home Assistant **app** → open it in a **browser** instead.
- Your phone is not on the vehicle's network → connect to the vehicle Wi-Fi.

The menu path always leads to the same place.
