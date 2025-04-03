# Facture Elec NC

**Facture Elec NC** est une intégration personnalisée Home Assistant qui calcule automatiquement votre facture d'électricité à partir de capteurs de puissance, des tarifs locaux et des paramètres configurables comme la commune, la puissance souscrite, et le prix de rachat.

---

## ⚡ Fonctionnalités

- 🧮 Calcul automatique de :
  - Valeur de l’énergie importée (XPF)
  - Prime fixe
  - Montant de la taxe communale
  - Redevance de comptage
  - Montant de la TGC
  - Valeur de l’énergie exportée (si configurée)
  - Facture totale mensuelle

- 🔁 Réinitialisation automatique des compteurs tous les mois
- 🏝️ Tarification spécifique à la Nouvelle-Calédonie
- 📊 Capteurs restaurables après redémarrage

---

## 📦 Capteurs créés

| Capteur                          | Description |
|---------------------------------|-------------|
| `sensor.energie_importee`       | Énergie importée (kWh) |
| `sensor.valeur_energie_importee`| Montant en XPF de l’énergie importée |
| `sensor.prime_fixe`             | Prime fixe mensuelle |
| `sensor.montant_taxe_communale` | Calcul de la taxe communale |
| `sensor.redevance_comptage`     | Montant de la redevance |
| `sensor.montant_tgc`            | TGC appliquée sur la base totalisée |
| `sensor.energie_exportee`       | Énergie exportée (kWh) — si activée |
| `sensor.valeur_exportee`        | Valeur exportée en XPF |
| `sensor.valeur_energie_nette`   | Différence entre import et export |
| `sensor.facture_totale`         | Total à payer |

---

## ⚙️ Configuration

### Via l'interface Home Assistant (config_flow)

- Choix de la commune (pour appliquer la taxe locale)
- Puissance souscrite : 3.3 / 6.6 / 9.9 kVA
- Prix de rachat de l’énergie (XPF/kWh)
- Capteur de puissance importée (obligatoire)
- Capteur de puissance exportée (optionnel)
- Jour de remise à zéro mensuelle (1 à 28)

---

## 🖼️ Interface

Cette intégration propose une icône personnalisée (`icon.png`) visible lors de l’ajout dans Home Assistant.

---

## 🔧 Installation

### Via HACS (recommandé)
1. Ajouter ce dépôt comme dépôt personnalisé
2. Type : Intégration
3. Installer
4. Redémarrer Home Assistant
5. Ajouter l’intégration "Facture Elec NC" via les paramètres

### Manuellement
1. Copier ce dépôt dans : `custom_components/facture_elec_nc`
2. Redémarrer Home Assistant

---

## 🧑‍💻 Dépendances
- Aucune dépendance externe

---

## 📄 Licence
MIT

---

## 🤝 Codeowner
Maintenu par **NeurHome**

> Nouvelle-Calédonie • Énergie • Automatisation
