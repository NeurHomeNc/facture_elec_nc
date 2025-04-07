from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import aiohttp
import unicodedata
from .const import (
    DOMAIN,
    CONF_COMMUNE,
    CONF_PUISSANCE_KVA,
    CONF_PRIX_REVENTE,
    CONF_SENSOR_IMPORT,
    CONF_SENSOR_EXPORT,
    CONF_RESET_DAY
)

API_URL = "https://neurhome.nc/data_elec.php"

def simplify(name):
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().replace(" ", "").replace("-", "")

class BaseFactureSensor(RestoreEntity):
    def __init__(self, name, unique_id, entry_id):
        self._attr_name = name
        self._attr_unit_of_measurement = "XPF"
        self._attr_unique_id = unique_id
        self._attr_device_info = {
            "identifiers": {(entry_id, DOMAIN)},
            "name": "Facture Électricité NC",
            "manufacturer": "NeurHome",
            "model": "Calculateur de facture"
        }
        self._attr_state = None

    async def async_added_to_hass(self):
        if (old := await self.async_get_last_state()):
            try:
                self._attr_state = int(float(old.state))
            except:
                pass

class PrimeFixeSensor(BaseFactureSensor):
    def __init__(self, puissance, entry_id):
        super().__init__("Prime fixe", "prime_fixe", entry_id)
        self.puissance = puissance

    async def async_update(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as resp:
                data = await resp.json()
        valeur = float(data[self.puissance][0])
        self._attr_state = round(valeur)

class RedevanceComptageSensor(BaseFactureSensor):
    def __init__(self, entry_id):
        super().__init__("Redevance comptage", "redevance_comptage", entry_id)

    async def async_update(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as resp:
                data = await resp.json()
        self._attr_state = round(data["redevance_comptage"])

class EnergySensor(BaseFactureSensor):
    def __init__(self, name, sensor_id, reset_day, prix_kwh, unique_id, entry_id):
        super().__init__(name, unique_id, entry_id)
        self.sensor_id = sensor_id
        self.reset_day = reset_day
        self.prix_kwh = prix_kwh

    async def async_update(self):
        entity = self.hass.states.get(self.sensor_id)
        if entity is None or entity.state in ("unknown", "unavailable"):
            return
        try:
            kwh = float(entity.state)
            self._attr_state = round(kwh * self.prix_kwh)
        except:
            return

class TaxeCommunaleSensor(BaseFactureSensor):
    def __init__(self, commune, capteur_prime, capteur_import, entry_id):
        super().__init__("Taxe communale", "taxe_communale", entry_id)
        self.commune = simplify(commune)
        self.capteur_prime = capteur_prime
        self.capteur_import = capteur_import

    async def async_update(self):
        prime = self.hass.states.get(self.capteur_prime)
        imp = self.hass.states.get(self.capteur_import)
        if not prime or not imp:
            return
        try:
            prime_val = float(prime.state)
            imp_val = float(imp.state)
        except:
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as resp:
                data = await resp.json()

        taux = data["taxes"].get(self.commune, 0)
        montant = (prime_val + imp_val) * taux
        self._attr_state = round(montant)

class TGCSensor(BaseFactureSensor):
    def __init__(self, capteur_prime, capteur_import, capteur_taxe, capteur_redevance, entry_id):
        super().__init__("Montant TGC", "montant_tgc", entry_id)
        self.capteur_prime = capteur_prime
        self.capteur_import = capteur_import
        self.capteur_taxe = capteur_taxe
        self.capteur_redevance = capteur_redevance

    async def async_update(self):
        try:
            prime = float(self.hass.states.get(self.capteur_prime).state)
            imp = float(self.hass.states.get(self.capteur_import).state)
            taxe = float(self.hass.states.get(self.capteur_taxe).state)
            redevance = float(self.hass.states.get(self.capteur_redevance).state)
        except:
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as resp:
                data = await resp.json()

        taux_tgc = data.get("taux_tgc", 0)
        base = prime + imp + taxe + redevance
        self._attr_state = round(base * taux_tgc)

class ExportEnergySensor(BaseFactureSensor):
    def __init__(self, name, sensor_id, reset_day, prix_revente, unique_id, entry_id):
        super().__init__(name, unique_id, entry_id)
        self.sensor_id = sensor_id
        self.reset_day = reset_day
        self.prix_revente = prix_revente

    async def async_update(self):
        entity = self.hass.states.get(self.sensor_id)
        if entity is None or entity.state in ("unknown", "unavailable"):
            return
        try:
            kwh = float(entity.state)
            self._attr_state = round(kwh * self.prix_revente)
        except:
            return

class TotalFactureSensor(BaseFactureSensor):
    def __init__(self, capteurs, entry_id):
        super().__init__("Total facture", "total_facture", entry_id)
        self.capteurs = capteurs

    async def async_update(self):
        total = 0
        for entity_id in self.capteurs:
            state = self.hass.states.get(entity_id)
            try:
                total += float(state.state)
            except:
                continue
        self._attr_state = round(total)

class EnergyAmountSensor(RestoreEntity):
    async def reset_and_update_reset_day(self):
        today = dt_util.utcnow().day
        self.reset_day = min(today, 29)
        if self.hass.data.get("facture_elec_nc_reset_days") is None:
            self.hass.data["facture_elec_nc_reset_days"] = {}
        self.hass.data["facture_elec_nc_reset_days"][self.entry_id] = self.reset_day
        self._attr_state = 0

        # Mise à jour dans config entry
        entry = next((e for e in self.hass.config_entries.async_entries(DOMAIN) if e.entry_id == self.entry_id), None)
        if entry:
            new_options = dict(entry.options)
            new_options[CONF_RESET_DAY] = self.reset_day
            self.hass.config_entries.async_update_entry(entry, options=new_options)

    def __init__(self, name, power_sensor_id, reset_day, unique_id, entry_id, mode="import"):
        self.entry_id = entry_id
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_unit_of_measurement = "kWh"
        self._attr_state = None
        self._attr_device_info = {
            "identifiers": {(entry_id, DOMAIN)},
            "name": "Facture Électricité NC",
            "manufacturer": "NeurHome",
            "model": "Calculateur de facture"
        }
        self.power_sensor_id = power_sensor_id
        self.reset_day = reset_day
        self.mode = mode
        self._last_update = dt_util.utcnow()

    async def async_added_to_hass(self):
        if (old := await self.async_get_last_state()):
            try:
                self._attr_state = float(old.state)
            except:
                self._attr_state = 0

    async def async_update(self):
        now = dt_util.utcnow()
        entity = self.hass.states.get(self.power_sensor_id)
        if entity is None or entity.state in ("unknown", "unavailable"):
            return
        try:
            power = float(entity.state)
        except:
            return

        elapsed = (now - self._last_update).total_seconds() / 3600
        self._last_update = now

        if (self.mode == "import" and power > 0) or (self.mode == "export" and power < 0):
            kwh = abs(power) * elapsed / 1000
        else:
            kwh = 0

        if self._attr_state is None:
            self._attr_state = 0

        if now.day == self.reset_day:
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if self._last_update < midnight:
                self._attr_state = 0

        self._attr_state = round(self._attr_state + kwh, 2)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    hass.data.setdefault("facture_elec_nc_energy_entities", {})
    hass.data.setdefault("facture_elec_nc_reset_days", {})
    entry_id = entry.entry_id
    puissance = entry.data[CONF_PUISSANCE_KVA]
    commune = entry.data[CONF_COMMUNE]
    prix_revente = entry.data[CONF_PRIX_REVENTE]
    sensor_import = entry.data[CONF_SENSOR_IMPORT]
    sensor_export = entry.data.get(CONF_SENSOR_EXPORT)
    reset_day = entry.data.get(CONF_RESET_DAY, 1)

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as resp:
            data = await resp.json()
    prix_achat = float(data[puissance][1])

    sensors = []

    capteur_prime = "sensor.prime_fixe"
    capteur_import_val = "sensor.valeur_energie_importee"
    capteur_taxe = "sensor.taxe_communale"
    capteur_redevance = "sensor.redevance_comptage"
    capteur_export_val = "sensor.valeur_energie_exportee"

    sensors.append(PrimeFixeSensor(puissance, entry_id))
    sensors.append(EnergySensor("Valeur énergie importée", "sensor.energie_importee_kwh", reset_day, prix_achat, "valeur_energie_importee", entry_id))
    sensors.append(TaxeCommunaleSensor(commune, capteur_prime, capteur_import_val, entry_id))
    sensors.append(RedevanceComptageSensor(entry_id))
    sensors.append(TGCSensor(capteur_prime, capteur_import_val, capteur_taxe, capteur_redevance, entry_id))

    capteurs_total = [
        capteur_prime,
        capteur_import_val,
        capteur_taxe,
        capteur_redevance,
        "sensor.montant_tgc"
    ]

    import_sensor = EnergyAmountSensor("Énergie importée (kWh)", sensor_import, reset_day, "energie_importee_kwh", entry_id, mode="import")
    sensors.append(import_sensor)
    hass.data["facture_elec_nc_energy_entities"].setdefault(entry_id, []).append(import_sensor)

    if sensor_export:
        export_sensor = EnergyAmountSensor("Énergie exportée (kWh)", sensor_export, reset_day, "energie_exportee_kwh", entry_id, mode="export")
        sensors.append(export_sensor)
        hass.data["facture_elec_nc_energy_entities"].setdefault(entry_id, []).append(export_sensor)
        sensors.append(ExportEnergySensor("Valeur énergie exportée", "sensor.energie_exportee_kwh", reset_day, prix_revente, "valeur_energie_exportee", entry_id))
        capteurs_total.append(capteur_export_val)

    sensors.append(TotalFactureSensor(capteurs_total, entry_id))

    async_add_entities(sensors)
