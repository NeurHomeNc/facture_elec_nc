from homeassistant import config_entries
import voluptuous as vol
from homeassistant.helpers.selector import selector
from .const import (
    COMMUNES,
    PUISSANCES_KVA,
    PRIX_REVENTE_CHOICES,
    CONF_COMMUNE,
    CONF_PUISSANCE_KVA,
    CONF_PRIX_REVENTE,
    CONF_SENSOR_IMPORT,
    CONF_SENSOR_EXPORT,
    CONF_RESET_DAY,
)

class FactureElecNCOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        data = self.config_entry.data

        puissance_options = [
            {"value": k, "label": v} for k, v in PUISSANCES_KVA.items()
        ]

        data_schema = vol.Schema({
            vol.Required(CONF_COMMUNE, default=options.get(CONF_COMMUNE, data.get(CONF_COMMUNE))): vol.In(COMMUNES),
            #vol.Required(CONF_PUISSANCE_KVA, default=options.get(CONF_PUISSANCE_KVA, data.get(CONF_PUISSANCE_KVA))): vol.In(PUISSANCES_KVA),
            vol.Required(CONF_PUISSANCE_KVA, default=options.get(CONF_PUISSANCE_KVA, data.get(CONF_PUISSANCE_KVA))): selector({
                "select": {
                    "options": puissance_options,
                    "translation_key": "puissance_kva",
                    "mode": "dropdown"
                }
            }),
            vol.Required(CONF_PRIX_REVENTE, default=options.get(CONF_PRIX_REVENTE, data.get(CONF_PRIX_REVENTE))): vol.In(PRIX_REVENTE_CHOICES),
            vol.Required(CONF_SENSOR_IMPORT, default=options.get(CONF_SENSOR_IMPORT, data.get(CONF_SENSOR_IMPORT))): selector({
                "entity": {"domain": "sensor"}
            }),
            vol.Optional(CONF_SENSOR_EXPORT, default=options.get(CONF_SENSOR_EXPORT, data.get(CONF_SENSOR_EXPORT, ""))): selector({
                "entity": {"domain": "sensor"}
            }),
            vol.Optional(CONF_RESET_DAY, default=options.get(CONF_RESET_DAY, data.get(CONF_RESET_DAY, 1))): vol.In(range(1, 29)),
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)
