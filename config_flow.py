"""Config flow to setup YN360 integration."""

import logging
from typing import Any

from bleak import BleakClient
from habluetooth import BluetoothServiceInfoBleak
import voluptuous as vol

from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_URL
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

AUTH_SCHEMA = vol.Schema(
    {vol.Required(CONF_ACCESS_TOKEN): cv.string, vol.Optional(CONF_URL): cv.string}
)

LOGGER = logging.getLogger(__name__)


class YN360ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for YN360 Bluetooth RGB light."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user initiation."""
        # return self.async_show_form(step_id="user", data_schema=AUTH_SCHEMA, errors={})
        return await self.async_step_bluetooth()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak = None
    ) -> ConfigFlowResult:
        """Get Bluetooth stuff somehow."""

        discovered_devices = async_discovered_service_info(self.hass)
        device = [
            device for device in discovered_devices if device.name == "YONGNUO LED"
        ]
        if len(device) != 1:
            return self.async_abort(reason="No devices found")

        device = device[0]
        uuid = device.address

        found_control = False
        control_uuid = None
        async with BleakClient(uuid) as client:
            for service in client.services:
                for characteristic in service.characteristics:
                    if "write" in characteristic.properties:
                        control_uuid = characteristic.uuid
                        found_control = True

        if not found_control:
            return self.async_abort(reason="No control characteristic found")

        await self.async_set_unique_id(uuid)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=device.name, data={"uuid": uuid, "control_uuid": control_uuid}
        )

    def is_matching(self, other_flow: BluetoothServiceInfoBleak) -> bool:
        """Check if discovery info matches the YN360 device."""
        return other_flow.name == "YONGNUO LED"
