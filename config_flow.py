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

        LOGGER.error(str(discovery_info))

        if discovery_info is None or discovery_info["action"] == "add_and_refresh":
            if discovery_info is not None:
                known_devices = discovery_info["devices"]
            else:
                known_devices = []

            discovered_devices = async_discovered_service_info(self.hass)
            devices = {
                device.address: f"{device.name}: {device.address}"
                for device in discovered_devices
                if device.name == "YONGNUO LED" and device.address not in known_devices
            }
            schema = vol.Schema(
                {
                    vol.Optional("devices"): cv.multi_select(devices),
                    vol.Required("action"): vol.In(["add_and_refresh", "submit"]),
                }
            )

            if len(known_devices) > 0:
                desc = "\n".join(["Identified devices:", *known_devices])
            else:
                desc = None

            return self.async_show_form(
                step_id="bluetooth", data_schema=schema, description=desc
            )

        # if len(device) < 1:
        #     return self.async_abort(reason="No devices found")
        # if len(device) > 1:
        #     matched_device_names = ", ".join([device.name for device in device])
        #     return self.async_abort(
        #         reason=f"Multiple devices found, matched devices: {matched_device_names}"
        #     )

        # device = device[0]
        data = {}
        data["uuids"] = discovery_info["devices"]
        data["control_uuids"] = {}

        for uuid in devices:  # devices is already list of uuid
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

        return self.async_create_entry(title="YN360", data=data)
