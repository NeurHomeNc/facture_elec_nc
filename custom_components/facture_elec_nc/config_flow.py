from homeassistant import config_entries
import voluptuous as vol
from homeassistant.helpers.selector import selector
from .const import (
    DOMAIN,
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

class FactureElecNCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Facture électricité NC", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_COMMUNE): vol.In(COMMUNES),
            vol.Required(CONF_PUISSANCE_KVA): vol.In(PUISSANCES_KVA),
            vol.Required(CONF_PRIX_REVENTE): vol.In(PRIX_REVENTE_CHOICES),
            vol.Required(CONF_SENSOR_IMPORT): selector({"entity": {"domain": "sensor"}}),
            vol.Optional(CONF_SENSOR_EXPORT): selector({"entity": {"domain": "sensor"}}),
            vol.Optional(CONF_RESET_DAY, default=1): vol.In(range(1, 29)),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)

    def async_get_options_flow(self):
        from .options_flow import FactureElecNCOptionsFlowHandler
        return FactureElecNCOptionsFlowHandler(self)

