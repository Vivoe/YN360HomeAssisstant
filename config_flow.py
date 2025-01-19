"""Config flow to setup YN360 integration."""

import logging
from typing import Any

from bleak import BleakClient
from habluetooth import BluetoothServiceInfoBleak

import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN

LOGGER = logging.getLogger(__name__)


class YN360ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for YN360 Bluetooth RGB light."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user initiation."""
        return await self.async_step_bluetooth()

    async def async_step_bluetooth(self, discovery_info=None) -> ConfigFlowResult:
        """Get Bluetooth stuff somehow."""

        if discovery_info is None or discovery_info["refresh"]:
            discovered_devices = async_discovered_service_info(self.hass)
            devices = {
                device.address: device.name
                for device in discovered_devices
                if device.name == "YONGNUO LED"
            }
            schema = vol.Schema(
                {
                    vol.Optional("devices"): cv.multi_select(devices),
                    vol.Required("Action"): vol.In(
                        ["Add device and refresh", "submit"]
                    ),
                }
            )

            if isinstance(discovery_info, dict) and "devices" in discovery_info:
                known_device_ids = [device.name for device in devices]
                desc = "\n".join(["Identified devices: \n", *known_device_ids])
            else:
                desc = None

            return self.async_show_form(
                step_id="bluetooth", data_schema=schema, description_placeholders=desc
            )

        # if len(device) < 1:
        #     return self.async_abort(reason="No devices found")
        # if len(device) > 1:
        #     matched_device_names = ", ".join([device.name for device in device])
        #     return self.async_abort(
        #         reason=f"Multiple devices found, matched devices: {matched_device_names}"
        #     )

        LOGGER.error(str(discovery_info))

        # device = device[0]
        device = None
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
