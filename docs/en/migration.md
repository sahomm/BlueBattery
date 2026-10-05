# Migrating from the built-in Home Assistant support

[🇩🇪 Deutsch](../de/umstieg.md) | 🇬🇧 English · [← back to overview](../../README.en.md)

The BB-Display comes with its own simple Home Assistant support (switch **"Home Assistant"** on the display under Settings → Remote access → MQTT). This integration replaces it. **Running both results in duplicate values** – so switch the built-in support off.

## Fresh start (recommended)

If previous history doesn't matter:

1. On the display, under **Settings → Remote access → MQTT**, switch **"Home Assistant" off** – the old entries disappear from Home Assistant.
2. Install the integration following the [setup](setup.md).

## Keep history

The integration can take over the existing entity IDs – dashboards, automations and history simply keep working:

1. Set up the integration (values appear twice for a while).
2. **Settings → Devices & services → BlueBattery → Configure → Migration: prepare** – check the list and save.
3. On the display, under **Settings → Remote access → MQTT**, switch **"Home Assistant" off** and wait one minute.
4. **Configure → Migration: finish.**

Values that exist as a different type in the integration (e.g. "booster limit" now as a sensor instead of an on/off value) are not taken over.

## Other BlueBattery devices with their own support

BB-Tank and BlueLevel also have a "Home Assistant" or "MQTT Discovery" switch. Switch it off if the device is paired with the BB-Display – otherwise values appear twice. For devices that do **not** come via the display (e.g. a second battery computer), leave it on.

If old devices remain in Home Assistant after switching it off, see the [FAQ](faq.md#old-devices-remain-after-switching-off-the-built-in-support).
