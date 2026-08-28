"""Config flow for the Elektro Primorska izpadi integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import ElektroIzpadiClient, filter_outages
from .const import (
    CONF_HISNA_STEVILKA,
    CONF_KRAJ,
    CONF_OBMOCJE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    OBMOCJA,
)

_LOGGER = logging.getLogger(__name__)


def _build_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_KRAJ, default=user_input.get(CONF_KRAJ, "")
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Optional(
                CONF_HISNA_STEVILKA,
                default=user_input.get(CONF_HISNA_STEVILKA, ""),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required(
                CONF_OBMOCJE, default=user_input.get(CONF_OBMOCJE, "vsi")
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": key, "label": label}
                        for key, label in OBMOCJA.items()
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_UPDATE_INTERVAL,
                    max=MAX_UPDATE_INTERVAL,
                    step=5,
                    unit_of_measurement="min",
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }
    )


async def _validate_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input by fetching live outage data."""
    session = async_create_clientsession(hass)
    client = ElektroIzpadiClient(session)
    outages = await client.async_fetch_outages(data[CONF_OBMOCJE])
    matched = filter_outages(
        outages, data[CONF_KRAJ], data.get(CONF_HISNA_STEVILKA)
    )
    return {"title": data[CONF_KRAJ], "matched": len(matched)}


class ElektroIzpadiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elektro Primorska izpadi."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            kraj = user_input[CONF_KRAJ].strip()
            hisna = (user_input.get(CONF_HISNA_STEVILKA) or "").strip()
            user_input[CONF_KRAJ] = kraj
            user_input[CONF_HISNA_STEVILKA] = hisna

            await self.async_set_unique_id(f"{kraj.lower()}_{hisna.lower()}")
            self._abort_if_unique_id_configured()

            try:
                info = await _validate_input(self.hass, user_input)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unable to reach the Elektro Primorska API")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry  # nosec B101

        errors: dict[str, str] = {}
        if user_input is not None:
            kraj = user_input[CONF_KRAJ].strip()
            hisna = (user_input.get(CONF_HISNA_STEVILKA) or "").strip()
            user_input[CONF_KRAJ] = kraj
            user_input[CONF_HISNA_STEVILKA] = hisna
            try:
                await _validate_input(self.hass, user_input)
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates=user_input
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_build_schema(dict(entry.data)),
            errors=errors,
        )
