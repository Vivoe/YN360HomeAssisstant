"""YN360 Light integration for Home Assistant."""

import logging

from bleak import BleakClient

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PAYLOAD_FLUSH, PAYLOAD_OFF, PAYLOAD_ON_DEFAULT

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> bool:
    """Set up the YN360 light platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]

    ble_client = async_ble_device_from_address(hass, config["uuid"])
    async_add_entities([YN360Light(ble_client, config["control_uuid"])])
    return True


class YN360Light(LightEntity):
    """YN360 light entity."""

    def __init__(self, ble_client, control_uuid) -> None:
        """Initialize the light."""
        self._name = "YN360"
        self._ble_client = ble_client
        self._control_uuid = control_uuid
        self._state_payload = PAYLOAD_ON_DEFAULT

    async def send_payload(self, payloads):
        """Send a hex payload to the device."""
        if not isinstance(payloads, list):
            payloads = [payloads]

        for payload in payloads:
            data = bytes.fromhex(payload)
            async with BleakClient(self._ble_client) as client:
                await client.write_gatt_char(self._control_uuid, data)

    @property
    def name(self):
        """Name."""
        return self._name

    async def async_turn_on(self, **kwargs):
        """Turn on."""
        await self.send_payload([PAYLOAD_FLUSH, self._state_payload])

    async def async_turn_off(self, **kwargs):
        """Turn off."""
        await self.send_payload([PAYLOAD_FLUSH, PAYLOAD_OFF])

    def turn_on(self, **kwargs):
        """Turn on, but not implemented."""
        raise NotImplementedError("Using async instead of turn_on")

    def turn_off(self, **kwargs):
        """Turn off, but not implemented."""
        raise NotImplementedError("Using async instead of turn_off")
