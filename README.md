# Tinxy Local Home Assistant Integration

> [!WARNING]
> **Disclaimer:** This is an unofficial, community-developed integration and is not affiliated with or endorsed by Tinxy. This integration relies on local APIs and is currently in beta. Please be prepared for potential troubleshooting.

Welcome to the **tinxy-local** integration for Home Assistant! This integration allows you to control your Tinxy switches, fans, and locks directly over your local Wi-Fi network, ensuring fast response times and privacy.

**Credits**: Original foundation and creation by [@arevindh](https://github.com/arevindh). Please note that this specific repository contains community updates built on top of their work and is **not** maintained by the original author.

---

## ✨ Features

- **Local Control:** Controls devices directly via HTTP over your local network. No cloud dependence for toggling!
- **Zero-Touch Auto-Provisioning:** Once your first device is configured, any new Tinxy devices added to your Wi-Fi are automatically discovered via mDNS, configured, and added to your dashboard with zero clicks required!
- **Hardware Configuration Sync:** Control native hardware settings directly from Home Assistant! Toggles for **Restore State on Power**, **Green Status LED**, and **Push Notifications** are exposed as hidden configuration entities on your device page, dynamically syncing with the Tinxy Cloud.
- **Optimistic State Updates:** Snappy UI feedback. Toggles instantly reflect in Home Assistant without waiting for redundant polling requests, minimizing network load on your switches.
- **Auto-Discovery (Zeroconf):** IP addresses are automatically resolved and updated dynamically if your router changes them.

---

## 🛠️ Prerequisites

1. **Home Assistant Community Store (HACS)**: Ensure HACS is installed in your Home Assistant setup.
2. **API Key**: You will need a Tinxy Cloud API key to fetch the initial device metadata during setup.

---

## 🚀 Installation

### Step 1: Install via HACS
1. Go to **HACS** in your Home Assistant UI.
2. Click **Integrations** -> **Custom repositories** (three dots in top right).
3. Add the repository URL: `https://github.com/waytosahil/tinxylocal` as an Integration.
4. Click **Download** and install the integration.
5. **Restart Home Assistant**.

### Step 2: Configure Your First Device
1. Navigate to **Settings** > **Devices & Services** in Home Assistant.
2. Click **Add Integration** and search for **tinxy-local**.
3. **API Key Prompt**: Enter your Tinxy API key. This is required to fetch your device configuration from the cloud securely.
4. **Device Selection**: The integration will retrieve a list of devices associated with your account. Select the specific device you wish to configure.
5. **Automatic IP Resolution:** The integration will automatically discover and resolve the local IP address of the selected device on your Wi-Fi network using Zeroconf (mDNS). No manual IP inputs are required!

### Step 3: Zero-Touch Auto-Provisioning (For Additional Devices)
Once you have configured your first device (and saved your API token in Home Assistant), adding more devices is entirely automated!
1. Set up your new Tinxy module in the official Tinxy mobile app and connect it to your Wi-Fi.
2. That's it! Home Assistant will automatically intercept its mDNS broadcast, fetch its configuration from the cloud using your saved token, and silently provision it to your dashboard.

---

## 🛑 Troubleshooting

### Local API Freezes or Timeouts
The tiny microcontrollers inside Tinxy switches have a limited capacity for handling network requests. We have highly optimized this integration to prevent socket exhaustion, but if a device fails to respond:
- **Avoid rapid toggling:** Spamming the switch in Home Assistant can overwhelm the local ESP web server.
- **Fix:** If it freezes, try power cycling or resetting the physical device at the wall switch.
- **Increase Polling Interval:** If you have many devices, consider clicking "Configure" on the integration in Home Assistant and increasing the polling interval from 6 seconds to 15 seconds to reduce background network noise.

### Manual Reset
If the integration fails critically or gets stuck in a bad state:
1. Access your Home Assistant installation's `custom_components/tinxylocal` directory (e.g., via Samba or File Editor).
2. Delete the `tinxylocal` folder.
3. Reboot Home Assistant and reinstall via HACS.

---
*Built with ❤️ for the Home Assistant community.*
