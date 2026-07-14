"""The Tinxy Local integration."""

from __future__ import annotations

import os
import stat
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_DEVICE, CONF_MQTT_PASS, CONF_POLLING_INTERVAL, CONF_REQUEST_TIMEOUT, DEFAULT_POLLING_INTERVAL, DEFAULT_REQUEST_TIMEOUT, DOMAIN
from .coordinator import TinxyUpdateCoordinator
from .hub import TinxyLocalHub

_LOGGER = logging.getLogger(__name__)

# List the platforms that this integration will support.
PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.FAN, Platform.LOCK]


def _set_executable_permissions(directory: str):
    """Ensure all files in the directory are executable."""
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if not os.access(file_path, os.X_OK):
                current_perms = os.stat(file_path).st_mode
                os.chmod(file_path, current_perms | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tinxy from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # Set executable permissions for files in the build directory
    integration_path = hass.config.path("custom_components/tinxylocal/build")
    if os.path.exists(integration_path):
        _LOGGER.info("Setting executable permissions for files in %s", integration_path)
        await hass.async_add_executor_job(_set_executable_permissions, integration_path)
    else:
        _LOGGER.warning("Build directory does not exist: %s", integration_path)

    web_session = async_get_clientsession(hass)

    # Get request timeout from options or use default
    request_timeout = entry.options.get(CONF_REQUEST_TIMEOUT, DEFAULT_REQUEST_TIMEOUT)
    
    # Get polling interval from options or use default
    polling_interval = entry.options.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)

    # Extract device configurations
    device_data = entry.data[CONF_DEVICE]
    device_id = device_data["_id"]
    suffix = device_id[-5:].lower()
    service_name = f"tinxy{suffix}._http._tcp.local."
    
    current_ip = entry.data[CONF_HOST]
    
    try:
        from homeassistant.components import zeroconf
        _LOGGER.debug("Tinxy: Resolving IP address via Zeroconf for device %s at startup", device_id)
        aiozc = await zeroconf.async_get_instance(hass)
        info = await aiozc.async_get_service_info("_http._tcp.local.", service_name)
        if info and info.addresses:
            resolved_ip = ".".join(map(str, info.addresses[0]))
            if resolved_ip != current_ip:
                _LOGGER.info("Tinxy: Resolved new IP address %s via Zeroconf for %s (previous: %s)", resolved_ip, device_data["name"], current_ip)
                current_ip = resolved_ip
                new_data = {**entry.data, CONF_HOST: resolved_ip}
                hass.config_entries.async_update_entry(entry, data=new_data)
    except Exception as err:
        _LOGGER.warning("Tinxy: Zeroconf resolution failed at startup for %s: %s", device_data["name"], err)

    # Build list of devices/relays belonging to this node
    node_devices = []
    if device_data.get("devices"):
        node_devices = [
            {"name": dev_name, "type": dev_type}
            for dev_name, dev_type in zip(
                device_data["devices"], device_data["deviceTypes"], strict=False
            )
        ]
    else:
        gtype = device_data.get("typeId", {}).get("gtype", "")
        model = device_data.get("typeId", {}).get("name", "")
        if gtype == "action.devices.types.LOCK":
            dev_type = "Lock"
        elif model in ("EVA_BULB", "WIFI_BULB_WHITE_V1", "Dimmable Light"):
            dev_type = "Light"
        elif model in ("WIFI_SWITCH_1FAN_V1", "Fan"):
            dev_type = "Fan"
        else:
            dev_type = "Switch"
        node_devices = [{"name": device_data["name"], "type": dev_type}]

    nodes = [
        {
            "ip_address": current_ip,
            "mqtt_password": entry.data[CONF_MQTT_PASS],
            "device_id": device_data["_id"],
            "name": device_data["name"],
            "model": device_data["typeId"]["name"],
            "unique_id": device_data["_id"],
            "devices": node_devices,
        }
    ]

    # Initialize TinxyLocalHub instances for each node
    hubs = [TinxyLocalHub(hass, node["ip_address"], request_timeout) for node in nodes]

    # Initialize the coordinator with the list of nodes and web session
    coordinator = TinxyUpdateCoordinator(hass, nodes, hubs, web_session, polling_interval)
    coordinator.config_entry = entry

    # Store the coordinator and hubs in Home Assistant's data store
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "hubs": hubs}

    # Forward the entry setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id not in hass.data[DOMAIN]:
        return True

    # Shutdown all hubs to stop background workers
    hubs = hass.data[DOMAIN][entry.entry_id]["hubs"]
    for hub in hubs:
        await hub.shutdown()
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
