# ⚡️ Facture Électricité NC — Intégration Home Assistant

Une intégration personnalisée pour Home Assistant permettant de calculer automatiquement la facture d'électricité en Nouvelle-Calédonie selon la commune, la puissance souscrite, la consommation (import et export), les taxes locales, la redevance comptage et la TGC.

---

## 📦 Fonctionnalités

- Récupération automatique des tarifs depuis [`https://neurhome.nc/data_elec.php`](https://neurhome.nc/data_elec.php)
- Suivi de la **consommation d'énergie importée et exportée (en kWh)** à partir de capteurs de puissance
- Calcul automatique :
  - ✅ Prime fixe
  - ✅ Valeur énergie importée
  - ✅ Taxe communale
  - ✅ Redevance comptage
  - ✅ Montant TGC
  - ✅ Valeur énergie exportée
  - ✅ 💰 Total de la facture
- Remise à zéro **mensuelle** des compteurs à un jour configurable
- Bouton de **remise à zéro manuelle** (met aussi à jour le jour de reset)

---

## 🧾 Entités créées

| Entité                            | Unité | Description |
|----------------------------------|-------|-------------|
| `sensor.prime_fixe`              | XPF   | Montant de la prime fixe |
| `sensor.energie_importee_kwh`    | kWh   | Énergie importée cumulée |
| `sensor.energie_exportee_kwh`    | kWh   | Énergie exportée cumulée |
| `sensor.valeur_energie_importee` | XPF   | Montant de l’énergie importée |
| `sensor.valeur_energie_exportee` | XPF   | Montant de l’énergie exportée (valeur négative) |
| `sensor.taxe_communale`          | XPF   | Taxe communale en fonction de la commune |
| `sensor.redevance_comptage`      | XPF   | Redevance fixe annuelle |
| `sensor.montant_tgc`             | XPF   | TGC sur l’ensemble de la facture |
| `sensor.total_facture`           | XPF   | Somme totale (import - export + taxes) |
| `button.remise_a_zero_manuelle`  | -     | Bouton pour remise à zéro manuelle |

---

## ⚙️ Paramètres configurables

Lors de l'ajout de l'intégration :

- **Commune** 
- **Puissance souscrite**
- **Prix de revente** 
- **Capteur de puissance (import)** 
- **Capteur de puissance (export)** optionnel
- **Jour de remise à zéro** mensuelle (par défaut le 1)

> 🔁 Ces paramètres sont **modifiables à tout moment** depuis l’interface (⚙️ Options de l’intégration).

---

## 🔘 Bouton : Remise à zéro manuelle

En cliquant sur le bouton `Remise à zéro manuelle` :

- Les entités `energie_importee_kwh` et `energie_exportee_kwh` sont remises à 0
- Le **jour de reset** est mis à jour avec le jour actuel (sauf 30/31 → 29)

---

## 🔧 Installation manuelle

1. Copie ce dépôt dans `config/custom_components/facture_elec_nc`
2. Redémarre Home Assistant
3. Ajoute l’intégration via *Paramètres > Appareils & services > Ajouter une intégration > Facture Électricité NC*

---

## 📁 Fichiers principaux

- `__init__.py` : initialisation et rechargement automatique
- `sensor.py` : création des entités et logique métier
- `button.py` : entité pour remise à zéro manuelle
- `config_flow.py` : interface de configuration initiale
- `options_flow.py` : interface de modification des paramètres
- `.translations/fr.json` : labels traduits pour l’interface

---

## 💡 Remarques

- Le calcul repose sur des données publiques fournies par `neurhome.nc`
- Toutes les valeurs monétaires sont en CFP (XPF)
- Cette intégration n’est pas encore validée officiellement par l’équipe Home Assistant

---

## 🧪 Support

Créé avec ❤️ pour la Nouvelle-Calédonie 🇳🇨  
Pour toute suggestion ou bug : crée une *issue* ou contacte le développeur.
