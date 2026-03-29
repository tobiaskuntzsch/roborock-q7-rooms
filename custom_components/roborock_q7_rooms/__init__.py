"""Roborock Q7 Room Cleaning integration.

Adds a service to send room cleaning commands to Q7 devices.
Reuses credentials from the official Roborock integration.
"""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from roborock.data import UserData
from roborock.devices.device_manager import UserParams, create_device_manager, DeviceManager
from roborock.devices.device import RoborockDevice

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_CLEAN_SEGMENTS = "clean_segments"
SERVICE_STOP = "stop"
SERVICE_DOCK = "dock"

DEVICE_SCHEMA = {
    vol.Optional("device"): cv.string,
}

CLEAN_SEGMENTS_SCHEMA = vol.Schema(
    {
        **DEVICE_SCHEMA,
        vol.Required("segments"): vol.All(cv.ensure_list, [cv.positive_int]),
        vol.Optional("repeat", default=1): cv.positive_int,
    }
)

DEVICE_ONLY_SCHEMA = vol.Schema(DEVICE_SCHEMA)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Roborock Q7 Room Cleaning from a config entry."""
    # Get credentials from the official roborock integration
    roborock_entries = hass.config_entries.async_entries("roborock")
    if not roborock_entries:
        _LOGGER.error("No Roborock integration found. Please set up the official Roborock integration first.")
        return False

    roborock_entry = roborock_entries[0]
    email = roborock_entry.data.get("email", roborock_entry.data.get("username", ""))
    user_data_dict = roborock_entry.data.get("user_data")
    base_url = roborock_entry.data.get("base_url")

    if not user_data_dict:
        _LOGGER.error("Could not read credentials from Roborock integration")
        return False

    user_data = UserData.from_dict(user_data_dict)
    user_params = UserParams(username=email, user_data=user_data, base_url=base_url)

    device_manager = await create_device_manager(user_params)
    devices = await device_manager.get_devices()

    q7_devices = [d for d in devices if d.b01_q7_properties is not None]

    if not q7_devices:
        _LOGGER.warning("No Q7 devices found")
        await device_manager.close()
        return False

    _LOGGER.info("Found %d Q7 device(s): %s", len(q7_devices), [d._name for d in q7_devices])

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "device_manager": device_manager,
        "devices": q7_devices,
    }

    # Register services
    async def _get_q7(call: ServiceCall) -> RoborockDevice | None:
        """Get the Q7 device, optionally by name."""
        device_name = call.data.get("device")
        for dev in q7_devices:
            if device_name is None or dev._name.lower() == device_name.lower():
                return dev
        _LOGGER.error("Q7 device not found: %s", device_name)
        return None

    async def handle_clean_segments(call: ServiceCall) -> None:
        """Handle clean_segments service call."""
        dev = await _get_q7(call)
        if dev is None:
            return
        segments = call.data["segments"]
        repeat = call.data.get("repeat", 1)
        _LOGGER.info("Q7 %s: cleaning segments %s (repeat=%d)", dev._name, segments, repeat)
        for _ in range(repeat):
            await dev.b01_q7_properties.clean_segments(segments)

    async def handle_stop(call: ServiceCall) -> None:
        """Handle stop service call."""
        dev = await _get_q7(call)
        if dev is None:
            return
        await dev.b01_q7_properties.stop_clean()

    async def handle_dock(call: ServiceCall) -> None:
        """Handle dock service call."""
        dev = await _get_q7(call)
        if dev is None:
            return
        await dev.b01_q7_properties.return_to_dock()

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAN_SEGMENTS,
        handle_clean_segments,
        schema=CLEAN_SEGMENTS_SCHEMA,
    )
    hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop, schema=DEVICE_ONLY_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DOCK, handle_dock, schema=DEVICE_ONLY_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(DOMAIN, SERVICE_CLEAN_SEGMENTS)
    hass.services.async_remove(DOMAIN, SERVICE_STOP)
    hass.services.async_remove(DOMAIN, SERVICE_DOCK)

    data = hass.data[DOMAIN].pop(entry.entry_id)
    await data["device_manager"].close()
    return True
