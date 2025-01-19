"""Config flow to setup YN360 integration."""

import logging
from typing import Any

from bleak import BleakClient
import voluptuous as vol

from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

LOGGER = logging.getLogger(__name__)


# pylint: disable=abstract-method
class YN360ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for YN360 Bluetooth RGB light."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user initiation."""
        return await self.async_step_bluetooth()

    async def async_step_bluetooth(self, discovery_info=None) -> ConfigFlowResult:
        """Get Bluetooth stuff somehow."""

        LOGGER.error(str(discovery_info))

        if discovery_info is None:
            discovered_devices = async_discovered_service_info(self.hass)
            devices = {
                device.address: f"{device.name}: {device.address}"
                for device in discovered_devices
                if device.name == "YONGNUO LED"
            }
            schema = vol.Schema({vol.Required("devices"): cv.multi_select(devices)})

            return self.async_show_form(step_id="bluetooth", data_schema=schema)

        data = {}
        data["uuids"] = discovery_info["devices"]
        data["control_uuids"] = {}

        for uuid in data["uuids"]:  # devices is already list of uuid
            found_control = False
            async with BleakClient(uuid) as client:
                for service in client.services:
                    for characteristic in service.characteristics:
                        if "write" in characteristic.properties:
                            data["control_uuids"][uuid] = characteristic.uuid
                            found_control = True

            if not found_control:
                return self.async_abort(
                    reason=f"No control characteristic found for device {uuid}"
                )

        uid = "yn360_" + "_".join(sorted(data["uuids"]))
        data["uid"] = uid
        await self.async_set_unique_id(uid)
        self._abort_if_unique_id_configured()

        LOGGER.error(data)
        return self.async_create_entry(title="YN360", data=data)
