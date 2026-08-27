"""Binary sensor platform for the Elektro Primorska izpadi integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_HISNA_STEVILKA, CONF_KRAJ, DOMAIN
from .coordinator import ElektroIzpadiCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ElektroIzpadiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IzpadVTekuBinarySensor(coordinator, entry)])


class IzpadVTekuBinarySensor(
    CoordinatorEntity[ElektroIzpadiCoordinator], BinarySensorEntity
):
    """ON while the configured location is inside a planned outage window."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_has_entity_name = True
    _attr_icon = "mdi:transmission-tower-off"
    _attr_name = "Izpad v teku"

    def __init__(
        self, coordinator: ElektroIzpadiCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_izpad_v_teku"
        self._unsub_track = None
        kraj = entry.data[CONF_KRAJ]
        hisna = (entry.data.get(CONF_HISNA_STEVILKA) or "").strip()
        lokacija = f"{kraj} {hisna}".strip()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Elektro izpadi {lokacija}",
            manufacturer="Elektro Primorska",
            model="Načrtovani izklopi",
            entry_type=DeviceEntryType.SERVICE,
        )

    def _ongoing_outage(self) -> dict | None:
        """Return the outage currently in progress, if any."""
        now = dt_util.now()
        for outage in self.coordinator.data or []:
            start, end = outage["od"], outage["do"]
            if start is None or start > now:
                continue
            if end is None or now < end:
                return outage
        return None

    @property
    def is_on(self) -> bool:
        return self._ongoing_outage() is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        ongoing = self._ongoing_outage()
        if ongoing is None:
            return {}
        return {
            "kraj": ongoing["kraj"],
            "ulica": ongoing["lokacija"],
            "hisne_stevilke": ongoing["hisne_stevilke"],
            "zacetek": ongoing["od"].isoformat(),
            "konec": ongoing["do"].isoformat() if ongoing["do"] is not None else None,
            "akcija": ongoing["akcija"],
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._schedule_next_boundary()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._schedule_next_boundary()
        super()._handle_coordinator_update()

    @callback
    def _schedule_next_boundary(self) -> None:
        """Re-render the state exactly at the next outage start or end."""
        if self._unsub_track is not None:
            self._unsub_track()
            self._unsub_track = None
        now = dt_util.now()
        boundaries = [
            moment
            for outage in self.coordinator.data or []
            for moment in (outage["od"], outage["do"])
            if moment is not None and moment > now
        ]
        if not boundaries:
            return
        self._unsub_track = async_track_point_in_time(
            self.hass, self._boundary_reached, min(boundaries)
        )

    @callback
    def _boundary_reached(self, _now) -> None:
        self._unsub_track = None
        self.async_write_ha_state()
        self._schedule_next_boundary()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_track is not None:
            self._unsub_track()
            self._unsub_track = None
        await super().async_will_remove_from_hass()
