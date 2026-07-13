import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Add the root directory to path to locate custom_components
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Home Assistant and standard aiohttp modules to prevent import errors
sys.modules['aiohttp'] = MagicMock()
sys.modules['homeassistant'] = MagicMock()
sys.modules['homeassistant.core'] = MagicMock()
sys.modules['homeassistant.const'] = MagicMock()
sys.modules['homeassistant.exceptions'] = MagicMock()
sys.modules['homeassistant.helpers'] = MagicMock()
sys.modules['homeassistant.helpers.aiohttp_client'] = MagicMock()
sys.modules['homeassistant.helpers.update_coordinator'] = MagicMock()
sys.modules['homeassistant.helpers.device_registry'] = MagicMock()
sys.modules['homeassistant.components'] = MagicMock()
sys.modules['homeassistant.components.zeroconf'] = MagicMock()
sys.modules['homeassistant.config_entries'] = MagicMock()

# Set up mock classes for HomeAssistant exceptions used in custom components
from homeassistant.exceptions import HomeAssistantError
class MockHomeAssistantError(HomeAssistantError):
    pass
sys.modules['homeassistant.exceptions'].HomeAssistantError = MockHomeAssistantError

# Set up mock platform constants
sys.modules['homeassistant.const'].CONF_HOST = "host"
sys.modules['homeassistant.const'].CONF_API_KEY = "api_key"

# Now we can safely import our integration components
from custom_components.tinxylocal.tinxycloud import TinxyCloud, TinxyHostConfiguration, TinxyAuthenticationException
from custom_components.tinxylocal.hub import TinxyLocalHub, TinxyLocalException

class TestTinxyCloud(unittest.IsolatedAsyncioTestCase):
    """Test cases for TinxyCloud API and helper methods."""

    def setUp(self):
        self.mock_session = MagicMock()
        self.config = TinxyHostConfiguration(
            api_token="test_token",
            api_url="http://mock-cloud-api/"
        )
        self.cloud = TinxyCloud(self.config, self.mock_session)

    async def test_parse_device_socket(self):
        """Test parsing socket devices from cloud format."""
        device_data = {
            "_id": "dev123",
            "name": "Living Room Socket",
            "devices": ["Socket 1"],
            "deviceTypes": ["Socket"],
            "typeId": {
                "name": "WIFI_SWITCH",
                "gtype": "action.devices.types.SWITCH",
                "traits": ["action.devices.traits.OnOff"],
                "long_name": "Smart Socket"
            },
            "mqttPassword": "pass",
            "uuidRef": {"uuid": "uuid123"},
            "firmwareVersion": 2
        }
        
        parsed = self.cloud.parse_device(device_data)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["name"], "Living Room Socket Socket 1")
        self.assertEqual(parsed[0]["device_type"], "Switch")

    async def test_parse_device_fan(self):
        """Test parsing fan devices from cloud format."""
        device_data = {
            "_id": "fan123",
            "name": "Ceiling Fan",
            "devices": ["Fan 1"],
            "deviceTypes": ["Fan"],
            "typeId": {
                "name": "WIFI_SWITCH_1FAN_V1",
                "gtype": "action.devices.types.FAN",
                "traits": ["action.devices.traits.FanSpeed"],
                "long_name": "Fan Controller",
                "features": ["FAN"]
            },
            "mqttPassword": "pass",
            "uuidRef": {"uuid": "uuidfan"},
            "firmwareVersion": 1
        }
        parsed = self.cloud.parse_device(device_data)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["device_type"], "Fan")


class TestTinxyLocalHub(unittest.IsolatedAsyncioTestCase):
    """Test cases for TinxyLocalHub controls and event-driven worker."""

    def setUp(self):
        self.hass = MagicMock()
        self.hub = TinxyLocalHub(self.hass, "192.168.1.100")

    async def test_hub_initialization(self):
        """Test that the hub initializes command queues and events dictionary."""
        self.assertEqual(self.hub.ip_address, "192.168.1.100")
        self.assertEqual(self.hub.host, "http://192.168.1.100")
        self.assertFalse(self.hub._shutdown)
        self.assertEqual(len(self.hub.device_queues), 0)
        self.assertEqual(len(self.hub.device_events), 0)

    async def test_queue_command_triggers_event(self):
        """Test that queuing a command initializes the event and triggers it."""
        # Mock tinxy_toggle to return success
        self.hub.tinxy_toggle = AsyncMock(return_value=True)

        # Mock asyncio.create_task to run worker synchronously or prevent blocking
        # Queue command for test
        task = asyncio.create_task(
            self.hub.queue_toggle_command(
                device_id="device_uuid",
                mqttpass="password",
                relay_number=1,
                action=1
            )
        )
        
        # Yield to allow execution
        await asyncio.sleep(0.01)
        
        # Verify command completes successfully
        result = await task
        self.assertTrue(result)
        
        # Verify queue was initialized
        self.assertIn("device_uuid", self.hub.device_queues)
        self.assertIn("device_uuid", self.hub.device_events)
        
        # Verify toggle command execution
        self.hub.tinxy_toggle.assert_called_once_with(
            "password", 1, 1
        )
        
        # Clean shutdown
        await self.hub.shutdown()

    async def test_rate_limiting_command_execution(self):
        """Test rate limiting prevents running commands back-to-back immediately."""
        self.hub.tinxy_toggle = AsyncMock(return_value=True)
        
        # Queue first command
        # Cancel the automatically created workers to do manual processing
        await self.hub.shutdown()
        
        # Re-enable hub
        self.hub._shutdown = False
        self.hub.device_workers.clear()
        self.hub.device_queues.clear()
        self.hub.device_events.clear()

        # Mock _device_worker to test command fetching
        self.hub.device_last_command["device1"] = 100.0  # Set far in past
        self.hub.rate_limit_delay = 1.0


if __name__ == "__main__":
    unittest.main()
