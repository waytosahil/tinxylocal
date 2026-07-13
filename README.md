
# Tinxy Local Home Assistant Integration (Beta) Installation Guide

This guide will help you set up the **tinxy-local** integration for Home Assistant. Since this integration is in beta, please carefully follow each step and be prepared for potential troubleshooting.

Join [Discord server](https://discord.gg/VH4jgz2f) for support.

## Prerequisites

1. **Home Assistant Community Store (HACS)**: Ensure HACS is installed in your Home Assistant setup. HACS is required to add third-party custom integrations.
2. **API Key**: Obtain an API key for the tinxy-local integration.

## Installation Steps

### Step 1: Install the Tinxy-Local Integration

1. Open the [ tinxy-local GitHub repository ](https://github.com/arevindh/tinxylocal).
2. **Add to HACS**:
   - Go to HACS in your Home Assistant UI.
   - Add the tinxy-local integration by entering the repository URL `https://github.com/arevindh/tinxylocal`.
   - Follow the prompts to complete the installation.
   - **Restart Home Assistant** to ensure the new integration loads properly.

### Step 2: Configure Each Device with the Tinxy-Local Integration

For each device you want to add:

1. **Add the Device Using the Tinxy Integration**:
   - Navigate to **Settings** > **Devices & Services** in Home Assistant.
   - Click **Add Integration** and search for **tinxy-local**.
   - When prompted, enter the API key to link the device with the integration (If you have an existing device, you can choose to use the existing token).

### Prompt Details for Tinxy Local Integration

When setting up each device with the **tinxy-local** integration, you’ll encounter a series of prompts that guide you through the setup. Here’s what to expect:

1. **API Key Prompt**:
   - The first prompt will ask you to enter your **API key**.
   - This key is required to link your Home Assistant instance with your Tinxy account.
   
2. **Device Selection Prompt**:
   - After entering the API key, the integration will retrieve a list of devices associated with your account.
   - You will be prompted to **select a device** from this list. Choose the specific device you wish to configure.
   - **Automatic Discovery:** The integration will automatically discover and resolve the local IP address of the selected device on your Wi-Fi network using Zeroconf (mDNS). No manual IP inputs are required!

These prompts ensure that each device is correctly authenticated, selected, and connected over your local network. Repeat this process for each additional device you wish to add.

### Step 3: Local Connection Troubleshooting

1. **Local API Connection Troubleshooting**:
   - If the device fails to toggle or respond correctly, avoid rapid repeated toggling as this can cause the local API to freeze. If toggling fails after multiple attempts, try power cycling or resetting your device.


### Step 4: Troubleshooting

1. **Access to Samba**:
   - Ensure that you have Samba or another file access method enabled to manually modify files if necessary.
2. **Manual Reset**:
   - If the integration fails for any device, you may need to manually delete the tinxy-local files:
     - Access your Home Assistant installation’s `custom_components` directory.
     - Remove any existing tinxy-local files.
     - Reboot Home Assistant.

---

This guide provides the installation and configuration steps for each device with the tinxy-local integration. Since it’s in beta, you may encounter issues; consult the developer or community for additional support if necessary.
