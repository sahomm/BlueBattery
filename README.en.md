# BlueBattery for Home Assistant

[🇩🇪 Deutsch](https://github.com/sahomm/BlueBattery/blob/main/README.md) | 🇬🇧 English

<p align="center">
  <img src="https://raw.githubusercontent.com/sahomm/BlueBattery/main/custom_components/bluebattery/brand/icon.png" alt="BlueBattery" width="96">
  &nbsp;&nbsp;
  <img src="https://raw.githubusercontent.com/sahomm/BlueBattery/main/images/produkt-bb-display.png" alt="BB-Display with Wi-Fi and MQTT" width="260">
</p>

Bring your motorhome or caravan into **Home Assistant**: battery and solar, tanks, temperatures and the **heater (Truma/Alde)** – all via the **[BB-Display](https://www.blue-battery.com/product-page/bb-display)** by [BlueBattery](https://www.blue-battery.com). The integration finds your BB-Display automatically and takes over all devices paired with it.

<p align="center">
  <img src="https://raw.githubusercontent.com/sahomm/BlueBattery/main/images/integration-geraete.png" alt="BlueBattery in Home Assistant: BB-Display with all paired devices" width="560">
  <br><em>One BB-Display with battery computer, tanks, temperature sensors and Truma</em>
</p>

> **Requirement: a BB-Display.** The integration connects BlueBattery devices exclusively **via the BB-Display** – battery computer, BlueLevel/BB-Tank, temperature sensors and Truma/Alde via the TIN adapter. **Without a BB-Display the integration does not work (yet).**

## What you can do with it

The BlueBattery app shows you everything. With Home Assistant **your vehicle reacts** – even when nobody is on board. For each example there is a ready-made template you can import with one click.

| | Use case | You need |
|---|---|---|
| 🔥 | **[Push on heater fault](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md#heater-fault-notification)** – with error code, even if the display goes offline | BB-Display + [TIN adapter](https://www.blue-battery.com/product-page/tin-adapter) |
| ❄️ | **[Frost protection](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md#frost-protection)** – warning, and the heater switches on automatically | BB-Display + TIN adapter |
| ♨️ | **[Pre-heating](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md#pre-heating)** – at a set time or with one tap while on the way | BB-Display + TIN adapter |
| 🧊 | **[Fridge & freezer](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md#fridge-and-freezer)** – warning before anything thaws | BB-Display + temperature sensor (Xiaomi, RuuviTag) |
| 🚰 | **[Tank warning](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md#tank-warning)** – grey water full, fresh water low | BB-Display + [BlueLevel / BB-Tank](https://www.blue-battery.com/product-page/bluelevel) |
| 📐 | **[Spirit level](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md#spirit-level)** – bubble level and cm per wheel when parking | BB-Display + BlueLevel / BB-Tank |
| 🔋 | **[Battery warning](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md#battery-warning)** – house and starter battery at a glance | BB-Display + [battery computer](https://www.blue-battery.com/produkte) |
| ☀️ | **[Energy dashboard](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md#energy-dashboard)** – solar yield and consumption over weeks | BB-Display + battery computer |

All examples: **[Practical examples](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md)**

## What you need

- ✅ a **BB-Display** on your vehicle's Wi-Fi, with your BlueBattery devices paired
- ✅ **Home Assistant** (easiest: Home Assistant OS, e.g. on a Raspberry Pi in the vehicle – [official guide](https://www.home-assistant.io/installation/))
- ✅ **HACS** – a kind of "app store for add-on software" in Home Assistant ([how to install HACS](https://hacs.xyz/docs/use/); you need a free GitHub account for it)
- ✅ about **30 minutes**

> **Internet:** You need internet for the **setup** (downloading apps, HACS and the integration). In **operation** everything runs locally on your vehicle's network – without internet. Only remote access and push notifications need a connection.

## Setup in 7 steps

In full detail: **[Step-by-step setup](https://github.com/sahomm/BlueBattery/blob/main/docs/en/setup.md)**.

> **Tip:** Some steps have a link **"Open directly ↗"**. It opens the matching page in your Home Assistant via [my.home-assistant.io](https://my.home-assistant.io). The first time, the page asks once for the address of your Home Assistant (e.g. `http://homeassistant.local:8123`) and after that briefly for "Open link" each time – this is a security check. The menu path always leads to the same place.

**1. Pair devices with the BB-Display** – Home Assistant only sees what the display knows.

Select the battery computer, pair and name tank and temperature sensors, set up the TIN adapter.

✅ The display shows the values of your devices.

**2. Install Mosquitto** – Mosquitto is the "post office": the display drops off its values there and Home Assistant picks them up. The app is already included in the app store.

Settings → Apps → App store → "Mosquitto broker" → Install → enable "Start on boot" and "Watchdog" → Start. [Open directly ↗](https://my.home-assistant.io/redirect/supervisor_addon/?addon=core_mosquitto)

✅ Mosquitto shows "Running".

**3. Create a user for the display** – so the display is allowed to drop off values at Mosquitto.

Settings → People → Add person → "Allow login" → set username and a strong password → "Local access only", not an administrator → Create. [Open directly ↗](https://my.home-assistant.io/redirect/people/)

📝 Write down username and password – you need both in step 5.

✅ The new person appears in the list.

**4. Set up the MQTT integration** – MQTT is the "language" in which the display, Mosquitto and Home Assistant talk to each other.

Settings → Devices & services → under "Discovered" **MQTT** → Configure → confirm. [Open directly ↗](https://my.home-assistant.io/redirect/config_flow_start/?domain=mqtt)

✅ Devices & services shows an **MQTT** tile.

**5. Connect the BB-Display to Home Assistant** – the display gets the address of Home Assistant and the login from step 3.

1. Open the display's settings page in a browser. You find the display's address in your router's device list or as described in the [display manual](https://www.blue-battery.com/product-page/bb-display).
2. **Settings → Remote access → MQTT**: **Server** = IP address of your Home Assistant (in Home Assistant under Settings → System → Network), **Port** `1883`, **user/password** from step 3, leave the **topic** unchanged, switch **"Home Assistant" off** → Save.

✅ The ⇄ symbol appears at the top of the display.

**6. Install BlueBattery via HACS** – easiest with this button: it opens BlueBattery directly in HACS and adds the repository itself after a confirmation. Then **Download** → restart Home Assistant.

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sahomm&repository=BlueBattery&category=integration)

<details>
<summary>Button not working? The manual way</summary>

HACS → ⋮ (top right) → Custom repositories → `https://github.com/sahomm/BlueBattery`, type **Integration** → Add. Then search for **BlueBattery** → Download → restart Home Assistant.
</details>

✅ Home Assistant is reachable again after the restart.

**7. Set up BlueBattery** – by now Home Assistant has found your display on its own.

Settings → Devices & services → under "Discovered" **BlueBattery – BB-Display** → Configure → select devices → Done. [Open directly ↗](https://my.home-assistant.io/redirect/config_flow_start/?domain=bluebattery)

✅ Devices & services → BlueBattery lists your display and all devices – like in the picture above.

🎉 **Done!** Later you simply pair new devices on the display – Home Assistant then offers them for adding. And with the [practical examples](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md) you get notifications on your phone next.

## Supported devices

All devices come **via the BB-Display**.

| Device | Connection to the BB-Display | Status |
|---|---|---|
| BB-Display itself (indoor temperature, humidity, dew point) | – | ✅ |
| Battery computers (BBX200/400 Pro, D1/D2, X200/X300, BBX400, Basic) | Bluetooth, selected on the display | ✅ |
| BlueLevel / BlueLevel+, BB-Tank | Bluetooth, paired with the display | ✅ |
| Temperature sensors Xiaomi LYWSD03MMC, RuuviTag | Bluetooth, paired with the display | ✅ |
| Truma Combi (CP plus iNet ready) | TIN adapter | ✅ |
| Alde Compact 3020 HE / 3030 | TIN adapter | 🧪 experimental |

## Learn more

- **[Practical examples](https://github.com/sahomm/BlueBattery/blob/main/docs/en/examples.md)** – templates to import
- **[Step-by-step setup](https://github.com/sahomm/BlueBattery/blob/main/docs/en/setup.md)** – in detail, with all settings
- **[Heater control](https://github.com/sahomm/BlueBattery/blob/main/docs/en/heating.md)** – Truma and Alde
- **[Questions & answers](https://github.com/sahomm/BlueBattery/blob/main/docs/en/faq.md)** – including troubleshooting
- **[Migrating from the built-in support](https://github.com/sahomm/BlueBattery/blob/main/docs/en/migration.md)** – keep your history
- **[What is BlueBattery?](https://www.blue-battery.com)** – the manufacturer's products and forum

## Contributing

- Bugs and feature requests: [GitHub Issues](https://github.com/sahomm/BlueBattery/issues) – ideally with a **diagnostics export** (Devices & services → BlueBattery → ⋮ → Download diagnostics; addresses are redacted).
- **Alde owners wanted:** if you have an Alde with TIN adapter, a diagnostics export helps a lot.
- Technical background: [Architecture](https://github.com/sahomm/BlueBattery/blob/main/docs/ARCHITEKTUR.md) (German)

This project is developed by [sahomm](https://github.com/sahomm) in coordination with the BlueBattery developer and with support from Claude (Anthropic).

## Legal notice

- **Community project:** The integration is developed in coordination with the BlueBattery developer, but it is not an official BlueBattery product. BlueBattery logo and product images © BlueBattery, used with kind permission. For questions about the devices themselves: [blue-battery.com](https://www.blue-battery.com) and the [BlueBattery forum](https://www.blue-battery.com/groups).
- **No affiliation with heater or device manufacturers:** This project is **not affiliated** with Truma Gerätetechnik GmbH & Co. KG, Alde International Systems AB or any other manufacturer mentioned here (including Xiaomi, Ruuvi). It is not supported, reviewed or endorsed by them.
- **Trademarks for description only:** Names such as *Truma*, *Combi*, *CP plus*, *iNet*, *Alde*, *Xiaomi*, *RuuviTag*, *Home Assistant* or *Raspberry Pi* are trademarks or product names of their respective owners. They are used solely to describe **which devices** the integration works with. **No logos** of these manufacturers are used.
- **Heater control:** The heater is addressed via BlueBattery's BB-Display and TIN adapter, not via interfaces or software of the heater manufacturers. Use at your own risk. For warranty, guarantee and operation of the heater, only its manufacturer or dealer is responsible; please check heater faults on the heater's control panel first.
- **Liability:** The software is provided without warranty (see [License](#license)). It does not replace on-site supervision – especially not for frost protection.

## License

[MIT](https://github.com/sahomm/BlueBattery/blob/main/LICENSE)
