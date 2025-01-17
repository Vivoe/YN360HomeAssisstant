"""YN360 Light integration for Home Assistant."""

from homeassistant.components.light import LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the YN360 light platform."""
    add_entities([YN360Light()])
    # host = config[CONF_HOST]


class YN360Light(LightEntity):
    """YN360 light entity."""

    def __init__(self, mac) -> None:
        """Initialize the light."""
        self._name = "YN360"

    @property
    def name(self):
        """Name."""
        return self._name
