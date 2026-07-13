"""Tinxy Node Update Coordinator."""

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .hub import TinxyConnectionException, TinxyLocalException, TinxyLocalHub

_LOGGER = logging.getLogger(__name__)
REQUEST_REFRESH_DELAY = 0.50


class TinxyUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data directly from Tinxy nodes."""

    device_metadata: dict[str, dict[str, Any]]
    nodes: list[dict[str, Any]]

    def __init__(
        self, hass: HomeAssistant, nodes: list[dict[str, Any]], web_session, default_polling_interval: int = 5
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Tinxy Nodes",
            update_interval=timedelta(seconds=default_polling_interval),
        )
        self.hass = hass
        self.nodes = nodes  # Type-annotated as a list of dictionaries
        self.web_session = web_session
        self.hubs = [TinxyLocalHub(hass, node["ip_address"]) for node in nodes]
        self.device_metadata = {}  # Type-annotated as a dictionary

    async def _async_resolve_zeroconf(self, device_id: str) -> str | None:
        """Resolve a device ID to an IP address using Home Assistant's Zeroconf helper."""
        from homeassistant.components import zeroconf
        
        # Suffix is the last 5 characters of the device ID (e.g. chip ID suffix)
        suffix = device_id[-5:].lower()
        service_name = f"tinxy{suffix}._http._tcp.local."
        
        _LOGGER.debug("Resolving Zeroconf service %s", service_name)
        try:
            aiozc = await zeroconf.async_get_instance(self.hass)
            info = await aiozc.async_get_service_info("_http._tcp.local.", service_name)
            if info and info.addresses:
                new_ip = ".".join(map(str, info.addresses[0]))
                return new_ip
        except Exception as err:
            _LOGGER.debug("Zeroconf resolution failed for %s: %s", service_name, err)
        return None

    async def _async_update_data(self):
        """Fetch data from each configured Tinxy node in parallel."""
        status_list = {}

        async def fetch_one(hub, node):
            device_data = None
            try:
                device_data = await hub.fetch_device_data(node, self.web_session)
            except (TinxyConnectionException, TinxyLocalException) as conn_err:
                _LOGGER.warning(
                    "Connection error for node %s: %s. Attempting Zeroconf resolution.",
                    node["name"], conn_err
                )
                try:
                    new_ip = await self._async_resolve_zeroconf(node["device_id"])
                    if new_ip and new_ip != hub.ip_address:
                        _LOGGER.info(
                            "Resolved new IP %s for node %s via Zeroconf. Updating host.",
                            new_ip, node["name"]
                        )
                        hub.ip_address = new_ip
                        hub.host = f"http://{new_ip}"
                        node["ip_address"] = new_ip
                        
                        if hasattr(self, "config_entry") and self.config_entry:
                            new_data = {**self.config_entry.data, "host": new_ip}
                            self.hass.config_entries.async_update_entry(
                                self.config_entry, data=new_data
                            )
                        
                        # Retry fetch with the new IP address
                        device_data = await hub.fetch_device_data(node, self.web_session)
                except Exception as resolve_err:
                    _LOGGER.error("Failed during Zeroconf recovery for %s: %s", node["name"], resolve_err)
            
            if device_data:
                return node["device_id"], device_data
            return None

        # Execute all fetches in parallel
        tasks = [fetch_one(hub, node) for hub, node in zip(self.hubs, self.nodes, strict=False)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                _LOGGER.error("Unexpected exception during concurrent device update: %s", result)
                continue
            if isinstance(result, tuple) and len(result) == 2:
                device_id, device_data = result
                status_list[device_id] = device_data
                # Populate device metadata for other information (firmware, model, etc.)
                self.device_metadata[device_id] = {
                    "firmware": device_data.get("firmware", "Unknown"),
                    "model": device_data.get("model", "Tinxy Smart Device"),
                    "rssi": device_data.get("rssi"),
                    "ssid": device_data.get("ssid"),
                    "ip": device_data.get("ip"),
                    "version": device_data.get("version"),
                    "door": device_data.get("door"),
                }

        # Set `self.data` to `status_list` so entities can access it
        self.data = status_list
        _LOGGER.debug("Coordinator data updated: %s", self.data)

        # Call the device registration method after the initial data fetch
        await self._register_devices()
        return status_list

    async def _register_devices(self):
        """Register devices in the Home Assistant device registry after data is loaded."""
        device_registry = dr.async_get(self.hass)
        for node in self.nodes:
            metadata = self.device_metadata.get(node["device_id"], {})
            firmware_version = metadata.get("firmware", "Unknown")
            model = metadata.get("model", "Tinxy Smart Device")

            # Only use identifiers without connections
            device_registry.async_get_or_create(
                config_entry_id=self.config_entry.entry_id,
                identifiers={(DOMAIN, node["device_id"])},
                name=node["name"],
                manufacturer="Tinxy",
                model=model,
                sw_version=str(firmware_version) if firmware_version is not None else None,
            )
