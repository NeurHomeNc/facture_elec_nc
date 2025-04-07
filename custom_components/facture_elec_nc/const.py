DOMAIN = "facture_elec_nc"

CONF_COMMUNE = "commune"
CONF_PUISSANCE_KVA = "puissance_kva"
CONF_PRIX_REVENTE = "prix_revente"
CONF_SENSOR_IMPORT = "sensor_import"
CONF_SENSOR_EXPORT = "sensor_export"
CONF_RESET_DAY = "reset_day"

COMMUNES = [
    "Nouméa", "Mont-Dore", "Dumbéa", "Païta", "Lifou", "Koné", "Bourail", "Poindimié", "Maré", "Houaïlou",
    "La Foa", "Canala", "Poya", "Hienghène", "Ponérihouen", "Koumac", "Thio", "Ouvéa", "Kouaoua", "Voh",
    "Boulouparis", "Yaté", "Île des Pins", "Kaala-Gomen", "Moindou", "Touho", "Ouégoa", "Farino", "Sarraméa"
]

PUISSANCES_KVA = {
    "3,3": "3,3 kVA",
    "6,6": "6,6 kVA",
    "9,9": "> 6,6 kVA"
}

PRIX_REVENTE_CHOICES = [15, 21]