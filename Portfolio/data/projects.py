"""Catalogue des projets du parcours Data Engineer.

Contenu issu des README et du code de chaque dossier de projet.
Pour ajouter ou modifier un projet, il suffit d'éditer cette liste.
"""

CATEGORIES = [
    "Analyse & modélisation",
    "Bases de données & stockage",
    "Pipelines & orchestration",
    "Cloud & infrastructure",
    "ML & IA",
    "Audit & gouvernance",
]

PROJECTS = [
    {
        "number": 2,
        "title": "Analyse des données de systèmes éducatifs",
        "client": "EdStats – Banque mondiale",
        "category": "Analyse & modélisation",
        "period": "",
        "folder": "Projet_2_Analysez_les_donnees_de_systemes_educatifs",
        "summary": "Identifier les pays les plus prometteurs pour développer une activité de formation en ligne, à partir des données EdStats.",
        "context": (
            "Une structure de formation en ligne veut savoir dans quels pays s'implanter. "
            "Les données EdStats de la Banque mondiale (5 fichiers CSV, séries de 1970 à 2100) sont volumineuses, "
            "hétérogènes et très incomplètes : il faut les assainir avant toute conclusion."
        ),
        "approach": [
            "**Bronze** : chargement brut des 5 CSV, contrôle des types, doublons et valeurs manquantes ; retrait des « faux pays » (agrégats régionaux, groupes de revenus).",
            "**Silver** : sélection de la période 2000-2015 et des indicateurs pertinents après analyse du taux de renseignement.",
            "**Gold** : moyenne par pays et par indicateur, pivot (1 ligne par pays), puis matrice de corrélation de Pearson pour écarter les indicateurs redondants.",
            "**Analyse** : distributions par indicateur, top 10 par indicateur, puis score global par somme des rangs.",
        ],
        "tools": ["Python", "pandas", "NumPy", "seaborn", "matplotlib", "Google Colab"],
        "results": [
            "196 pays analysés sur 6 indicateurs finaux (inscriptions dans le supérieur, RNB/habitant, internautes, croissance démographique, population en âge du lycée, durée du secondaire).",
            "Fortes disparités mises en évidence : RNB/habitant médian de 8 428 $ pour un maximum au-delà de 109 000 $.",
            "Classement global reproductible des 10 pays les plus attractifs (somme des rangs sur tous les indicateurs).",
        ],
        "limits": [
            "Exécution liée à Google Colab et Google Drive (chemins à adapter en local).",
            "Le classement par somme des rangs donne le même poids à chaque indicateur.",
        ],
        "skills": ["Python", "Nettoyage & qualité des données", "Data visualisation", "Modélisation de données", "Documentation"],
        "value": "Transformer un jeu de données brut et lacunaire en un classement lisible et justifié, avec une architecture en couches (bronze / silver / gold) qui rend chaque décision traçable.",
        "deliverables": [
            ("Notebook d'analyse", "Projet2_Analyse_des_données_SE.ipynb"),
            ("Présentation", "Livrables/Wassim-1-présentation.pptx"),
        ],
        "images": [],
    },
    {
        "number": 3,
        "title": "DataImmo – Base de données des transactions immobilières",
        "client": "Laplace Immo",
        "category": "Bases de données & stockage",
        "period": "Octobre 2025",
        "folder": "Projet_3_Entrainez_vous_avec_SQL_et_créez_votre_BDD",
        "summary": "Créer, alimenter et interroger une base relationnelle nationale des transactions immobilières sur Google BigQuery.",
        "context": (
            "Laplace Immo, réseau national d'agences, veut exploiter ses données pour suivre le prix au m², "
            "repérer les zones dynamiques et répondre aux besoins des agences régionales."
        ),
        "approach": [
            "Étude des fichiers Excel fournis et rédaction du **dictionnaire de données**.",
            "Conception d'un **schéma relationnel normalisé** de 3 tables : `valeurs_foncieres`, `donnees_commune`, `referentiel_geographique`.",
            "Nettoyage, transformation puis chargement dans **BigQuery**.",
            "Requêtes SQL métier : évolution trimestrielle, répartition par type de bien, par zone géographique, prix moyen au m², zones les plus dynamiques.",
        ],
        "tools": ["Google BigQuery", "SQL", "Excel", "Google Cloud Platform"],
        "results": [
            "Base relationnelle normalisée d'environ 35 000 transactions et 35 000 communes (1er semestre 2020).",
            "Dynamiques régionales du marché et zones à fort potentiel mises en évidence.",
            "Premiers indicateurs fiables et reproductibles pour la décision stratégique.",
        ],
        "limits": [
            "Pistes : pipeline ETL régulier, période étendue 2021-2025, tableaux de bord (Power BI, Looker Studio), modèle de valeur prévisionnelle.",
        ],
        "skills": ["SQL", "Modélisation de données", "Data warehouse (BigQuery)", "Cloud (GCP / AWS)", "Nettoyage & qualité des données", "Documentation"],
        "value": "Passer de fichiers Excel dispersés à une source de vérité unique, interrogeable en SQL, sur laquelle les agences peuvent s'appuyer.",
        "deliverables": [
            ("Dictionnaire de données", "Livrables/Wassim_1_dictionnaire.xlsx"),
            ("Support de présentation", "Livrables/Wassim_2_support.pptx"),
        ],
        "images": [],
    },
    {
        "number": 4,
        "title": "Audit des écarts de chiffre d'affaires sur un cube OLAP",
        "client": "SuperSmartMarket",
        "category": "Audit & gouvernance",
        "period": "Novembre 2025",
        "folder": "Projet_4_Auditez_un_environnement_de_données",
        "summary": "Retrouver la cause de l'instabilité du chiffre d'affaires de journées pourtant clôturées.",
        "context": (
            "Chez SuperSmartMarket, le CA d'une journée clôturée peut encore changer le lendemain, "
            "ce qui rend les indicateurs financiers peu fiables. Architecture : SQL Server (OLTP) → cube OLAP Azure Analysis Services → Power BI."
        ),
        "approach": [
            "Analyse de l'architecture et des flux, rédaction du **dictionnaire de données** et reconstitution du **schéma relationnel**.",
            "Prototype dans **BigQuery** (tables de dimensions et de faits, clés primaires et étrangères).",
            "Requêtes SQL pour recalculer les indicateurs clés (CA total, top 10 clients, CA par employé).",
            "Analyse des **logs** pour comparer date de transaction et date d'insertion.",
        ],
        "tools": ["Google BigQuery", "SQL", "SQL Server", "Azure Analysis Services", "Power BI"],
        "results": [
            "Cause identifiée : les écarts ne viennent pas des calculs mais du **processus d'intégration** (ventes du 14/08 insérées le 15/08 à cause du paramétrage du scheduler).",
            "3 constats documentés : logs non normalisés, aucune colonne au format DATE, décalage transaction / insertion.",
            "5 recommandations chiffrées en avantages et limites : logs normalisés, `date_complete`, contrôles d'intégrité, scheduler, séparation date métier / date technique.",
        ],
        "limits": [
            "Pistes : refonte progressive de l'architecture décisionnelle, monitoring et alertes automatiques.",
        ],
        "skills": ["Audit & gouvernance", "SQL", "Data warehouse (BigQuery)", "Modélisation de données", "Tests & fiabilité", "Documentation"],
        "value": "Restaurer la confiance dans les indicateurs financiers en prouvant, logs à l'appui, l'origine exacte d'un écart, puis en proposant des correctifs priorisés.",
        "deliverables": [
            ("Rapport d'audit", "Livrables/Wassim_2_rapport-audit.docx"),
            ("Présentation", "Livrables/Wassim_1_presentation.pptx"),
            ("Dictionnaire de données", "Livrables/Wassim_3_dictionnaire-de-données.xlsx"),
        ],
        "images": [],
    },
    {
        "number": 5,
        "title": "Système de stockage de données patients (HealthcareDB)",
        "client": "Données de santé",
        "category": "Bases de données & stockage",
        "period": "",
        "folder": "Projet_5_Systeme_de_stockage_des_données",
        "summary": "Migrer un jeu de données patients vers MongoDB dans Docker, avec historisation SCD2 et gestion des rôles.",
        "context": (
            "Un fichier CSV de données patients (environ 8 Mo) doit être stocké dans une base NoSQL, "
            "avec historique des modifications, contrôles d'intégrité et accès restreints par rôle."
        ),
        "approach": [
            "Déploiement de **MongoDB** et du script de migration avec **Docker Compose**.",
            "Script Python : tests d'intégrité sur les données, ingestion et gestion de l'historique en **SCD Type 2** (`UpdateOne` / `InsertOne`).",
            "Journalisation des opérations dans une collection `import_logs`.",
            "Rôles de sécurité : `admin_rw` (find, insert, update, remove) et `reader_only` (find et listCollections) ; variables d'environnement pour les secrets.",
        ],
        "tools": ["MongoDB", "Docker", "Docker Compose", "Python", "pandas", "pymongo", "MongoDB Compass"],
        "results": [
            "Base `healthcareDB` opérationnelle avec les collections `patients` et `import_logs`.",
            "Migration relançable à la demande, sans reconstruire l'image.",
            "Droits d'accès démontrés par rôle (captures ci-dessous).",
        ],
        "limits": [],
        "skills": ["NoSQL (MongoDB)", "Docker & conteneurisation", "Python", "Sécurité & secrets", "Tests & fiabilité"],
        "value": "Un stockage reproductible en une commande, qui conserve l'historique des changements et applique le moindre privilège.",
        "deliverables": [
            ("Script de migration", "script_tests.py"),
            ("Orchestration Docker", "docker-compose.yml"),
        ],
        "images": [
            ("Rôle admin_rw : privilèges d'écriture", "assets/p5_role_admin_rw.png"),
            ("Rôle reader_only : lecture seule", "assets/p5_role_reader.png"),
        ],
    },
    {
        "number": 6,
        "title": "API de prédiction de la consommation énergétique (SiteEnergyUse)",
        "client": "Prédiction énergétique de bâtiments",
        "category": "ML & IA",
        "period": "",
        "folder": "Projet_6/siteeui_api",
        "summary": "Pipeline ML complet : préparation des données, modèle XGBoost, API BentoML et conteneur Docker.",
        "context": "Prédire la consommation énergétique `SiteEnergyUse(kBtu)` d'un bâtiment et la rendre accessible via une API déployable.",
        "approach": [
            "Préparation, nettoyage et feature engineering sur Google Colab, export de `X_final_cleaned_encoded.csv` et `y_target.csv`.",
            "Réentraînement local d'un **XGBoost** (split 80/20, imputation par la médiane, `max_depth=4`, 300 arbres, `learning_rate=0.05`), évaluation par RMSE et R².",
            "Packaging du modèle et service d'inférence avec **BentoML** (`siteeui_service.py`).",
            "**Dockerisation** de l'API (port 3000) et déploiement optionnel sur AWS (ECR + App Runner).",
        ],
        "tools": ["Python", "XGBoost", "scikit-learn", "BentoML", "Docker", "AWS ECR / App Runner", "Google Colab"],
        "results": [
            "Modèle versionné (`siteeui_xgb.json`) servi par une API HTTP.",
            "Image Docker prête à être déployée : `docker run -p 3000:3000 siteeui_service:latest`.",
        ],
        "limits": ["Le déploiement AWS est optionnel et décrit mais non requis pour faire tourner l'API."],
        "skills": ["Python", "MLOps / API ML", "Docker & conteneurisation", "Cloud (GCP / AWS)", "Nettoyage & qualité des données"],
        "value": "Faire passer un modèle du notebook à un service consommable par d'autres applications, reproductible via Docker.",
        "deliverables": [
            ("Entraînement du modèle", "model_train.py"),
            ("Service d'API", "siteeui_service.py"),
            ("Dockerfile", "Dockerfile"),
        ],
        "images": [],
    },
    {
        "number": 7,
        "title": "Analyse de logements Airbnb avec MongoDB (Paris & Lyon)",
        "client": "Annonces Airbnb",
        "category": "Bases de données & stockage",
        "period": "",
        "folder": "Projet_7_Concevez_et_analysez_une_base_de_données_NoSQL",
        "summary": "Importer les annonces Airbnb de Paris et Lyon dans MongoDB et en extraire des indicateurs.",
        "context": "Concevoir une base NoSQL à partir des fichiers d'annonces (plusieurs milliers de documents par ville) et l'interroger pour produire des statistiques par ville et par quartier.",
        "approach": [
            "Import des CSV dans la collection MongoDB `listings_paris` de la base `noscites`, avec ajout d'un champ `city` pour distinguer Paris et Lyon.",
            "Scripts d'import avec contrôle des volumes par ville ; variante d'import vers une instance MongoDB distincte.",
            "Requêtes et agrégations en Python avec **Polars** (`requetes_complexes.py`).",
        ],
        "tools": ["MongoDB", "Python", "pymongo", "Polars"],
        "results": [
            "Taux de réservation moyen par mois et par type de logement.",
            "Médiane du nombre d'avis, globale et par catégorie d'hôte (superhost ou non).",
            "Densité de logements et taux de réservation par quartier de Paris.",
        ],
        "limits": ["Les chemins d'import sont des chemins locaux à adapter."],
        "skills": ["NoSQL (MongoDB)", "Python", "Modélisation de données", "Data visualisation"],
        "value": "Exploiter un volume de données semi-structurées avec un modèle documentaire, et en tirer des indicateurs décisionnels par territoire.",
        "deliverables": [
            ("Import des données", "import_lyon.py"),
            ("Requêtes d'analyse", "requetes_complexes.py"),
        ],
        "images": [],
    },
    {
        "number": 8,
        "title": "GreenAndCoop – Infrastructure de données météo",
        "client": "GreenAndCoop",
        "category": "Pipelines & orchestration",
        "period": "",
        "folder": "Projet_8_Construisez_et_testez_une_infrastructure_de_données",
        "summary": "Transformer trois sources météo hétérogènes en un schéma en étoile fiable, avec dbt et 31 tests automatisés.",
        "context": (
            "Trois sources de données météo : InfoClimat (stations SYNOP, unités SI) et deux stations Weather Underground "
            "(Ichtegem en Belgique, La Madeleine en France, unités impériales). Les Data Scientists ont besoin d'un schéma unifié et testé."
        ),
        "approach": [
            "Ingestion de JSON et XLSX vers CSV (`prepare_data.py`), puis chargement dans **PostgreSQL** (Docker) avec **Airbyte**.",
            "Modélisation **dbt** en 4 couches : Bronze, Silver (conversions impérial → métrique), Gold (union des 3 sources), Datamart (schéma en étoile).",
            "Tables finales : `dim_weather_stations` et `fact_weather_observations`.",
            "Migration vers une base **AWS RDS**.",
        ],
        "tools": ["dbt", "PostgreSQL", "Airbyte", "Docker", "Python", "AWS RDS"],
        "results": [
            "**31 tests automatisés** : not_null, unique, relationships, accepted_values, plages physiques (température, pression, humidité), cohérence du point de rosée.",
            "Schéma analytique documenté (docs dbt) et exploitable par les Data Scientists.",
            "Unités harmonisées entre sources impériales et SI.",
        ],
        "limits": [],
        "skills": ["Transformation (dbt)", "SQL", "Modélisation de données", "Tests & fiabilité", "Docker & conteneurisation", "Cloud (GCP / AWS)", "Nettoyage & qualité des données"],
        "value": "Un entrepôt de données dont chaque couche est testée : les analystes consomment des données harmonisées et de qualité vérifiée.",
        "deliverables": [
            ("Projet dbt", "greenandcoop"),
            ("Scripts d'ingestion", "ingestion"),
        ],
        "images": [],
    },
    {
        "number": 9,
        "title": "PoC InduTechData – Pipeline de tickets en temps réel",
        "client": "InduTechData",
        "category": "Cloud & infrastructure",
        "period": "2026",
        "folder": "Projet_9_Modélisez_une_infrastructure_dans_le_cloud/indutech-tickets-poc",
        "summary": "Prouver la faisabilité d'un traitement temps réel des tickets clients avec Redpanda et Spark Structured Streaming.",
        "context": "Démontrer qu'une architecture de streaming peut recevoir, enrichir et agréger des demandes clients au fil de l'eau.",
        "approach": [
            "**Producer** Python (Faker + confluent-kafka) qui émet des tickets JSON vers un topic Redpanda de 3 partitions.",
            "**Consumer** PySpark 3.5.3 : parsing JSON, enrichissement par équipe support, agrégation par fenêtre d'1 minute (watermark 30 s).",
            "Sorties : fichiers **Parquet** enrichis et agrégations console ; supervision via Redpanda Console.",
            "Stack entièrement conteneurisée avec **Docker Compose** ; healthchecks et `depends_on: service_healthy`.",
        ],
        "tools": ["Redpanda (Kafka)", "Apache Spark Structured Streaming", "PySpark", "Python", "Docker Compose", "Parquet"],
        "results": [
            "Pipeline complet démarrable en une commande (`docker compose up -d --build`).",
            "Agrégations toutes les 20 s par type de demande et priorité.",
            "Optimisations documentées : mémoire Spark, partitions de shuffle, backpressure (`maxOffsetsPerTrigger`).",
        ],
        "limits": ["PoC : volume simulé, pas de déploiement cloud managé."],
        "skills": ["Streaming (Kafka / Spark)", "Docker & conteneurisation", "Python", "Cloud (GCP / AWS)", "Tests & fiabilité", "Documentation"],
        "value": "Valider une architecture temps réel avant tout investissement, avec une documentation de dépannage tirée de problèmes réellement rencontrés.",
        "deliverables": [
            ("README du PoC", "README.md"),
            ("Producer", "producer/producer.py"),
            ("Consumer Spark", "consumer/spark_consumer.py"),
        ],
        "images": [],
    },
    {
        "number": 10,
        "title": "BottleNeck – Automatisation du reporting commercial",
        "client": "BottleNeck (marchand de vin)",
        "category": "Pipelines & orchestration",
        "period": "2026",
        "folder": "Projet_10_Construisez_et_testez_une_automatisation_de_transformation_et_analyse_de_données",
        "summary": "Remplacer un rapprochement mensuel manuel par un pipeline orchestré, testé et planifié.",
        "context": "Les ventes viennent de deux systèmes (ERP et CMS web). Le rapprochement manuel était lent, non reproductible et source d'erreurs.",
        "approach": [
            "Orchestration **Kestra** : 31 tâches, déclenchement cron le 15 de chaque mois à 9h (Europe/Paris).",
            "**DuckDB** pour lire les Excel, nettoyer, dédoublonner, joindre et agréger.",
            "Détection des vins « premium » par z-score en Python (seuil z > 2).",
            "Stratégie **fail-fast** : 6 tests bloquants, chaque échec arrête le pipeline.",
        ],
        "tools": ["Kestra", "DuckDB", "Python", "pandas", "Docker Compose", "PostgreSQL"],
        "results": [
            "825 lignes ERP, 714 lignes WEB nettoyées sur 1 428 brutes, 714 lignes après fusion.",
            "Chiffre d'affaires total : **70 568,60 €**.",
            "**30 vins premium** détectés ; livrables générés : rapport Excel, `premium.csv`, `ordinaire.csv`.",
        ],
        "limits": [
            "Kestra orchestre mais ne transforme pas à grande échelle : à coupler avec dbt pour industrialiser.",
            "Pistes : notifications email, dépôt cloud des livrables, table de rejets.",
        ],
        "skills": ["Orchestration (Kestra)", "SQL", "Python", "Tests & fiabilité", "Docker & conteneurisation", "Nettoyage & qualité des données"],
        "value": "Un reporting mensuel exact et reproductible sans supervision, où une donnée corrompue ne peut jamais se propager en aval.",
        "deliverables": [
            ("Workflow Kestra", "bottleneck_pipeline.yml"),
            ("Logigramme", "docs/logigramme.drawio"),
            ("Docker Compose", "docker-compose.yml"),
        ],
        "images": [],
    },
    {
        "number": 11,
        "title": "POC RAG – Recommandation d'événements culturels",
        "client": "Puls-Events",
        "category": "ML & IA",
        "period": "2026",
        "folder": "Projet_11_Concevez_et_deployez_un_systeme_RAG",
        "summary": "Chatbot RAG qui recommande des événements culturels à Montpellier, avec garde-fou anti-hallucination.",
        "context": "Recommander en langage naturel des événements de moins d'un an à partir de l'API ouverte OpenAgenda, en citant ses sources.",
        "approach": [
            "**Ingestion** OpenAgenda : pagination, filtre temporel, nettoyage, dédoublonnage par uid.",
            "**Indexation** : embeddings `mistral-embed`, index **FAISS** reconstructible.",
            "**RAG** (LangChain + `mistral-small-latest`) : 10 voisins, seuil de similarité avec refus si rien de pertinent, prompt strict anti-hallucination, sources citées.",
            "**Évaluation** chiffrée sur jeu annoté : Precision@k, Recall@k, taux de refus, latence.",
        ],
        "tools": ["Python", "LangChain", "Mistral AI", "FAISS", "OpenAgenda API", "unittest"],
        "results": [
            "Chaîne complète ingestion → indexation → chatbot, rafraîchissable via `update_data.py`.",
            "Réponses tracées (titre et URL de chaque événement).",
            "Tests unitaires déterministes, sans appel réseau ni LLM (mocks).",
        ],
        "limits": [
            "Un seul agenda (Montpellier) ; mise à jour manuelle ; FAISS local, à remplacer par Qdrant, Milvus ou pgvector à grande échelle.",
        ],
        "skills": ["IA générative (RAG)", "Python", "Tests & fiabilité", "Sécurité & secrets", "Documentation"],
        "value": "Un assistant fiable parce qu'il sait refuser de répondre et prouver ses réponses, avec une qualité mesurée plutôt que supposée.",
        "deliverables": [
            ("Ingestion", "src/ingestion/openagenda_ingest.py"),
            ("Système RAG", "src/rag/build_rag.py"),
            ("Évaluation", "evaluate.py"),
        ],
        "images": [],
    },
    {
        "number": 12,
        "title": "Sport Data Solution – POC d'infrastructure de données",
        "client": "Sport Data Solution",
        "category": "Cloud & infrastructure",
        "period": "2026",
        "folder": "Projet_12_Gerez_un_projet_d'infrastructure",
        "summary": "Pipeline automatisé et reproductible, des fichiers Excel RH et sportifs jusqu'à un rapport Power BI de pilotage.",
        "context": (
            "Deux dispositifs à piloter : une prime au mode actif (selon la distance domicile-travail) "
            "et 5 jours de congé « bien-être ». Les indicateurs doivent être recalculables dès qu'une règle métier change."
        ),
        "approach": [
            "Architecture **médaillon** dans PostgreSQL : raw → staging → intermediate → marts.",
            "Règles métier paramétrables dans **dbt** (taux de prime, seuils, plafonds).",
            "Distances domicile-travail via Nominatim et OpenRouteService, avec **fallback Haversine** si l'API échoue.",
            "Orchestration **Kestra** (pipeline + digest Slack quotidien), le tout dans **Docker Compose** ; restitution **Power BI** de 3 pages.",
        ],
        "tools": ["PostgreSQL", "dbt", "Kestra", "Docker Compose", "Python", "OpenRouteService", "Power BI", "Slack"],
        "results": [
            "Pipeline idempotent, relançable sans doublon ni effet de bord.",
            "4 marts exposés à Power BI : éligibilité prime, impact financier, éligibilité bien-être, anomalies.",
            "Changer une règle (ex. `taux_prime`) puis relancer recalcule tous les indicateurs.",
        ],
        "limits": [
            "Actualisation Power BI manuelle, activités simulées ; pistes : API Strava, ingestion incrémentale, gateway Power BI.",
        ],
        "skills": ["Transformation (dbt)", "Orchestration (Kestra)", "Docker & conteneurisation", "Modélisation de données", "Sécurité & secrets", "Data visualisation", "SQL", "Python"],
        "value": "Une chaîne de bout en bout où le métier peut modifier une règle et obtenir des chiffres à jour, avec une exploitation sécurisée (secrets hors dépôt, rôle à droits limités).",
        "deliverables": [
            ("Rapport Power BI", "powerbi/sport_data_solution.pbix"),
            ("Flow Kestra", "kestra/flows/sport_data_pipeline.yml"),
            ("Projet dbt", "dbt"),
        ],
        "images": [],
    },
]

# Pour chaque compétence : ce qu'elle démontre et la valeur apportée.
SKILL_DESCRIPTIONS = {
    "Python": ("Scripts d'ingestion, de migration, d'analyse et de services.", "Automatiser et fiabiliser les traitements répétitifs."),
    "SQL": ("Requêtes analytiques, jointures, agrégations, modèles dbt.", "Obtenir des indicateurs fiables directement à la source."),
    "Modélisation de données": ("Schémas relationnels normalisés, schéma en étoile, architecture médaillon.", "Des données structurées, compréhensibles et évolutives."),
    "Nettoyage & qualité des données": ("Dédoublonnage, typage, gestion des valeurs manquantes et aberrantes.", "Éviter que des données erronées faussent les décisions."),
    "Data visualisation": ("Graphiques exploratoires, rapports Power BI.", "Rendre les résultats lisibles pour les équipes métier."),
    "Cloud (GCP / AWS)": ("BigQuery, AWS RDS, ECR et App Runner.", "Exploiter des services managés, sans infrastructure à maintenir."),
    "Data warehouse (BigQuery)": ("Création de tables, clés, requêtes analytiques à grande échelle.", "Interroger rapidement de gros volumes."),
    "NoSQL (MongoDB)": ("Collections, agrégations, SCD2, rôles d'accès.", "Stocker des données semi-structurées et conserver leur historique."),
    "Docker & conteneurisation": ("Docker et Docker Compose pour bases, pipelines, API.", "Environnements reproductibles, déployables en une commande."),
    "Orchestration (Kestra)": ("Flows YAML, planification cron, retries ciblés, notifications.", "Des traitements automatiques, planifiés et supervisés."),
    "Transformation (dbt)": ("Modèles en couches, variables métier, tests, documentation.", "Une logique métier versionnée, testée et recalculable."),
    "Streaming (Kafka / Spark)": ("Redpanda, Spark Structured Streaming, fenêtres et watermark.", "Réagir aux données en temps quasi réel."),
    "MLOps / API ML": ("Entraînement XGBoost, packaging BentoML, API conteneurisée.", "Mettre un modèle en production, pas seulement en notebook."),
    "IA générative (RAG)": ("Embeddings, index vectoriel, génération contrainte, évaluation.", "Des assistants fiables, sourcés et mesurés."),
    "Tests & fiabilité": ("Tests dbt, tests fail-fast, tests unitaires avec mocks, contrôles d'intégrité.", "Détecter les erreurs avant qu'elles n'atteignent les utilisateurs."),
    "Sécurité & secrets": ("Rôles à moindre privilège, secrets hors dépôt, variables d'environnement.", "Protéger les données et les accès."),
    "Audit & gouvernance": ("Cartographie des flux, analyse de logs, recommandations priorisées.", "Restaurer la confiance dans les indicateurs."),
    "Documentation": ("Dictionnaires de données, schémas, README, rapports.", "Un travail transmissible et réutilisable par l'équipe."),
}
