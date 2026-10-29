# 🛒 SuperSmartMarket – Audit des écarts de chiffre d'affaires sur le cube OLAP

> Mission d'audit de données réalisée pour **SuperSmartMarket**, enseigne de distribution alimentaire et de grande consommation.
> Recherche de la cause des variations du chiffre d'affaires sur des journées déjà clôturées, à l'aide d'un prototype de base de données sur **Google BigQuery**.

**Date :** Novembre 2025

---

## 📌 Contexte

SuperSmartMarket veut placer la donnée au cœur de sa stratégie pour proposer une expérience client hyper-personnalisée. L'entreprise rencontre pourtant un **problème critique** : **son chiffre d'affaires est instable**. Le CA d'une journée clôturée peut encore changer le lendemain, ce qui rend les indicateurs financiers peu fiables.

### Objectifs de la mission

- Auditer l'architecture et les flux de données existants
- Identifier les incohérences dans le chiffre d'affaires
- Construire un **dictionnaire des données** et un **schéma relationnel** cohérent
- Vérifier les chiffres clés grâce à un **prototype de base de données**
- Restaurer la confiance dans les indicateurs financiers

---

## 🏗️ Architecture existante

```
Caisses / Site web / ERP
          │
          ▼
  SQL Server (base live, OLTP)
          │   ← traitements batch planifiés (scheduler)
          ▼
  Cube OLAP (Azure Analysis Services)
          │
          ▼
  Power BI (Dataviz / reporting)
```

| Composant | Rôle |
|---|---|
| **SQL Server** | Stocke les données opérationnelles (magasins, site web, ERP) et sert de référentiel central |
| **Site web & ERP** | Produisent et utilisent les données clients, ventes et processus internes |
| **Cube OLAP (Azure Analysis Services)** | Organise les données en dimensions (temps, client, produit, employé) et en mesures (CA, quantités) |
| **Power BI** | Visualisation et reporting pour les équipes métier |

---

## 🧭 Démarche

1. Analyse de l'architecture et des flux de données
2. Rédaction du **dictionnaire des données**
3. Reconstitution du **schéma relationnel**
4. Création d'un **prototype dans BigQuery** (tables, clés primaires et étrangères)
5. **Requêtes SQL** pour recalculer les indicateurs clés
6. Intégration et analyse des **logs** pour retrouver l'origine des écarts
7. Rédaction du **rapport d'audit** et des recommandations

---

## 🗄️ Prototype de base de données (BigQuery)

| Table | Type | Clé primaire | Clés étrangères |
|---|---|---|---|
| `CLIENT` | Dimension | `CUSTOMER_ID` | – |
| `PRODUIT` | Dimension | `EAN` | – |
| `EMPLOYE` | Dimension | `id_employe` | – |
| `CALENDRIER` | Dimension | `date` | – |
| `VENTE_DETAIL` | Fait | `ID_BDD` | `CUSTOMER_ID`, `EAN`, `id_employe`, `date` |
| `LOGS` | Technique | – | Événements d'insertion, de mise à jour et de suppression |

### Pourquoi BigQuery pour le prototype ?

- **Serverless** : aucune infrastructure à gérer, contrairement à SQL Server
- **Scalable** : traite de gros volumes sans contrainte de stockage
- **Rapide** : moteur optimisé pour les requêtes analytiques, adapté à un POC
- **Compatible** : se connecte facilement à Power BI ou Looker Studio

---

## 📖 Dictionnaire des données (extrait)

### Table `VENTE_DETAIL`

| Code | Signification | Type | Longueur | Nature |
|---|---|---|---|---|
| `ID_BDD` | Identifiant unique de la transaction | varchar | 20 | Incrémentale |
| `CUSTOMER_ID` | Identifiant unique du client | varchar | 50 | Incrémentale |
| `id_employe` | Identifiant unique de l'employé | varchar | 50 | Incrémentale |
| `EAN` | Identifiant unique du produit | varchar | 100 | Incrémentale |
| `Date achat` | Code date au format standard Excel | integer | – | Élémentaire |
| `ID ticket` | Identifiant unique du ticket | varchar | 50 | Incrémentale |

### Table `CALENDRIER` (avec mesure corrective)

| Code | Signification | Type |
|---|---|---|
| `date` | Code date au format standard Excel | integer |
| `annee` / `mois` / `Jour` | Année, mois, jour | integer |
| `mois_nom` | Nom du mois | varchar(10) |
| `annee_mois` | Code année-mois | integer |
| `jour_semaine` | Numéro du jour de la semaine | integer |
| `trimestre` | Trimestre | varchar(2) |
| **`date_complete`** ✨ | **Date complète au format `YYYY-MM-DD`** (mesure corrective) | **date** |

> 📎 Le dictionnaire complet (Employé, Calendrier, Clients, Produits, Vente détail) se trouve dans `docs/dictionnaire_de_donnees.xlsx`.

---

## 🔍 Requêtes SQL

Les requêtes du dossier `sql/` recalculent les indicateurs clés pour la journée du **14 août** :

- 📊 le **chiffre d'affaires total** de la journée ;
- 👥 le **top 10 des clients** par CA ;
- 🧑‍💼 la **part du CA encaissée par chaque employé** ;
- 🕵️ le **CA par jour avec la table de logs**, pour comparer la date de transaction et la date d'insertion.

Exemple : convertir la date Excel et calculer le CA par jour

```sql
-- Conversion du code date Excel (integer) en vrai type DATE
-- puis calcul du chiffre d'affaires par jour
SELECT
  DATE_ADD(DATE '1899-12-30', INTERVAL vd.date_achat DAY) AS date_vente,
  ROUND(SUM(p.prix), 2) AS chiffre_affaires
FROM `projet.dataset.VENTE_DETAIL` AS vd
JOIN `projet.dataset.PRODUIT` AS p
  ON vd.EAN = p.EAN
GROUP BY date_vente
ORDER BY date_vente;
```

---

## 🚨 Constats de l'audit

| # | Constat | Impact |
|---|---|---|
| 1 | **Logs mélangés et non normalisés** : une seule table regroupe des événements hétérogènes, et la colonne `detail` contient tantôt une date, tantôt un prix, tantôt un identifiant | Analyses complexes, jointures risquées, anomalies difficiles à isoler |
| 2 | **Aucune colonne au format DATE** dans la table calendrier : les dates sont des codes Excel typés en integer | Analyses temporelles peu fiables, risque de confusion dans les agrégations |
| 3 | **Décalage entre transaction et insertion** : des ventes du 14/08 sont insérées le 15/08, probablement à cause du paramétrage du scheduler | Le CA d'un jour clôturé continue d'évoluer, ce qui fausse le pilotage |

**Évaluation des risques :** impact **élevé**, probabilité **élevée** (le problème est structurel et se répète).

👉 Les logs ont servi de **preuve** : les écarts ne viennent pas des calculs, mais du **processus d'intégration des données**.

---

## ✅ Recommandations

1. **Normaliser les logs et les intégrer au MDD** : créer une table de logs par entité, ou enrichir la table existante avec des colonnes `ancienne_valeur`, `nouvelle_valeur` et `type_valeur`
2. **Ajouter une colonne `date_complete` (DATE)** dans la table calendrier
3. **Mettre en place des contrôles d'intégrité** : requêtes régulières pour vérifier les clés primaires et étrangères, les doublons et les anomalies de chargement
4. **Vérifier le paramétrage du scheduler** pour que les traitements ne démarrent qu'une fois toutes les ventes de la journée enregistrées
5. **Séparer la date métier et la date technique** avec deux colonnes, `date_transaction` et `date_insertion`

### ⚖️ Avantages et limites

| Avantages | Limites |
|---|---|
| Calculs de CA plus fiables | Effort de mise en œuvre technique et organisationnel |
| Traçabilité renforcée grâce aux logs dans le MDD | Temps nécessaire pour vérifier le scheduler et les batchs |
| Meilleure gouvernance (contrôles, typage) | Modèle plus complexe avec la table de logs |
| Distinction claire entre date métier et date technique | Dépendance aux contraintes des systèmes existants |

---

## 🔮 Perspectives

- Refonte progressive de l'**architecture décisionnelle**
- **Monitoring et alertes automatiques** pour détecter les anomalies au plus tôt
- Évolution graduelle du modèle décisionnel selon les priorités et les ressources

---

## 📁 Structure du repo

```
├── docs/
│   ├── rapport_audit.docx            # Rapport d'audit complet
│   ├── presentation.pptx             # Support de soutenance
│   ├── dictionnaire_de_donnees.xlsx  # Dictionnaire des données
│   └── schema_relationnel.png        # Schéma relationnel
├── sql/
│   ├── 01_creation_tables.sql        # Création des tables BigQuery
│   ├── 02_requetes_ca.sql            # CA total, top 10 clients, CA par employé
│   └── 03_analyse_logs.sql           # Analyse des écarts avec les logs
└── README.md
```

---

## 🛠️ Stack technique

![BigQuery](https://img.shields.io/badge/Google%20BigQuery-4285F4?logo=googlecloud&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL%20Server-CC2927?logo=microsoftsqlserver&logoColor=white)
![Azure](https://img.shields.io/badge/Azure%20Analysis%20Services-0078D4?logo=microsoftazure&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?logo=powerbi&logoColor=black)
![SQL](https://img.shields.io/badge/SQL-336791?logo=postgresql&logoColor=white)

---

