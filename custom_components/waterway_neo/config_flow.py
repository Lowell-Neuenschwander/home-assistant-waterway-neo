"""Config flow for Waterway NEO."""

from __future__ import annotations

import hashlib
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import WaterwayNeoClient, WaterwayNeoError
from .const import (
    CONF_AUTO_SYNC_CLOCK,
    CONF_CHANNEL,
    CONF_CLOCK_DRIFT_THRESHOLD,
    CONF_PUBLISH_KEY,
    CONF_SCAN_INTERVAL,
    CONF_SUBSCRIBE_KEY,
    CONF_TIME_ZONE,
    DEFAULT_AUTO_SYNC_CLOCK,
    DEFAULT_CLOCK_DRIFT_THRESHOLD,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class WaterwayNeoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Waterway NEO config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial setup step."""

        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = dict(user_input)
            user_input[CONF_HOST] = (
                user_input[CONF_HOST]
                .strip()
                .removeprefix("http://")
                .removeprefix("https://")
                .rstrip("/")
            )
            try:
                client = WaterwayNeoClient(
                    async_get_clientsession(self.hass),
                    host=user_input[CONF_HOST],
                    publish_key=user_input[CONF_PUBLISH_KEY],
                    subscribe_key=user_input[CONF_SUBSCRIBE_KEY],
                    channel=user_input[CONF_CHANNEL],
                    time_zone=user_input[CONF_TIME_ZONE],
                )
                data = await client.async_get_data()
                if not data.online or not data.cloud_available:
                    raise WaterwayNeoError("Controller did not return complete state")
            except (WaterwayNeoError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                unique_id = hashlib.sha256(user_input[CONF_CHANNEL].encode()).hexdigest()[:16]
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                title = user_input.pop(CONF_NAME)
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PUBLISH_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_SUBSCRIBE_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_CHANNEL): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_TIME_ZONE, default=self.hass.config.time_zone): str,
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): NumberSelector(
                    NumberSelectorConfig(
                        min=60,
                        max=3600,
                        step=30,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="seconds",
                    )
                ),
                vol.Required(
                    CONF_AUTO_SYNC_CLOCK, default=DEFAULT_AUTO_SYNC_CLOCK
                ): BooleanSelector(),
                vol.Required(
                    CONF_CLOCK_DRIFT_THRESHOLD,
                    default=DEFAULT_CLOCK_DRIFT_THRESHOLD,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="minutes",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
