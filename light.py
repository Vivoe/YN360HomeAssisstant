"""YN360 Light integration for Home Assistant."""

import asyncio
import logging

from bleak import BleakClient, BleakError

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PAYLOAD_FLUSH, PAYLOAD_OFF

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
        self._most_recent_device = self._entry_data["uuids"][0]

        self._brightness = 255
        self._color_mode = ColorMode.ONOFF
        self._color_temp = 5600
        self._rgb = (255, 255, 255)

        self._client = None
        self._disconnect_task = None

    def get_uuid_order(self):
        """Return the uuids in the order that should be tested."""
        uuids = self._entry_data["uuids"].copy()
        uuids.remove(self._most_recent_device)
        uuids.insert(0, self._most_recent_device)
        return uuids

    async def send_payload(self, payloads):
        """Send a hex payload to the device."""
        if not isinstance(payloads, list):
            payloads = [payloads]

        uuids = self.get_uuid_order()
        LOGGER.debug("Trying uuids in order: %s", uuids)
        # No break, we try with all devices in the case they're not sync'd.
        for uuid in uuids:
            control_uuid = self._entry_data["control_uuids"][uuid]
            try:
                # async with BleakClient(uuid) as client:
                client = await self.connect(uuid)
                for payload in payloads:
                    data = bytes.fromhex(payload)
                    await client.write_gatt_char(control_uuid, data)

                await self.schedule_disconnect(10)
                LOGGER.debug("Successfully executed on uuid %s", uuid)
                break
            except TimeoutError:
                LOGGER.debug("Could not connect to uuid %s due to timeout", uuid)
        else:
            raise RuntimeError("Could not connect to any uuids")

    def get_current_payload(self):
        """Get the payload for the given parameters. Always assume channel 1."""
        if not self.is_on:
            LOGGER.debug("[Payload] %s, IS_OFF", PAYLOAD_OFF)
            payload = PAYLOAD_OFF

        if self._color_mode == ColorMode.ONOFF:
            payload = f"AEAA0100{255:02x}56"
            LOGGER.debug("[Payload] %s, ColorMode ONOFF", payload)
        elif self._color_mode == ColorMode.BRIGHTNESS:
            # Default to the warm lights for regular brightness.
            payload = f"AEAA0100{self._brightness:02x}56"
            LOGGER.debug(
                "[Payload] %s, ColorMode BRIGHTNESS %s", payload, self._brightness
            )
        elif self._color_mode == ColorMode.RGB:
            r = self._rgb[0] * self._brightness / 255
            g = self._rgb[1] * self._brightness / 255
            b = self._rgb[2] * self._brightness / 255
            rgb_str = f"{int(r):02x}{int(g):02x}{int(b):02x}"
            payload = f"AEA1{rgb_str}56"

            LOGGER.debug(
                "[Payload] %s, ColorMode RGB %s, brightness %s",
                payload,
                self._rgb,
                self._brightness,
            )

        elif self._color_mode == ColorMode.COLOR_TEMP:
            # 1 = Only use warm, 0 = only use cold.
            temp_pct = (self._color_temp - 3200) / (5600 - 3200)
            cold_led = int(self._brightness * temp_pct)
            warm_led = int(self._brightness * (1 - temp_pct))
            payload = f"AEAA01{cold_led:02x}{warm_led:02x}56"
            LOGGER.debug(
                "[Payload] %s, ColorMode COLOR_TEMP %s, brightness %s",
                payload,
                self._color_temp,
                self._brightness,
            )
        else:
            raise ValueError(f"Invalid color mode {self._color_mode!s}")

        return payload

    def update_state(self, **kwargs):
        """Update the state based on the user input."""
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            self._color_mode = ColorMode.BRIGHTNESS
        if ATTR_RGB_COLOR in kwargs:
            self._rgb = kwargs[ATTR_RGB_COLOR]
            self._color_mode = ColorMode.RGB
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._color_temp = kwargs[ATTR_COLOR_TEMP_KELVIN]
            self._color_mode = ColorMode.COLOR_TEMP

    async def async_turn_on(self, **kwargs):
        """Turn on."""
        LOGGER.debug(str(kwargs))
        self.update_state(**kwargs)
        payload = self.get_current_payload()

        LOGGER.debug("Turning on with payload: %s", payload)
        # await self.send_payload([PAYLOAD_FLUSH, payload])
        await self.send_payload([payload])
        self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn off."""
        LOGGER.debug("Turning off with payload: %s", PAYLOAD_OFF)
        await self.send_payload(PAYLOAD_OFF)
        self._state = False

    def turn_on(self, **kwargs):
        """Turn on, but not implemented."""
        raise NotImplementedError("Using async instead of turn_on")

    def turn_off(self, **kwargs):
        """Turn off, but not implemented."""
        raise NotImplementedError("Using async instead of turn_off")

    @property
    def name(self):
        """Name."""
        return self._name

    @property
    def supported_color_modes(self):
        """Supported color modes."""
        return {
            ColorMode.ONOFF,
            ColorMode.BRIGHTNESS,
            ColorMode.RGB,
            ColorMode.COLOR_TEMP,
        }

    @property
    def color_mode(self):
        """Color mode."""
        return self._color_mode

    @property
    def is_on(self):
        """Is on."""
        return self._state

    @property
    def unique_id(self):
        """Unique ID."""
        return self._entry_data["uid"]

    @property
    def brightness(self):
        """Brightness."""
        return self._brightness

    @property
    def max_color_temp_kelvin(self):
        """Max color temp."""
        return 5600

    @property
    def min_color_temp_kelvin(self):
        """Min color temp."""
        return 3200

    @property
    def color_temp_kelvin(self):
        """Color temp."""
        return self._color_temp

    async def schedule_disconnect(self, delay):
        """Schedule a disconnect after a delay."""
        LOGGER.debug("Schedulling disconnect")
        if self._disconnect_task:
            self._disconnect_task.cancel()
        self._disconnect_task = asyncio.create_task(self._disconnect_after_delay(delay))

    async def _disconnect_after_delay(self, delay):
        LOGGER.debug("Triggering disconect task")
        try:
            await asyncio.sleep(delay)
            LOGGER.debug("Should be time to disconnect")
            await self.disconnect()
        except asyncio.CancelledError:
            # Handle the cancellation if needed
            LOGGER.debug("Disconnect task cancelled")

    async def connect(self, address):
        """Connect to the device and get a client instance."""
        if self._client is not None:
            try:
                if self._client.address == address and self._client.is_connected:
                    return self._client
            except AttributeError:
                LOGGER.debug("BleakClient backend has no address")
            # If can't reuse connection, clean up and just make a new one.
            if self._client.is_connected:
                await self._client.disconnect()
            else:
                self._client = None

            return await self.connect(address)

        # New client
        most_recent_err = None
        for i in range(3):
            try:
                LOGGER.debug("Connecting to device %s, attempt %s", address, i)
                self._client = BleakClient(address)
                await self._client.connect()
                break
            except BleakError as e:
                most_recent_err = e
                await asyncio.sleep(1)
        else:
            raise most_recent_err
        return self._client

    async def disconnect(self):
        """Disconnect from the device."""
        LOGGER.debug("Trying to disconnect")
        if self._client and self._client.is_connected:
            LOGGER.debug("Disconnecting from device %s", self._client.address)
            await self._client.disconnect()
        self._client = None
