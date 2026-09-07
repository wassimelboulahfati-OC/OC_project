"""
load_sources.py
----------------
Charge les fichiers Excel sources (RH et sportif) dans le schéma `raw`
de la base de données projet, SANS transformation (principe medallion :
la couche raw reçoit la donnée brute, intacte).

Le nettoyage/normalisation sera fait plus tard par dbt (couche staging).
"""

import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ------------------------------------------------------------------
# 1. Chargement des variables d'environnement depuis le .env
# ------------------------------------------------------------------
# On remonte à la racine du projet (le dossier parent de /python)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DB_NAME = os.getenv("DATA_DB_NAME")
DATA_DB_USER = os.getenv("DATA_DB_USER")
DATA_DB_PASSWORD = os.getenv("DATA_DB_PASSWORD")
# Depuis la machine hôte, la base projet est exposée sur le port 5433
DATA_DB_HOST = os.getenv("DATA_DB_HOST", "localhost")
DATA_DB_PORT = os.getenv("DATA_DB_PORT", "5433")

# ------------------------------------------------------------------
# 2. Définition des fichiers à charger
#    (nom du fichier  ->  nom de la table cible dans le schéma raw)
# ------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"

SOURCES = {
    "Données_RH_2026.xlsx": "rh",
    "Données_Sportive_2026.xlsx": "sport",
}

TARGET_SCHEMA = "raw"


def build_engine():
    """Crée le moteur SQLAlchemy vers la base projet."""
    url = (
        f"postgresql+psycopg2://{DATA_DB_USER}:{DATA_DB_PASSWORD}"
        f"@{DATA_DB_HOST}:{DATA_DB_PORT}/{DATA_DB_NAME}"
    )
    return create_engine(url)


def load_file(engine, file_name: str, table_name: str):
    """Lit un fichier Excel et le charge dans raw.<table_name>."""
    file_path = DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    print(f"Lecture de {file_name} ...")
    df = pd.read_excel(file_path)  # openpyxl est utilisé automatiquement

    print(f"  -> {len(df)} lignes, {len(df.columns)} colonnes lues.")

    # Chargement dans Postgres (remplace la table si elle existe déjà)
    df.to_sql(
        name=table_name,
        con=engine,
        schema=TARGET_SCHEMA,
        if_exists="replace",   # POC : on recharge à neuf à chaque exécution
        index=False,
    )
    print(f"  -> Chargé dans {TARGET_SCHEMA}.{table_name}")
    return len(df)


def main():
    # Vérification minimale de la config
    missing = [k for k, v in {
        "DATA_DB_NAME": DATA_DB_NAME,
        "DATA_DB_USER": DATA_DB_USER,
        "DATA_DB_PASSWORD": DATA_DB_PASSWORD,
    }.items() if not v]
    if missing:
        print(f"ERREUR : variables .env manquantes : {', '.join(missing)}")
        sys.exit(1)

    engine = build_engine()

    # Test de connexion avant de commencer
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"Connexion OK à {DATA_DB_NAME}@{DATA_DB_HOST}:{DATA_DB_PORT}\n")
    except Exception as e:
        print(f"ERREUR de connexion à la base : {e}")
        sys.exit(1)

    # Chargement de chaque source
    total = 0
    for file_name, table_name in SOURCES.items():
        total += load_file(engine, file_name, table_name)

    print(f"\nTerminé. {total} lignes chargées au total dans le schéma '{TARGET_SCHEMA}'.")


if __name__ == "__main__":
    main()
