"""YN360 Light integration for Home Assistant."""

import asyncio
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
    async_add_entities(YN360Light(entry_data))

    # ble_client = async_ble_device_from_address(hass, config["uuid"])
    # async_add_entities([YN360Light(ble_client, config["uuid"], config["control_uuid"])])
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

    async def get_client(self, address):
        """Attempt to get a BleakClient, returns None if cannot connect."""
        try:
            return BleakClient(address, timeout=1).connect()
        except BleakError:
            return None

    async def get_clients(self):
        """Get all potential devices. Missing devices wil be filtered out."""
        clients_all = [self.get_client(address) for address in self._entry_data["uuid"]]
        return [client for client in clients_all if client is not None]

    async def send_payload(self, clients, payloads):
        """Send a hex payload to the device."""
        if not isinstance(payloads, list):
            payloads = [payloads]

        for payload in payloads:
            data = bytes.fromhex(payload)
            tasks = [
                client.write_gatt_char(
                    self._entry_data["control_uuid"][client.address], data
                )
                for client in clients
            ]
            await asyncio.gather(*tasks)

    @property
    def name(self):
        """Name."""
        return self._name

    async def async_turn_on(self, **kwargs):
        """Turn on."""
        clients = await self.get_clients()
        LOGGER.debug("Turning on with payload: %s", self._state_payload)
        await self.send_payload(clients, self._state_payload)
        self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn off."""
        clients = await self.get_clients()
        LOGGER.debug("Turning on with payload: %s", self._state_payload)
        await self.send_payload(clients, PAYLOAD_OFF)
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
        return self._entry_data["uid"]
