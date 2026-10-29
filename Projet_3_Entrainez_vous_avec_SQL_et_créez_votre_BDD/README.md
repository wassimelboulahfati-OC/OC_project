# 🏠 DataImmo – Base de données nationale des transactions immobilières

> Proof of Concept réalisé pour **Laplace Immo**, réseau national d'agences immobilières.
> Création, alimentation et exploitation d'une base de données relationnelle sur **Google BigQuery**.

**Date :** Octobre 2025

---

## 📌 Contexte

Laplace Immo veut **exploiter ses données** pour mieux accompagner ses clients et se démarquer de la concurrence.

L'objectif du projet est de créer une **base de données nationale des transactions immobilières** afin de :

- suivre l'évolution du **prix au m²** ;
- identifier les **zones dynamiques** du marché ;
- répondre aux **besoins des agences régionales**.

---

## 🧭 Démarche

1. Étude des fichiers Excel fournis et rédaction d'un **dictionnaire de données**
2. Conception d'un **schéma relationnel normalisé**
3. **Nettoyage et transformation** des données
4. **Chargement** des données dans BigQuery
5. Rédaction et exécution de **requêtes SQL** pour répondre aux besoins métier

---

## 📂 Données sources

| Source | Description | Format |
|---|---|---|
| Valeurs foncières | Transactions immobilières (prix, surface, type de bien, date…) | Excel (.xlsx) |
| Données communes | Données démographiques et géographiques des communes | Excel (.xlsx) |
| Référentiel géographique | Régions, départements, codes INSEE | Excel (.xlsx) |

**Volumétrie :**
- Transactions : ~35 000
- Communes : ~35 000
- Régions : 13 régions métropolitaines + DOM

**Période couverte :** 1er semestre 2020
**Types de biens :** appartements, maisons, locaux commerciaux…

---

## 📖 Extrait du dictionnaire de données (table `donnees_commune`)

| Code | Signification | Type | Longueur |
|---|---|---|---|
| `id_commune` | Identifiant unique de la table | Varchar | 5 |
| `CODREG` | Code région | Varchar | 2 |
| `CODDEP` | Code département | Varchar | 2 |
| `CODARR` | Code arrondissement | Varchar | 2 |
| `CODCAN` | Code du canton | Varchar | 2 |
| `CODCOM` | Code commune | Varchar | 3 |
| `COM` | Nom de la commune | Varchar | 100 |
| `PMUN` | Population municipale | Entier | – |
| `PCAP` | Population comptée à part | Entier | – |
| `PTOT` | Population totale | Entier | – |

---

## 🗄️ Modèle de données

Base hébergée sur **BigQuery (Google Cloud Platform)**, modèle relationnel normalisé en **3 tables** :

| Table | Contenu |
|---|---|
| `valeurs_foncieres` | Transactions immobilières : prix, surface, type de bien, date… |
| `donnees_commune` | Données démographiques et géographiques des communes |
| `referentiel_geographique` | Référentiel des régions, départements et codes INSEE |

```
referentiel_geographique  1 ──── N  donnees_commune  1 ──── N  valeurs_foncieres
```

> 📎 Le schéma relationnel complet est disponible dans `docs/schema_relationnel.png`.

---

## 🔍 Requêtes SQL et analyses

Les requêtes SQL (dans le dossier `sql/`) répondent aux besoins métier, notamment :

- analyse des ventes par **période** (évolution trimestrielle) ;
- répartition des ventes par **type de bien** ;
- analyse par **région**, **département** et **commune** ;
- répartition des appartements par **nombre de pièces** ;
- calcul du **prix moyen au m²** par zone géographique ;
- identification des **zones les plus dynamiques**.

Exemple de requête :

```sql
-- Prix moyen au m² par région pour les appartements
SELECT
  rg.nom_region,
  ROUND(AVG(vf.valeur_fonciere / vf.surface_reelle_bati), 2) AS prix_moyen_m2
FROM `projet.dataset.valeurs_foncieres` AS vf
JOIN `projet.dataset.donnees_commune` AS dc
  ON vf.id_commune = dc.id_commune
JOIN `projet.dataset.referentiel_geographique` AS rg
  ON dc.CODREG = rg.code_region
WHERE vf.type_local = 'Appartement'
  AND vf.surface_reelle_bati > 0
GROUP BY rg.nom_region
ORDER BY prix_moyen_m2 DESC;
```

---

## 📁 Structure du repo

```
├── data/                  # Fichiers sources (Excel / CSV nettoyés)
├── docs/                  # Dictionnaire de données, schéma relationnel, support de soutenance
├── sql/                   # Scripts de création des tables et requêtes d'analyse
└── README.md
```

---

## 🚀 Reproduire le projet

1. Créer un projet sur **Google Cloud Platform** et activer **BigQuery**
2. Créer un dataset (ex. `dataimmo`)
3. Importer les fichiers nettoyés de `data/` dans les 3 tables
4. Exécuter les requêtes du dossier `sql/` dans la console BigQuery

---

## ✅ Résultats

- Création d'une base relationnelle normalisée (**DataImmo**)
- Intégration et nettoyage des données issues de fichiers Excel
- Mise en évidence des **dynamiques régionales** du marché immobilier
- Identification des **zones à fort potentiel** pour les agences
- Calculs **fiables et reproductibles** grâce à une base structurée
- Premiers **indicateurs exploitables** pour la prise de décision stratégique

---

## 🔮 Perspectives

**Prochaines étapes :**
- Automatiser l'ingestion des données (**pipeline ETL** régulier)
- Étendre la période d'analyse (données **2021–2025**)
- Intégrer des indicateurs économiques et sociaux (revenus, taux de vacance…)
- Développer des **tableaux de bord interactifs** (Power BI, Looker Studio…)

**Pistes à explorer :**
- Modélisation de la **valeur immobilière prévisionnelle**
- Analyse de la **demande locative** par zone
- **Recommandation personnalisée** pour les clients des agences

---

## 🛠️ Stack technique

![BigQuery](https://img.shields.io/badge/Google%20BigQuery-4285F4?logo=googlecloud&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-336791?logo=postgresql&logoColor=white)
![Excel](https://img.shields.io/badge/Excel-217346?logo=microsoftexcel&logoColor=white)

---
