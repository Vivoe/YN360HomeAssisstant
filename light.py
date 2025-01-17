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
    async_add_entities([YN360Light(ble_client, config["uuid"], config["control_uuid"])])
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up leftover devices."""
    if entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]


class YN360Light(LightEntity):
    """YN360 light entity."""

    def __init__(self, ble_client, uuid, control_uuid) -> None:
        """Initialize the light."""
        self._name = "YN360_" + uuid
        self._uuid = uuid
        self._state = False
        self._ble_client = ble_client
        self._control_uuid = control_uuid
        self._state_payload = PAYLOAD_ON_DEFAULT

    async def send_payload(self, client, payloads):
        """Send a hex payload to the device."""
        if not isinstance(payloads, list):
            payloads = [payloads]

        for payload in payloads:
            data = bytes.fromhex(payload)
            await client.write_gatt_char(self._control_uuid, data)

    @property
    def name(self):
        """Name."""
        return self._name

    async def async_turn_on(self, **kwargs):
        """Turn on."""
        async with BleakClient(self._ble_client) as client:
            LOGGER.debug("Turning on with payload: %s", self._state_payload)
            await self.send_payload(client, [PAYLOAD_FLUSH, self._state_payload])
            self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn off."""
        async with BleakClient(self._ble_client) as client:
            LOGGER.debug("Turning off with payload: %s", PAYLOAD_OFF)
            await self.send_payload(client, [PAYLOAD_FLUSH, PAYLOAD_OFF])
            self._state = False

    def turn_on(self, **kwargs):
        """Turn on, but not implemented."""
        raise NotImplementedError("Using async instead of turn_on")

    def turn_off(self, **kwargs):
        """Turn off, but not implemented."""
        raise NotImplementedError("Using async instead of turn_off")

    @property
    def is_on(self):
        """Is on."""
        return self._state

    @property
    def unique_id(self):
        """Unique ID."""
        return self._uuid
