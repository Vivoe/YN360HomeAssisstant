"""YN360 Light integration for Home Assistant."""

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

import logging

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the YN360 light platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    LOGGER.error(str(config))
    async_add_entities([YN360Light(config.uuid, config.control_uuid)])


class YN360Light(LightEntity):
    """YN360 light entity."""

    def __init__(self, uuid, control_uuid) -> None:
        """Initialize the light."""
        self._name = "YN360"

    @property
    def name(self):
        """Name."""
        return self._name

    @property
    def turn_on(self, **kwargs):
        return super().turn_on(**kwargs)

    @property
    def turn_off(self, **kwargs):
        return super().turn_off(**kwargs)
