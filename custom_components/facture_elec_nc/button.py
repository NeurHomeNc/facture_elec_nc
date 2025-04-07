from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

class ResetEnergieButton(ButtonEntity):
    def __init__(self, entry_id):
        self._attr_name = "Remise à zéro manuelle"
        self._attr_unique_id = f"{entry_id}_reset"
        self._entry_id = entry_id
        self._attr_device_info = {
            "identifiers": {(entry_id, DOMAIN)},
            "name": "Facture Électricité NC",
            "manufacturer": "NeurHome",
            "model": "Calculateur de facture"
        }

    async def async_press(self) -> None:
        sensors = self.hass.data.get("facture_elec_nc_energy_entities", {}).get(self._entry_id, [])
        for sensor in sensors:
            await sensor.reset_and_update_reset_day()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    async_add_entities([ResetEnergieButton(entry.entry_id)])
