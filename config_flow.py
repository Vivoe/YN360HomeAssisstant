"""Test file."""

from typing import Any

from habluetooth import BluetoothServiceInfoBleak
import voluptuous as vol

from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_URL
from homeassistant.helpers import config_validation as cv

import logging

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
        return self.async_show_form(step_id="user", data_schema=AUTH_SCHEMA, errors={})
        # return await self.async_step_bluetooth()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak = None
    ) -> ConfigFlowResult:
        """Get Bluetooth stuff somehow."""
        if discovery_info:
            LOGGER.info("|".join([str(x) for x in dir(discovery_info)]))
            uuid = discovery_info.address
            await self.async_set_unique_id(uuid)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=discovery_info.name, data={"address": uuid}
            )

        discovered_devices = async_discovered_service_info(self.hass)
        devices = {device.address: device.name for device in discovered_devices}
        if not devices:
            return self.async_abort(reason="No devices found")

        return self.async_show_form(
            step_id="bluetooth",
            data_schema=vol.Schema({vol.Required("device"): vol.In(devices)}),
        )
