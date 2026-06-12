# 🍷 BottleNeck — Pipeline d'automatisation du reporting commercial

Pipeline de données **orchestré, testé et planifié** qui réconcilie les ventes d'un marchand de vin issues de deux systèmes hétérogènes (ERP + CMS), calcule le chiffre d'affaires par produit et détecte statistiquement les vins « premium » (millésimes).

> **Objectif métier** : remplacer un rapprochement manuel mensuel — lent, non reproductible et source d'erreurs — par un pipeline automatisé qui garantit la justesse des données, chaque mois, sans supervision.

---

## 📊 Chiffres clés du run nominal

| Indicateur | Valeur |
|---|---|
| Lignes ERP | 825 |
| Lignes WEB (brutes → nettoyées) | 1428 → 714 |
| Lignes liaison | 825 |
| Lignes après fusion | 714 |
| Chiffre d'affaires total | **70 568,60 €** |
| Vins premium détectés (z > 2) | **30** |
| Tâches du pipeline | 31 |
| Tests fail-fast | 6 |

---

## 🛠️ Stack technique

| Outil | Rôle | Principe |
|---|---|---|
| **Kestra** | Orchestrateur | Pilote, ordonnance, retente, planifie. Ne calcule rien. |
| **DuckDB** | Moteur SQL embarqué | Lit le XLSX, nettoie, dédoublonne, joint, agrège. |
| **Python + pandas** | Calcul statistique | Une seule tâche : le z-score. |
| **Docker Compose** | Déploiement | Stack reproductible (Kestra + PostgreSQL). |
| **PostgreSQL** | Backend Kestra | Historique des exécutions, logs, état. |

**Principe directeur** : chaque outil fait une seule chose, et la fait bien. Aucun calcul dans l'orchestrateur.

---

## 🔄 Logigramme synthétique

```
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ Ingestion ERP│   │ Ingestion WEB│   │Ingestion LIAI│
   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
          └──────────────────┼──────────────────┘
                             ▼
                    ┌─────────────────┐
                    │  TEST non-vacuité│  n > 0
                    └────────┬─────────┘
                             ▼
              ┌──────────────────────────────┐
              │  Nettoyage & dédoublonnage    │  WHERE · CAST · DISTINCT
              └──────────────┬────────────────┘
                             ▼
                    ┌─────────────────┐
                    │ TEST volumétrie  │  825 · 714 · 825
                    └────────┬─────────┘
                             ▼
              ┌──────────────────────────────┐
              │  Fusion — INNER JOIN liaison  │  erp ⋈ lia ⋈ web
              └──────────────┬────────────────┘
                             ▼
                    ┌─────────────────┐
                    │  TEST fusion     │  n = 714
                    └────────┬─────────┘
                             ▼
              ┌──────────────────────────────┐
              │  Calcul CA = prix × ventes    │
              └──────────────┬────────────────┘
                             ▼
                    ┌─────────────────┐
                    │  TEST CA total   │  70 568,60 €
                    └────────┬─────────┘
                             ▼
              ┌──────────────────────────────┐
              │  Z-score (Python) — z > 2     │  🐍
              └──────────────┬────────────────┘
                             ▼
                    ┌─────────────────┐
                    │  TEST millésimes │  30 vins
                    └────────┬─────────┘
                             ▼
       ┌──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼
 📊 rapport_ca.xlsx  🍷 premium.csv  🍇 ordinaire.csv

 ── Chaque TEST en échec (KO) → ARRÊT IMMÉDIAT, aucune propagation en aval.
```

> Le logigramme détaillé au format éditable est disponible dans `docs/logigramme.drawio`.

---

## 🏗️ Architecture du pipeline

Le pipeline `bottleneck_pipeline` enchaîne **31 tâches** réparties en 5 groupes :

1. **Ingestion** — les 3 fichiers Excel sont chargés dans DuckDB via `read_xlsx(..., all_varchar=true)`, à partir des Namespace Files Kestra (`nsfile:///`).
2. **Nettoyage & dédoublonnage** — filtres `WHERE`, conversion de types (`CAST`), suppression des doublons (`DISTINCT`), filtre `post_type='product'` côté WEB.
3. **Fusion** — `INNER JOIN` ERP ⋈ liaison ⋈ WEB sur les identifiants (conservés en `VARCHAR`).
4. **Calcul CA & z-score** — agrégation SQL du chiffre d'affaires, puis calcul du z-score en Python.
5. **Exports** — génération du rapport Excel et des deux CSV.

---

## ✅ Stratégie de test — fail-fast

Six tests verrouillent chacun un invariant précis. Logique **fail-fast** : tout test en échec arrête immédiatement le pipeline, aucune donnée corrompue ne descend en aval.

| # | Famille de test | Implémentation | Valeur attendue |
|---|---|---|---|
| 1 | Non-vacuité (source brute) | `COUNT(*) FROM erp_raw` → fail si `n == 0` | `n > 0` |
| 2 | Volumétrie + unicité | `COUNT(*) == COUNT(DISTINCT clé) == N` | ERP=825 · WEB=714 · LIAISON=825 |
| 3 | Volumétrie intermédiaire | `COUNT(*)` sur `web_clean` (avant filtre) | 1428 |
| 4 | Cohérence post-jointure | `COUNT(*) == COUNT(DISTINCT product_id)` sur `fusion` | 714 |
| 5 | Cohérence métier — CA | `ROUND(SUM(CA_product), 2)` | 70 568,60 € |
| 6 | Cohérence métier — millésimes | `COUNT(*) WHERE is_premium = TRUE` | 30 vins |

**Élégance du système** : le test 2 couvre à lui seul trois invariants — le bon comptage, l'absence de doublon (`n == n_distinct`) et l'absence de NULL (sinon le compte changerait). Chaque test est un duo `Query` (qui lit) + `Fail` (qui arrête).

---

## 🧠 Décisions d'architecture

- **Dédoublonner avant la jointure, pas après** — éviter l'explosion cartésienne (1428 × 825) et garantir une volumétrie prévisible et testable.
- **`CAST` strict, pas `TRY_CAST`** — un `TRY_CAST` aurait silencieusement transformé une anomalie en `NULL`. On préfère une erreur visible à une perte invisible. (Ex. : un identifiant textuel `bon-cadeau-25-euros` détecté → identifiants traités en `VARCHAR`.)
- **Retry ciblé via `pluginDefaults`** — retry 3×10s uniquement sur les tâches DuckDB (panne technique transitoire ⇒ on retente), jamais sur les tâches `Fail` (échec métier déterministe ⇒ on arrête). *La résilience ne doit jamais masquer un bug métier.*
- **Déclenchement planifié** — trigger cron `0 9 15 * *` en timezone `Europe/Paris` (le 15 de chaque mois à 9h).
- **Zéro upload manuel** — sources versionnées dans Kestra via le protocole `nsfile:///`.

---

## 🚀 Installation & déploiement

### Prérequis
- Docker & Docker Compose installés

### Étapes

```powershell
# 1. Télécharger le docker-compose officiel de Kestra (PowerShell)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/kestra-io/kestra/develop/docker-compose.yml" -OutFile "docker-compose.yml"

# 2. Démarrer la stack en arrière-plan
docker compose up -d

# 3. Vérifier l'état des conteneurs
docker compose ps
```

> Le `docker-compose.yml` de ce projet est personnalisé :
> - ports remappés en `8090:8080` et `8091:8081`
> - bind-mount `./data:/app/data` pour persister la base DuckDB et les exports
> - PostgreSQL en version 18

### Accès
- Interface Kestra : **http://localhost:8090**

### Mise en place du flow
1. Déposer les 3 fichiers Excel sources dans les **Namespace Files** du namespace `bottleneck` :
   - `Fichier_erp.xlsx`
   - `Fichier_web.xlsx`
   - `fichier_liaison.xlsx`
2. Importer le flow `bottleneck_pipeline.yml`.
3. Lancer une exécution via le bouton **Execute**.

---

## 📦 Livrables générés

Les fichiers de sortie sont produits dans le dossier `./data/` (persisté via le volume Docker) :

| Fichier | Contenu |
|---|---|
| `rapport_ca.xlsx` | Chiffre d'affaires détaillé par produit (714 lignes) |
| `premium.csv` | Les 30 vins premium (z > 2) |
| `ordinaire.csv` | Les 684 vins ordinaires (z ≤ 2) |

---

## 📁 Structure du dépôt

```
.
├── bottleneck_pipeline.yml      # Workflow Kestra (31 tâches)
├── docker-compose.yml           # Stack Kestra + PostgreSQL (personnalisée)
├── docs/
│   ├── logigramme.drawio        # Diagramme de flux éditable
│   └── captures/                # Captures d'installation & d'exécution
├── data/                        # Base DuckDB + livrables (non versionné)
└── README.md
```

---

## 🔮 Limites & perspectives

**Limites de Kestra** : Kestra est avant tout un **orchestrateur**, pas un moteur de transformation. Il manque de scalabilité pour traiter de gros volumes. Pour industrialiser davantage, l'approche recommandée serait de le coupler à un outil de transformation dédié comme **dbt** (Kestra orchestre, dbt transforme, versionne et teste).

**Parallélisation** : les tâches indépendantes (ex. les 3 ingestions) pourraient être parallélisées. Ce choix n'a pas été retenu ici car le faible volume (quelques centaines de lignes) rend le gain négligeable ; c'est une optimisation activable en cas de montée en charge.

**Autres pistes d'extension** :
- 📧 Notification email en cas d'échec + envoi automatique du rapport
- ☁️ Dépôt cloud des livrables (Drive / S3) pour partage et archivage
- 🗂️ Table de rejets pour tracer les lignes écartées plutôt que les supprimer
- 📐 Hardening : harmoniser le nommage des sources (sensibilité à la casse), figer un schéma attendu


