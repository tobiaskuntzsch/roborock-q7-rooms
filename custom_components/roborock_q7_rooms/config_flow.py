"""Config flow for Roborock Q7 Room Cleaning."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RoborockQ7ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow - reuses credentials from the official Roborock integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Single confirmation step - credentials come from existing roborock integration."""
        errors: dict[str, str] = {}

        # Check if official roborock integration is configured
        roborock_entries = self.hass.config_entries.async_entries("roborock")
        if not roborock_entries:
            errors["base"] = "no_roborock"
            return self.async_show_form(
                step_id="user",
                errors=errors,
            )

        if user_input is not None:
            # Prevent duplicate entries
            await self.async_set_unique_id("roborock_q7_rooms")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Roborock Q7 Room Cleaning",
                data={},
            )

        return self.async_show_form(step_id="user")
