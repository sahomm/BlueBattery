# Questions & answers

[🇩🇪 Deutsch](../de/faq.md) | 🇬🇧 English · [← back to overview](../../README.en.md)

**General**
- [Do I need internet?](#do-i-need-internet)
- [Do I need a BB-Display?](#do-i-need-a-bb-display)
- [Which data arrives in Home Assistant?](#which-data-arrives-in-home-assistant)
- [Why do I see only one battery computer?](#why-do-i-see-only-one-battery-computer)
- [How accurate is the shore power energy?](#how-accurate-is-the-shore-power-energy)
- [What happens after a restart?](#what-happens-after-a-restart)
- [How do I open the display's settings page later?](#how-do-i-open-the-displays-settings-page-later)

**Troubleshooting**
- [The ⇄ symbol is missing on the display](#the--symbol-is-missing-on-the-display)
- [BlueBattery does not appear under "Discovered"](#bluebattery-does-not-appear-under-discovered)
- [A device is missing from the selection](#a-device-is-missing-from-the-selection)
- [All values are "unavailable"](#all-values-are-unavailable)
- [I see all values twice](#i-see-all-values-twice)
- [Old devices remain after switching off the built-in support](#old-devices-remain-after-switching-off-the-built-in-support)
- [HACS reports "Failed to download … 404"](#hacs-reports-failed-to-download--404)
- ["Open directly" doesn't work](#open-directly-doesnt-work)
- [How do I report a bug?](#how-do-i-report-a-bug)

**Advanced**
- [Home Assistant Container or Core](#home-assistant-container-or-core)
- [Watching MQTT messages](#watching-mqtt-messages)
- [How does the data reach Home Assistant?](#how-does-the-data-reach-home-assistant)

---

## General

### Do I need internet?

For the **setup**, yes – Home Assistant downloads the Mosquitto app, HACS and this integration from the internet. In **operation** everything runs locally on your vehicle's network, without internet. You only need a connection for remote access and for push notifications to your phone.

### Do I need a BB-Display?

Yes. The integration connects BlueBattery devices via the BB-Display – it collects the data of all paired devices and sends it to Home Assistant. Without a BB-Display the integration does not work (yet).

### Which data arrives in Home Assistant?

Everything the BB-Display forwards from the paired devices:

- **Battery computer:** state of charge, voltage, current, power, solar, booster, starter battery, charging phases, energy counters
- **Tanks:** level in % and litres, capacity, tank type, tilt (longitudinal and lateral)
- **Temperature sensors:** temperature, humidity, battery
- **BB-Display itself:** indoor temperature, humidity, dew point, connection
- **Heater:** see [Heater control](heating.md)

### Why do I see only one battery computer?

The BB-Display forwards exactly **one** battery computer – the one selected on the display.

### How accurate is the shore power energy?

The display calculates it from battery, solar and booster current – a good guide value, even without a dedicated shore power meter. All energy counters start fresh every day; Home Assistant continues them seamlessly in the [energy dashboard](examples.md#energy-dashboard).

### What happens after a restart?

- **Home Assistant restarted:** the last known values are available immediately. The display counts as *connected* as soon as it sends fresh data again.
- **Display restarted:** the heater gets 1–2 minutes to reconnect before a fault is reported.
- **Temperature sensor failed:** if the display no longer reports a valid value, the integration shows "unknown" instead of an outdated value.

### How do I open the display's settings page later?

Settings → Devices & services → BlueBattery → **BB-Display**. The device page has a link straight to the display's settings page. The display reports its address itself – the link stays correct even if the router assigns a new one. Incidentally, Home Assistant does not need the display's address for operation: the display connects to Mosquitto on its own.

---

## Troubleshooting

### The ⇄ symbol is missing on the display

The display is not connected to the broker. In the display's web interface under Remote access → MQTT, check:
- **Server** = IP address of your Home Assistant, **port** `1883`,
- **user and password** as created in [step 3](setup.md#step-3--create-a-user-for-the-display),
- is the **Mosquitto app** running (Settings → Apps → Mosquitto broker)?

If the user was just created and login fails, **restart the Mosquitto app** once.

### BlueBattery does not appear under "Discovered"

- Does the display show the ⇄ symbol? If not: see above.
- Is the integration installed via HACS and was Home Assistant **restarted** afterwards?
- Manual setup: Settings → Devices & services → **Add integration** → "BlueBattery" → enter the topic from the display (factory default `BlueBattery/BB-Display`).

### A device is missing from the selection

The integration only lists devices that are **paired with the BB-Display** and currently reported by it. Pair the device with the display (or select it as battery computer), check the range, then open **Configure** again in Home Assistant.

### All values are "unavailable"

The display is not sending data right now – e.g. because it is switched off or out of Wi-Fi range. As soon as it sends again, the values reappear on their own. The integration deliberately shows "unavailable" instead of old values, so you can rely on what you see.

### I see all values twice

The display's built-in Home Assistant support is still switched on. On the display, under MQTT, switch **"Home Assistant"** off – see [Migration](migration.md).

### Old devices remain after switching off the built-in support

Some devices (seen with BB-Tank and BlueLevel) do not clean up their old entries in the broker themselves. Fix: with [MQTT Explorer](https://mqtt-explorer.com), delete the device's entries under `homeassistant/…` – the devices then disappear from Home Assistant.

### HACS reports "Failed to download … 404"

An identifier like `21ff56e` was selected instead of a version. **HACS → BlueBattery → ⋮ → Redownload** and choose the latest version `v…`.

### "Open directly" doesn't work

See [If "Open directly" doesn't work](setup.md#if-open-directly-doesnt-work). The menu path is written before it in each step.

### How do I report a bug?

**Settings → Devices & services → BlueBattery → ⋮ → Download diagnostics** (addresses are redacted) and attach the file to an [issue on GitHub](https://github.com/sahomm/BlueBattery/issues).

---

## Advanced

### Home Assistant Container or Core

There are no apps there. You need your own MQTT broker (e.g. Mosquitto as a Docker container) and set up the MQTT integration with its address. You create user and password in the broker.

### Watching MQTT messages

In the MQTT integration: **Configure → Listen to a topic** → `BlueBattery/#` → Start listening. A message should arrive every 30 seconds (depending on the display setting). [MQTT Explorer](https://mqtt-explorer.com) gives a clearer overview.

### How does the data reach Home Assistant?

```
Battery computer ──┐
BlueLevel/BB-Tank ─┼─ Bluetooth ──► BB-Display ◄── Wi-Fi / MQTT ──► Home Assistant
Xiaomi/RuuviTag ───┘                    ▲                           (Mosquitto + BlueBattery)
                                        │ cable
                  Truma/Alde ── TIN adapter
```

The devices send via Bluetooth to the BB-Display or are connected through the TIN adapter. The display forwards everything via Wi-Fi/MQTT to Home Assistant and receives heater commands from there. For tanks it forwards level, volume, tilt and signal; diagnostic values of the tank sensors themselves (e.g. distance to the water surface) are not forwarded.

Technical details: [Architecture](../ARCHITEKTUR.md) (German)
