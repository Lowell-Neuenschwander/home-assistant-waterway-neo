"""Climate entity for Waterway NEO."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import MAX_TEMP_F, MIN_TEMP_F
from .coordinator import WaterwayNeoCoordinator
from .entity import WaterwayNeoEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Waterway NEO climate entity."""

    coordinator: WaterwayNeoCoordinator = entry.runtime_data
    async_add_entities([WaterwayNeoClimate(coordinator)])


class WaterwayNeoClimate(WaterwayNeoEntity, ClimateEntity):
    """Control the spa target temperature."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_hvac_mode = HVACMode.HEAT
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_min_temp = MIN_TEMP_F
    _attr_max_temp = MAX_TEMP_F
    _attr_target_temperature_step = 1

    def __init__(self, coordinator: WaterwayNeoCoordinator) -> None:
        super().__init__(coordinator, "climate")

    @property
    def current_temperature(self) -> int | None:
        return self.coordinator.data.water_temperature

    @property
    def target_temperature(self) -> int | None:
        return self.coordinator.data.target_temperature

    @property
    def hvac_action(self) -> HVACAction | None:
        current = self.current_temperature
        target = self.target_temperature
        if current is None or target is None:
            return None
        return HVACAction.HEATING if current < target else HVACAction.IDLE

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data.online
            and self.coordinator.data.cloud_available
            and self.target_temperature is not None
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = round(float(kwargs[ATTR_TEMPERATURE]))
        await self.coordinator.client.async_set_temperature(temperature)
        await self.coordinator.async_request_refresh()
