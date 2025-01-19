"""YN360 Light integration for Home Assistant."""

import asyncio
import logging

from bleak import BleakClient

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PAYLOAD_OFF, PAYLOAD_ON_DEFAULT

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> bool:
    """Set up the YN360 light platform."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([YN360Light(entry_data)])
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up leftover devices."""
    if entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]


class YN360Light(LightEntity):
    """YN360 light entity."""

    def __init__(self, entry_data) -> None:
        """Initialize the light."""
        self._entry_data = entry_data
        self._name = "YN360_" + entry_data["uid"]
        self._state = False
        self._state_payload = PAYLOAD_ON_DEFAULT

    async def send_payload(self, uuid, payloads):
        """Send a hex payload to the device."""
        control_uuid = self._entry_data["control_uuids"][uuid]
        if not isinstance(payloads, list):
            payloads = [payloads]

        try:
            async with BleakClient(uuid, timeout=1) as client:
                for payload in payloads:
                    data = bytes.fromhex(payload)
                    client.write_gatt_char(control_uuid, data)
        except TimeoutError:
            LOGGER.debug("Could not connect to uuid %s", uuid)

    @property
    def name(self):
        """Name."""
        return self._name

    async def async_turn_on(self, **kwargs):
        """Turn on."""
        LOGGER.debug("Turning on with payload: %s", self._state_payload)
        tasks = [
            self.send_payload(uuid, self._state_payload)
            for uuid in self._entry_data["uuids"]
        ]
        await asyncio.gather(*tasks)
        self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn off."""
        LOGGER.debug("Turning off with payload: %s", PAYLOAD_OFF)
        tasks = [
            self.send_payload(uuid, PAYLOAD_OFF) for uuid in self._entry_data["uuids"]
        ]
        await asyncio.gather(*tasks)
        self._state = True

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
        return self._entry_data["uid"]
