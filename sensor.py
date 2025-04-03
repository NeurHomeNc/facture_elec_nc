from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify
import aiohttp
import unicodedata

from .const import (
    CONF_COMMUNE,
    CONF_PUISSANCE_KVA,
    CONF_PRIX_RACHAT,
    CONF_SENSOR_IMPORT,
    CONF_SENSOR_EXPORT,
    CONF_RESET_DAY
)

# --------------------
# Utils
# --------------------
def get_key_from_puissance(puissance_kva):
    return {3: "PS3", 6: "PS6", 9: "PS9"}.get(puissance_kva)

def simplifier_commune(nom):
    nfkd = unicodedata.normalize('NFKD', nom)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower().replace(" ", "").replace("-", "")

# --------------------
# Base Sensor Classes
# --------------------
class BaseSensor(Entity):
    def __init__(self, name, unit, unique_suffix):
        self._attr_name = name
        self._attr_unit_of_measurement = unit
        self._attr_unique_id = slugify(f"facture_{unique_suffix}")

class RestoreBaseSensor(RestoreEntity, BaseSensor):
    def __init__(self, name, unit, unique_suffix):
        BaseSensor.__init__(self, name, unit, unique_suffix)

# --------------------
# API-based Sensors
# --------------------
class PrimeFixeSensor(BaseSensor):
    def __init__(self, puissance_kva):
        super().__init__("Prime fixe", "XPF", "prime_fixe")
        self.puissance_kva = puissance_kva

    async def async_update(self):
        key = get_key_from_puissance(self.puissance_kva)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://neurhome.nc/data_elec.php") as resp:
                    data = await resp.json()
            self._attr_state = float(data[key][0]) if key else "inconnu"
        except:
            self._attr_state = "erreur"

class PrixAchatSensor(BaseSensor):
    def __init__(self, puissance_kva):
        super().__init__("Prix d'achat", "XPF/kWh", "prix_achat")
        self.puissance_kva = puissance_kva

    async def async_update(self):
        key = get_key_from_puissance(self.puissance_kva)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://neurhome.nc/data_elec.php") as resp:
                    data = await resp.json()
            self._attr_state = float(data[key][1]) if key else "inconnu"
        except:
            self._attr_state = "erreur"

class RedevanceComptageSensor(BaseSensor):
    def __init__(self):
        super().__init__("Redevance comptage", "XPF", "redevance_comptage")

    async def async_update(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://neurhome.nc/data_elec.php") as resp:
                    data = await resp.json()
            self._attr_state = float(data["redevance_comptage"])
        except:
            self._attr_state = "erreur"

class TauxTGCSensor(BaseSensor):
    def __init__(self):
        super().__init__("Taux TGC", "%", "taux_tgc")

    async def async_update(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://neurhome.nc/data_elec.php") as resp:
                    data = await resp.json()
            self._attr_state = round(data["taux_tgc"] * 100, 2)
        except:
            self._attr_state = "erreur"

class TaxeCommunaleSensor(BaseSensor):
    def __init__(self, commune_affichee):
        super().__init__("Taxe communale", "%", "taxe_communale")
        self.commune_affichee = commune_affichee
        self.commune_cle = simplifier_commune(commune_affichee)

    async def async_update(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://neurhome.nc/data_elec.php") as resp:
                    data = await resp.json()
            taxe = data["taxes"].get(self.commune_cle)
            self._attr_state = round(taxe * 100, 2) if taxe is not None else 0.0
        except:
            self._attr_state = "erreur"

# --------------------
# Setup
# --------------------
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    puissance_kva = entry.data.get(CONF_PUISSANCE_KVA)
    commune = entry.data.get(CONF_COMMUNE)
    prix_rachat = entry.data.get(CONF_PRIX_RACHAT)
    sensor_import = entry.data.get(CONF_SENSOR_IMPORT)
    sensor_export = entry.data.get(CONF_SENSOR_EXPORT)
    reset_day = entry.data.get(CONF_RESET_DAY, 1)

    sensors = [
        PrimeFixeSensor(puissance_kva),
        PrixAchatSensor(puissance_kva),
        RedevanceComptageSensor(),
        TauxTGCSensor(),
        TaxeCommunaleSensor(commune)
    ]

    async_add_entities(sensors)

# --------------------
# Energy and Finance Sensors
# --------------------

class ValeurNetEnergieSensor(BaseSensor):
    def __init__(self, hass):
        super().__init__("Énergie nette (import - export)", "XPF", "valeur_energie_nette")
        self.hass = hass

    async def async_update(self):
        def val(e):
            state = self.hass.states.get(e)
            return float(state.state) if state and state.state not in ("unknown", "unavailable") else 0.0

        importee = val("sensor.valeur_energie_importee")
        exportee = val("sensor.valeur_exportee")
        self._attr_state = int(round(importee - exportee, 0))

class EnergyFromPowerSensor(RestoreBaseSensor):
    def __init__(self, hass, sensor_id, reset_day):
        super().__init__("Énergie importée", "kWh", "energie_importee")
        self.hass = hass
        self.sensor_id = sensor_id
        self.reset_day = reset_day
        self._attr_state = 0.0
        self._last_update = None

    async def async_added_to_hass(self):
        state = await self.async_get_last_state()
        if state and state.state not in ("unknown", "unavailable"):
            self._attr_state = float(state.state)
        self._last_update = dt_util.utcnow()

    async def async_update(self):
        now = dt_util.utcnow()
        entity = self.hass.states.get(self.sensor_id)
        if not entity or entity.state in ("unknown", "unavailable"):
            return
        try:
            watts = float(entity.state)
            if watts <= 0:
                return
            elapsed = (now - self._last_update).total_seconds() / 3600
            self._attr_state = round(self._attr_state + watts * elapsed / 1000, 4)
            self._last_update = now
            if now.day == self.reset_day and self._last_update < now.replace(hour=0, minute=0):
                self._attr_state = 0.0
        except:
            pass

class ValeurEnergieImporteeSensor(BaseSensor):
    def __init__(self, hass, energy_sensor, prix):
        super().__init__("Valeur énergie importée", "XPF", "valeur_energie_importee")
        self.hass = hass
        self.energy_sensor = energy_sensor
        self.prix = prix

    async def async_update(self):
        state = self.hass.states.get(self.energy_sensor)
        if not state or state.state in ("unknown", "unavailable"):
            return
        try:
            kwh = float(state.state)
            self._attr_state = int(round(kwh * self.prix, 0))
        except:
            self._attr_state = "erreur"

class PrixRachatConfigSensor(BaseSensor):
    def __init__(self, prix):
        super().__init__("Prix de rachat configuré", "XPF/kWh", "prix_rachat_config")
        self._attr_state = prix

    async def async_update(self):
        pass

class EnergyFromExportSensor(RestoreBaseSensor):
    def __init__(self, hass, sensor_id, reset_day):
        super().__init__("Énergie exportée", "kWh", "energie_exportee")
        self.hass = hass
        self.sensor_id = sensor_id
        self.reset_day = reset_day
        self._attr_state = 0.0
        self._last_update = None

    async def async_added_to_hass(self):
        state = await self.async_get_last_state()
        if state and state.state not in ("unknown", "unavailable"):
            self._attr_state = float(state.state)
        self._last_update = dt_util.utcnow()

    async def async_update(self):
        now = dt_util.utcnow()
        entity = self.hass.states.get(self.sensor_id)
        if not entity or entity.state in ("unknown", "unavailable"):
            return
        try:
            watts = float(entity.state)
            elapsed = (now - self._last_update).total_seconds() / 3600
            self._attr_state = round(self._attr_state + watts * elapsed / 1000, 4)
            self._last_update = now
            if now.day == self.reset_day and self._last_update < now.replace(hour=0, minute=0):
                self._attr_state = 0.0
        except:
            pass

class ValeurExportSensor(RestoreBaseSensor):
    def __init__(self, hass, export_sensor_id, prix):
        super().__init__("Valeur exportée", "XPF", "valeur_exportee")
        self.hass = hass
        self.export_sensor_id = export_sensor_id
        self.prix = prix

    async def async_added_to_hass(self):
        state = await self.async_get_last_state()
        if state and state.state not in ("unknown", "unavailable"):
            self._attr_state = float(state.state)

    async def async_update(self):
        entity = self.hass.states.get(self.export_sensor_id)
        if entity and entity.state not in ("unknown", "unavailable"):
            try:
                kwh = float(entity.state)
                self._attr_state = int(round(kwh * self.prix, 0))
            except:
                self._attr_state = 0.0

class FactureTotalSensor(BaseSensor):
    def __init__(self, hass):
        super().__init__("Facture totale", "XPF", "facture_totale")
        self.hass = hass

    async def async_update(self):
        def val(e):
            state = self.hass.states.get(e)
            return float(state.state) if state and state.state not in ("unknown", "unavailable") else 0.0

        v_import = val("sensor.valeur_energie_importee")
        prime = val("sensor.prime_fixe")
        taxe = val("sensor.taxe_communale") / 100.0
        redevance = val("sensor.redevance_comptage")
        tgc = val("sensor.taux_tgc") / 100.0
        export = val("sensor.valeur_exportee")

        base = v_import + prime + (v_import + prime) * taxe + redevance
        total = base * (1 + tgc) - export
        self._attr_state = int(round(total, 0))

class MontantTaxeCommunaleSensor(BaseSensor):
    def __init__(self, hass):
        super().__init__("Montant taxe communale", "XPF", "montant_taxe_communale")
        self.hass = hass

    async def async_update(self):
        def val(e):
            state = self.hass.states.get(e)
            return float(state.state) if state and state.state not in ("unknown", "unavailable") else 0.0

        valeur_importee = val("sensor.valeur_energie_importee")
        prime_fixe = val("sensor.prime_fixe")
        taxe = val("sensor.taxe_communale") / 100.0

        base = valeur_importee + prime_fixe
        self._attr_state = round(base * taxe, 0)


class MontantTGCSensor(BaseSensor):
    def __init__(self, hass):
        super().__init__("Montant TGC", "XPF", "montant_tgc")
        self.hass = hass

    async def async_update(self):
        def val(e):
            state = self.hass.states.get(e)
            return float(state.state) if state and state.state not in ("unknown", "unavailable") else 0.0

        valeur_importee = val("sensor.valeur_energie_importee")
        prime_fixe = val("sensor.prime_fixe")
        taxe_communale = val("sensor.montant_taxe_communale")
        redevance = val("sensor.redevance_comptage")
        tgc = val("sensor.taux_tgc") / 100.0

        base = valeur_importee + prime_fixe + taxe_communale + redevance
        self._attr_state = int(round(base * tgc, 0))

# --------------------
# Setup
# --------------------
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    puissance_kva = entry.data.get(CONF_PUISSANCE_KVA)
    commune = entry.data.get(CONF_COMMUNE)
    prix_rachat = entry.data.get(CONF_PRIX_RACHAT)
    sensor_import = entry.data.get(CONF_SENSOR_IMPORT)
    sensor_export = entry.data.get(CONF_SENSOR_EXPORT)
    reset_day = entry.data.get(CONF_RESET_DAY, 1)

    sensors = [
        PrimeFixeSensor(puissance_kva),
        PrixAchatSensor(puissance_kva),
        RedevanceComptageSensor(),
        TauxTGCSensor(),
        TaxeCommunaleSensor(commune),
        PrixRachatConfigSensor(prix_rachat),
        EnergyFromPowerSensor(hass, sensor_import, reset_day),
        ValeurEnergieImporteeSensor(hass, "sensor.energie_importee", prix_rachat),
        MontantTaxeCommunaleSensor(hass),
        MontantTGCSensor(hass),
        FactureTotalSensor(hass)
    ]

    if sensor_export:
        sensors.append(EnergyFromExportSensor(hass, sensor_export, reset_day))
        sensors.append(ValeurExportSensor(hass, sensor_export, prix_rachat))

    async_add_entities(sensors)