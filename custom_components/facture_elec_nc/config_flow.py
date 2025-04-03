from homeassistant import config_entries
from .const import (
    DOMAIN, COMMUNES, PUISSANCES_KVA,
    CONF_COMMUNE, CONF_PUISSANCE_KVA,
    CONF_PRIX_RACHAT, CONF_SENSOR_IMPORT,
    CONF_SENSOR_EXPORT, CONF_RESET_DAY
)
import voluptuous as vol
import requests
from homeassistant.helpers.selector import selector

class FactureElecNCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # Pas besoin de vérifier ou modifier quoi que ce soit ici
            return self.async_create_entry(title="Facture électricité", data=user_input)

        # 🧪 Récupération dynamique des prix de rachat
        try:
            response = requests.get("https://neurhome.nc/data_elec.php", timeout=5)
            data = response.json()
            prixs_rachat = data.get("prix_rachat", [15, 21])
        except Exception:
            prixs_rachat = [15, 21]  # fallback par défaut

        # 🧾 Formulaire de configuration
        data_schema = {
            vol.Required(CONF_COMMUNE): vol.In(COMMUNES),
            vol.Required(CONF_PUISSANCE_KVA): vol.In({3: "3,3 kVA", 6: "6,6 kVA", 9: "9,9 kVA"}),
            vol.Required(CONF_SENSOR_IMPORT): selector({"entity": {"domain": "sensor"}}),
            vol.Optional(CONF_SENSOR_EXPORT): selector({"entity": {"domain": "sensor"}}),
            vol.Optional(CONF_PRIX_RACHAT): vol.In(prixs_rachat),
            vol.Required(CONF_RESET_DAY, default=1): vol.In(range(1, 29)),
        }

        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema))
