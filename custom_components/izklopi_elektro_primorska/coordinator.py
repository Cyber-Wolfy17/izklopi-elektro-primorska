"""Coordinator for the Elektro Primorska izpadi integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ElektroIzpadiClient, filter_outages
from .const import CONF_HISNA_STEVILKA, CONF_KRAJ, CONF_OBMOCJE, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ElektroIzpadiCoordinator(DataUpdateCoordinator[list[dict]]):
    """Fetch outages and filter them for the configured location."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ElektroIzpadiClient,
        entry: ConfigEntry,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=update_interval,
        )
        self.client = client
        self.kraj: str = entry.data[CONF_KRAJ]
        self.hisna_stevilka: str = entry.data.get(CONF_HISNA_STEVILKA) or ""
        self.obmocje: str = entry.data[CONF_OBMOCJE]

    async def _async_update_data(self) -> list[dict]:
        try:
            outages = await self.client.async_fetch_outages(self.obmocje)
        except Exception as err:
            raise UpdateFailed(f"Napaka pri pridobivanju izpadov: {err}") from err
        return filter_outages(outages, self.kraj, self.hisna_stevilka)
