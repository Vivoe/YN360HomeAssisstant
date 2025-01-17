"""Yn360 app integration."""

from .const import DOMAIN


async def async_setup_entry(hass, entry) -> bool:
    """Set up Yn360 from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "light")
    )
    return True
