"""YN360 Light integration for Home Assistant."""

import logging

from bleak import BleakClient, BleakError

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
        self._most_recent_device = self._entry_data["uuids"][0]

    def get_uuid_order(self):
        """Return the uuids in the order that should be tested."""
        uuids = self._entry_data["uuids"].copy()
        uuids.remove(self._most_recent_device)
        uuids.insert(0, self._most_recent_device)
        return uuids

    async def send_payload(self, uuid, payloads):
        """Send a hex payload to the device."""
        control_uuid = self._entry_data["control_uuids"][uuid]
        if not isinstance(payloads, list):
            payloads = [payloads]

        try:
            async with BleakClient(uuid, timeout=3) as client:
                for payload in payloads:
                    data = bytes.fromhex(payload)
                    await client.write_gatt_char(control_uuid, data)
        except TimeoutError:
            LOGGER.debug("Could not connect to uuid %s due to timeout", uuid)
        except BleakError as e:
            LOGGER.error("Could not connect to uuid %s due to error: %s", uuid, e)

    async def send_payload_all(self, payloads):
        """Send a hex payload to the device."""
        if not isinstance(payloads, list):
            payloads = [payloads]

        uuids = self.get_uuid_order()
        LOGGER.debug("Trying uuids in order: %s", uuids)
        # No break, we try with all devices in the case they're not sync'd.
        for uuid in uuids:
            control_uuid = self._entry_data["control_uuids"][uuid]
            try:
                async with BleakClient(uuid, timeout=3) as client:
                    for payload in payloads:
                        data = bytes.fromhex(payload)
                        await client.write_gatt_char(control_uuid, data)
                    break
            except TimeoutError:
                LOGGER.debug("Could not connect to uuid %s due to timeout", uuid)

    @property
    def name(self):
        """Name."""
        return self._name

    async def async_turn_on(self, **kwargs):
        """Turn on."""
        LOGGER.debug("Turning on with payload: %s", self._state_payload)
        await self.send_payload_all(self._state_payload)
        # tasks = [
        #     self.send_payload(uuid, self._state_payload)
        #     for uuid in self._entry_data["uuids"]
        # ]
        # await asyncio.gather(*tasks)
        self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn off."""
        LOGGER.debug("Turning off with payload: %s", PAYLOAD_OFF)
        await self.send_payload_all(PAYLOAD_OFF)
        # tasks = [
        # self.send_payload(uuid, PAYLOAD_OFF) for uuid in self._entry_data["uuids"]
        # ]
        # await asyncio.gather(*tasks)
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
