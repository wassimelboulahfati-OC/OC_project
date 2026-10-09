# Sport Data Solution — POC d'infrastructure de données

Pipeline de données automatisé et reproductible qui transforme des fichiers métier (Excel RH et activités sportives) en un rapport décisionnel Power BI, afin de piloter deux dispositifs d'entreprise encourageant la pratique sportive des salariés.

---

## Contexte métier

L'entreprise souhaite encourager ses salariés à pratiquer une activité sportive et en piloter les effets à travers deux dispositifs :

- **Prime au mode actif** — prime versée aux salariés venant travailler à pied, en courant, à vélo ou en trottinette, calculée selon la distance domicile-travail.
- **Congé « bien-être »** — 5 jours de congé accordés aux salariés dépassant un seuil d'activités sportives sur la période.

Le besoin ne se limite pas à calculer ces montants une fois : il faut pouvoir **recalculer l'ensemble des indicateurs dès qu'une règle métier ou une source évolue**.

### Deux exigences opérationnelles
1. Un rapport Power BI de 3 pages (Synthèse, Éligibilité & répartition, Qualité des données).
2. Un pipeline relançable à la demande.

---

## Architecture

```
Sources            Ingestion              PostgreSQL (médaillon)        Reporting
───────            ─────────              ──────────────────────        ─────────
Excel RH      ┐                     ┌─> raw ─> staging ─> intermediate ─> marts ─> Power BI
Excel activités├──> sds-runner ─────┤                                              (mode Import)
API OpenRoute ┘    (Python/Docker)  └─> distances domicile-travail (ORS + Haversine)

        Orchestration : Kestra (flows YAML)  ·  Conteneurisation : Docker Compose
                          Notification : Slack (digest quotidien)
```

### Choix techniques
- **Pattern médaillon** pour la traçabilité et la qualité couche par couche.
- **dbt** pour une logique métier versionnée et paramétrable.
- **Docker** pour la reproductibilité de l'environnement.
- **Kestra** pour orchestrer l'ensemble en YAML versionnable.

---

## Stack technique

| Composant        | Rôle                                                        |
|------------------|-------------------------------------------------------------|
| PostgreSQL       | Système de référence (pattern médaillon)                    |
| dbt (postgres)   | Transformations et logique métier (staging → marts)         |
| Python           | Ingestion des sources, géocodage et calcul de distances     |
| Kestra           | Orchestration des flux (pipeline + digest Slack)            |
| Docker Compose   | Conteneurisation de l'ensemble                              |
| OpenRouteService | Calcul de distance routière domicile-travail                |
| Nominatim        | Géocodage des adresses                                      |
| Power BI         | Restitution décisionnelle (mode Import)                     |
| Slack            | Notification quotidienne des activités de la veille         |

---

## Le pattern médaillon

| Couche        | Contenu                                          | Rôle                                           |
|---------------|--------------------------------------------------|------------------------------------------------|
| `raw`         | Excel RH, Excel activités, distances ORS         | Données brutes, fidèles à la source            |
| `staging`     | Vues dbt `stg_*` (1 par source)                  | Nettoyage, typage, renommage                   |
| `intermediate`| Salariés × distances × activités                 | Jointures et calculs intermédiaires            |
| `marts`       | Tables finales exposées à Power BI               | Règle métier versionnée, recalculable          |

### Tables exposées (marts)
- `mart_eligibilite_prime`
- `mart_impact_financier`
- `mart_eligibilite_bien_etre`
- `mart_anomalies`

**Idempotence** : les schémas dbt sont recréés à chaque run et les chargements se font en mode `replace`. Le pipeline peut être relancé sans produire de doublons ni d'effet de bord.

---

## Règles métier paramétrables

Les règles métier sont déclarées comme variables dans `dbt/dbt_project.yml`, lisibles et modifiables sans toucher au SQL :

```yaml
vars:
  taux_prime: 0.05          # % du salaire brut annuel
  seuil_jours_bien_etre: 15 # nb d'activités mini pour les 5 jours bien-être
  nb_jours_bien_etre: 5     # nb de jours accordés
  plafond_marche_km: 15     # distance max marche / course à pied
  plafond_velo_km: 25       # distance max vélo / trottinette / autres
  nb_jours_ouvres_an: 218   # base de calcul du coût d'une journée (standard FR)
```

Elles sont appelées dans les modèles via `{{ var('…') }}`. **Changer une valeur puis relancer le pipeline recalcule l'ensemble des indicateurs.**

---

## Prérequis

- Docker et Docker Compose
- Power BI Desktop (pour ouvrir le rapport)
- (Optionnel, pour exécuter dbt en local) Python 3.x et dbt-postgres
- Une clé API [OpenRouteService](https://openrouteservice.org/)

---

## Configuration

Les secrets ne sont jamais versionnés. Créer un fichier `.env` à la racine (listé dans `.gitignore`) :

```dotenv
# PostgreSQL (données)
DATA_DB_HOST=localhost
DATA_DB_PORT=5433
DATA_DB_USER=sds_admin
DATA_DB_PASSWORD=<votre_mot_de_passe>
DATA_DB_NAME=sport_data

# Rôle applicatif à droits limités
SDS_APP_PASSWORD=<votre_mot_de_passe_app>

# OpenRouteService
ORS_API_KEY=<votre_cle_ors>
ORS_VERIFY_SSL=true

# Slack
SLACK_WEBHOOK_URL=<votre_webhook_slack>
SLACK_VERIFY_SSL=true
```

> **Note sur les secrets Kestra** : les secrets attendus par Kestra sont fournis encodés en base64 dans un fichier `.env_encoded` (non versionné), injecté au démarrage du conteneur et appelés dans les flux via `{{ secret('…') }}`.
>
> ⚠️ Lors de la génération de `.env_encoded`, découper chaque valeur **au premier `=`** uniquement (et non via `Split('=')`) afin de ne pas tronquer les valeurs base64 / JWT qui peuvent se terminer par `=`.

---

## Démarrage

Depuis la racine du projet :

```bash
# Démarrer l'ensemble des services
docker compose up -d

# Vérifier l'état des conteneurs
docker compose ps
```

Services attendus en statut **Up** : `sds_postgres_kestra`, `sds_postgres_data`, `sds_kestra`.

L'interface Kestra est disponible sur **http://localhost:8090**.

---

## Utilisation

### Lancer le pipeline complet

Dans Kestra (http://localhost:8090), exécuter le flow **`sport_data_pipeline`**. Enchaînement des tâches :

1. Reset des schémas dbt
2. Ingestion des sources dans `raw`
3. Calcul des distances domicile-travail (ORS + fallback Haversine)
4. `dbt run` : `staging → intermediate → marts`

À l'issue du run, les marts sont prêts pour Power BI.

### Notification Slack

Le flow **`slack_digest`** (cron quotidien à 08:00) envoie **un message Slack par activité de la veille** :

```sql
WHERE date_activite::date = current_date - interval '1 day'
```

### Changer une règle métier (ex. le taux de prime)

1. Modifier la variable dans `dbt/dbt_project.yml` (ex. `taux_prime: 0.05 → 0.1`).
2. Reconstruire l'image qui embarque le code dbt :
   ```bash
   docker build -t sds-runner:latest -f docker/Dockerfile .
   ```
3. Relancer le flow `sport_data_pipeline` dans Kestra.
4. Vérifier le recalcul en base :
   ```bash
   docker exec -it sds_postgres_data psql -U sds_admin -d sport_data \
     -c "SELECT sum(montant_prime) FROM marts.mart_eligibilite_prime;"
   ```
5. Actualiser le rapport Power BI (bouton **Actualiser**, mode Import).

---

## Exécuter dbt en local (optionnel)

dbt ne lit pas automatiquement le fichier `.env`. Les variables d'environnement doivent être présentes dans la session courante.

**PowerShell :**
```powershell
$env:DATA_DB_PASSWORD = "<votre_mot_de_passe>"
cd dbt
dbt run --profiles-dir .
```

**Pour charger automatiquement les variables depuis `.env` (PowerShell) :**
```powershell
Get-Content .\.env | Where-Object { $_ -match '^DATA_DB_' } | ForEach-Object {
    $i = $_.IndexOf('=')
    Set-Item -Path "Env:$($_.Substring(0,$i))" -Value $_.Substring($i+1)
}
```

---

## Calcul des distances & robustesse

Le calcul de la distance domicile-travail se fait en deux temps :

1. **Géocodage** de l'adresse du salarié via Nominatim (coordonnées GPS).
2. **Routing** via OpenRouteService (distance routière réelle).

En cas d'échec ORS (403, timeout…), le pipeline bascule automatiquement sur un **fallback Haversine** (distance à vol d'oiseau) : le run se termine quand même. Les adresses imprécises sont détectées et signalées dans `mart_anomalies` (page 3 de Power BI).

---

## Rapport Power BI

Fichier Power BI connecté en **mode Import** sur PostgreSQL (`localhost:5433`).

- **Page 1 — Synthèse** : cartes KPI (coûts bien-être / primes / total, effectifs bénéficiaires).
- **Page 2 — Éligibilité & répartition** : donut d'éligibilité à la prime, primes et activités par direction.
- **Page 3 — Qualité des données** : tableau des anomalies (adresses à corriger) + comptage.

> Après chaque relance du pipeline, actualiser manuellement le rapport (mode Import).

---

## Sécurité

- Aucun secret en clair dans le dépôt : `.env` non versionné (`.gitignore`).
- Secrets Kestra fournis via `.env_encoded` (base64), appelés par `{{ secret('…') }}`.
- Rôle PostgreSQL applicatif `sds_app` à droits limités (principe du moindre privilège).
- Script d'initialisation de la base en `.sh` qui lit les variables d'environnement au lieu d'un mot de passe en dur.

---

## Limites assumées (POC)

- Actualisation Power BI manuelle (mode Import).
- Données d'activités simulées.
- Secrets gérés via l'environnement du conteneur plutôt que nativement dans Kestra (édition open-source).
- Base reconstruite entièrement à chaque run (`truncate` / `replace`) — choix assumé face aux Excel métier, un merge incrémental étant risqué à purger en cas d'erreur de saisie.

## Évolutions envisagées

- Connexion de l'**API Strava** pour récupérer automatiquement les activités (en remplacement des données simulées).
- Gestion native des secrets (Kestra entreprise).
- Ingestion incrémentale (merge) quand les sources le permettent.
- Rafraîchissement automatique de Power BI via gateway.
- Code dbt monté en volume (éviter un rebuild à chaque changement).

---

## Structure du projet

```
.
├── docker-compose.yml
├── .env                      # non versionné
├── .env_encoded              # non versionné (secrets Kestra, base64)
├── docker/
│   └── Dockerfile            # image sds-runner
├── postgres/
│   └── init/
│       └── 01-schemas.sh     # schémas + rôle applicatif (via variables d'env)
├── python/
│   ├── ors_client.py         # géocodage + distances (ORS / Haversine)
│   ├── simulate_activities.py
│   └── post_slack.py
├── dbt/
│   ├── dbt_project.yml       # variables métier
│   ├── profiles.yml
│   └── models/
│       ├── 01_staging/
│       ├── 02_intermediate/
│       └── 03_marts/
├── kestra/
│   └── flows/
│       ├── sport_data_pipeline.yml
│       └── slack_digest.yml
└── powerbi/
    └── sport_data_solution.pbix
```

---

