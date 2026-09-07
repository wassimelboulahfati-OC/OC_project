# -*- coding: utf-8 -*-
"""
great_expectations_checks.py
----------------------------

Valide la table raw.activites (données brutes simulées) contre un ensemble
de règles métier. Détecte les anomalies volontairement injectées :
  - distances négatives
  - durées <= 0
  - dates dans le futur
  - id_salarie hors référentiel RH
  - types d'activités invalides

Approche : script Python "in-memory" GX Core 1.x
(Data Context éphémère -> Data Source Postgres -> Asset -> Suite -> Checkpoint)
"""

import os
from datetime import datetime

# Désactive la télémétrie GX AVANT l'import 
os.environ["GX_ANALYTICS_ENABLED"] = "false"

import great_expectations as gx
from great_expectations import expectations as gxe
from dotenv import load_dotenv


# ----------------------------------------------------------------------
# 0. Configuration connexion Postgres (depuis .env)
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_NAME = os.getenv("DATA_DB_NAME", "sport_data")
DB_USER = os.getenv("DATA_DB_USER", "sds_admin")
DB_PASSWORD = os.getenv("DATA_DB_PASSWORD")
DB_HOST = os.getenv("DATA_DB_HOST", "localhost")
DB_PORT = os.getenv("DATA_DB_PORT", "5433")

CONNECTION_STRING = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Liste des types d'activités valides (on inclut 'Runing' car présent dans
# les données sources - il sera corrigé par dbt en Phase 4, pas rejeté ici).
TYPES_VALIDES = [
    "Runing", "Randonnée", "Natation", "Triathlon", "Voile", "Escalade",
    "Équitation", "Tennis", "Tennis de table", "Badminton", "Rugby",
    "Football", "Basketball", "Boxe", "Judo",
]


# ----------------------------------------------------------------------
# 1. Construction du contexte GX et de la source de données
# ----------------------------------------------------------------------
def build_context_and_batch():
    """Crée un Data Context éphémère et retourne la Batch Definition + Suite."""
    context = gx.get_context()  # contexte éphémère (in-memory)

    # Source de données Postgres
    data_source = context.data_sources.add_postgres(
        name="sds_postgres",
        connection_string=CONNECTION_STRING,
    )

    # Data Asset = table raw.activites
    data_asset = data_source.add_table_asset(
        name="raw_activites",
        table_name="activites",
        schema_name="raw",
    )

    # Batch Definition = toute la table
    batch_definition = data_asset.add_batch_definition_whole_table(
        name="activites_full"
    )

    return context, batch_definition


# ----------------------------------------------------------------------
# 2. Définition de la suite d'attentes (expectations)
# ----------------------------------------------------------------------
def build_suite(context):
    """Crée et enregistre la suite d'expectations métier."""
    suite = gx.ExpectationSuite(name="suite_raw_activites")
    suite = context.suites.add(suite)

    # --- Intégrité / clés ---
    suite.add_expectation(
        gxe.ExpectColumnValuesToNotBeNull(column="id_activite")
    )
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeUnique(column="id_activite")
    )
    suite.add_expectation(
        gxe.ExpectColumnValuesToNotBeNull(column="id_salarie")
    )

    # --- id_salarie doit être dans le référentiel RH (< 900000) ---
    # (les anomalies injectées utilisent des IDs >= 900000)
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(
            column="id_salarie", min_value=1, max_value=899999
        )
    )

    # --- distance_km >= 0 (NULL toléré pour sports sans distance) ---
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(
            column="distance_km", min_value=0, max_value=100, mostly=1.0
        )
    )

    # --- duree_min strictement positive ---
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(
            column="duree_min", min_value=1, max_value=600
        )
    )

    # --- date_activite non nulle et pas dans le futur ---
    suite.add_expectation(
        gxe.ExpectColumnValuesToNotBeNull(column="date_activite")
    )
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(
            column="date_activite",
            max_value=datetime.now().isoformat(),
        )
    )

    # --- type_activite non nul et dans la liste valide ---
    suite.add_expectation(
        gxe.ExpectColumnValuesToNotBeNull(column="type_activite")
    )
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeInSet(
            column="type_activite", value_set=TYPES_VALIDES
        )
    )

    return suite


# ----------------------------------------------------------------------
# 3. Validation Definition + Checkpoint + exécution
# ----------------------------------------------------------------------
def main():
    if not DB_PASSWORD:
        raise RuntimeError("DATA_DB_PASSWORD introuvable. Vérifie le .env.")

    print(f"Great Expectations version : {gx.__version__}\n")

    context, batch_definition = build_context_and_batch()
    suite = build_suite(context)

    # Validation Definition = association Batch + Suite
    validation_definition = context.validation_definitions.add(
        gx.ValidationDefinition(
            name="valdef_raw_activites",
            data=batch_definition,
            suite=suite,
        )
    )

    # Checkpoint
    checkpoint = context.checkpoints.add(
        gx.Checkpoint(
            name="checkpoint_raw_activites",
            validation_definitions=[validation_definition],
            result_format={"result_format": "SUMMARY"},
        )
    )

    # Exécution
    results = checkpoint.run()

    # ------------------------------------------------------------------
    # 4. Rapport lisible
    # ------------------------------------------------------------------
    print("=" * 70)
    print("RAPPORT DE QUALITÉ - raw.activites")
    print("=" * 70)

    success_global = results.success
    print(f"\nStatut global : {'✅ SUCCÈS' if success_global else '❌ ÉCHEC (anomalies détectées)'}\n")

    for run_id, run_result in results.run_results.items():
        for expectation_result in run_result["results"]:
            cfg = expectation_result["expectation_config"]
            exp_type = cfg["type"]
            col = cfg["kwargs"].get("column", "-")
            ok = expectation_result["success"]
            stats = expectation_result.get("result", {})
            unexpected = stats.get("unexpected_count", 0)
            statut = "OK " if ok else "KO "
            détail = f"({unexpected} ligne(s) en anomalie)" if not ok else ""
            print(f"  [{statut}] {exp_type} sur '{col}' {détail}")

    print("\n" + "=" * 70)
    if not success_global:
        print("Des anomalies ont été détectées (attendu : distances < 0,")
        print("durées = 0, dates futures, id_salarie hors RH).")
        print("Elles seront filtrées/corrigées lors de la transformation dbt")
    print("=" * 70)


if __name__ == "__main__":
    main()
