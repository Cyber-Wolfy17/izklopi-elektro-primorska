"""Sensor platform for the Elektro Primorska izpadi integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HISNA_STEVILKA, CONF_KRAJ, DOMAIN, MAX_LISTED_OUTAGES
from .coordinator import ElektroIzpadiCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ElektroIzpadiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NaslednjiIzpadSensor(coordinator, entry)])


class NaslednjiIzpadSensor(
    CoordinatorEntity[ElektroIzpadiCoordinator], SensorEntity
):
    """Timestamp of the next planned outage for the configured location."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True
    _attr_icon = "mdi:transmission-tower-off"
    _attr_name = "Naslednji izpad"

    def __init__(
        self, coordinator: ElektroIzpadiCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_naslednji_izpad"
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

    @property
    def native_value(self) -> datetime | None:
        for outage in self.coordinator.data or []:
            if outage["od"] is not None:
                return outage["od"]
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        outages = self.coordinator.data or []
        naslednji = next((o for o in outages if o["od"] is not None), None)
        return {
            "kraj": naslednji["kraj"] if naslednji else None,
            "ulica": naslednji["lokacija"] if naslednji else None,
            "hisne_stevilke": naslednji["hisne_stevilke"] if naslednji else None,
            "konec": (
                naslednji["do"].isoformat()
                if naslednji and naslednji["do"] is not None
                else None
            ),
            "akcija": naslednji["akcija"] if naslednji else None,
            "stevilo_izpadov": len(outages),
            "naslednji_izpadi": [
                {
                    "ulica": o["lokacija"],
                    "kraj": o["kraj"],
                    "od": o["od"].isoformat() if o["od"] is not None else None,
                    "do": o["do"].isoformat() if o["do"] is not None else None,
                    "akcija": o["akcija"],
                }
                for o in outages[:MAX_LISTED_OUTAGES]
            ],
        }
