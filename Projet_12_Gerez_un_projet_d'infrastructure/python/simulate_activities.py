# -*- coding: utf-8 -*-
"""
simulate_activities.py
----------------------
Génère des activités sportives réalistes sur 12 mois glissants
pour les salariés sportifs (table raw.sport), et les charge dans raw.activites.

- Reproductible (seed fixée)
- Cohérence type d'activité / sport déclaré (on conserve 'Runing' tel quel)
- Distances/durées réalistes selon le sport
- Injection volontaire de ~2-3% d'anomalies pour Great Expectations (Phase 3)
"""

import os
import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ----------------------------------------------------------------------
# 0. Configuration & reproductibilité
# ----------------------------------------------------------------------
SEED = 42
random.seed(SEED)
fake = Faker("fr_FR")
Faker.seed(SEED)

# Charge le .env à la racine du projet (un niveau au-dessus de /python)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_NAME = os.getenv("DATA_DB_NAME", "sport_data")
DB_USER = os.getenv("DATA_DB_USER", "sds_admin")
DB_PASSWORD = os.getenv("DATA_DB_PASSWORD")
DB_HOST = os.getenv("DATA_DB_HOST", "localhost")
DB_PORT = os.getenv("DATA_DB_PORT", "5433")

ENGINE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ----------------------------------------------------------------------
# 1. Paramètres de simulation
# ----------------------------------------------------------------------
# Profils : part de salariés "très actifs" (>= 15 activités -> éligibles bien-être)
PART_TRES_ACTIFS = 0.55
ACTIVITES_TRES_ACTIF = (15, 40)      # min, max activités/an
ACTIVITES_OCCASIONNEL = (3, 14)

# Taux d'anomalies volontaires (pour Great Expectations)
TAUX_ANOMALIES = 0.025               # ~2.5%

# Fenêtre temporelle : 12 mois glissants
DATE_FIN = datetime.now().date()
DATE_DEBUT = DATE_FIN - timedelta(days=365)

# Catalogue : distance (km min/max) et durée (min min/max) par sport.
# distance_km = None -> sport sans distance (collectif, combat, raquette...)
CATALOGUE_SPORTS = {
    "Runing":          {"dist": (3, 15),   "duree": (20, 90)},   # faute conservée volontairement
    "Randonnée":       {"dist": (5, 25),   "duree": (60, 300)},
    "Natation":        {"dist": (0.5, 3),  "duree": (30, 90)},
    "Triathlon":       {"dist": (10, 40),  "duree": (60, 240)},
    "Voile":           {"dist": (5, 30),   "duree": (60, 240)},
    "Escalade":        {"dist": None,      "duree": (45, 180)},
    "Équitation":      {"dist": (2, 15),   "duree": (45, 120)},
    "Tennis":          {"dist": None,      "duree": (45, 120)},
    "Tennis de table": {"dist": None,      "duree": (30, 90)},
    "Badminton":       {"dist": None,      "duree": (30, 90)},
    "Rugby":           {"dist": None,      "duree": (60, 120)},
    "Football":        {"dist": None,      "duree": (60, 120)},
    "Basketball":      {"dist": None,      "duree": (45, 90)},
    "Boxe":            {"dist": None,      "duree": (45, 90)},
    "Judo":            {"dist": None,      "duree": (45, 120)},
}

# Valeur par défaut si un sport inconnu apparaît
DEFAUT_SPORT = {"dist": None, "duree": (30, 90)}

COMMENTAIRES = [
    "Super séance !", "Un peu fatigué aujourd'hui", "Nouveau record perso",
    "Sortie tranquille", "Séance intense", "Météo parfaite", "",
    "Avec des collègues", "Objectif atteint", "", "Récupération active", "",
]

# ----------------------------------------------------------------------
# 2. Fonctions
# ----------------------------------------------------------------------
def charger_sportifs(engine) -> pd.DataFrame:
    """Lit les salariés ayant un sport renseigné dans raw.sport."""
    query = """
        SELECT "ID salarié" AS id_salarie,
               "Pratique d'un sport" AS sport
        FROM raw.sport
        WHERE "Pratique d'un sport" IS NOT NULL
          AND trim("Pratique d'un sport") <> ''
    """
    df = pd.read_sql(query, engine)
    return df


def date_aleatoire() -> datetime:
    """Retourne une date+heure aléatoire dans la fenêtre 12 mois."""
    delta_jours = (DATE_FIN - DATE_DEBUT).days
    jour = DATE_DEBUT + timedelta(days=random.randint(0, delta_jours))
    heure = random.randint(6, 21)
    minute = random.choice([0, 15, 30, 45])
    return datetime(jour.year, jour.month, jour.day, heure, minute)


def generer_activites(df_sportifs: pd.DataFrame) -> pd.DataFrame:
    """Construit la liste des activités pour tous les sportifs."""
    lignes = []
    id_activite = 1

    for _, row in df_sportifs.iterrows():
        id_salarie = int(row["id_salarie"])
        sport = row["sport"].strip()
        params = CATALOGUE_SPORTS.get(sport, DEFAUT_SPORT)

        # Profil du salarié
        if random.random() < PART_TRES_ACTIFS:
            nb_activites = random.randint(*ACTIVITES_TRES_ACTIF)
        else:
            nb_activites = random.randint(*ACTIVITES_OCCASIONNEL)

        for _ in range(nb_activites):
            # Distance
            if params["dist"] is None:
                distance = None
            else:
                distance = round(random.uniform(*params["dist"]), 2)

            duree = random.randint(*params["duree"])
            dt = date_aleatoire()
            commentaire = random.choice(COMMENTAIRES)

            lignes.append({
                "id_activite": id_activite,
                "id_salarie": id_salarie,
                "date_activite": dt,
                "type_activite": sport,          # 'Runing' conservé tel quel
                "distance_km": distance,
                "duree_min": duree,
                "commentaire": commentaire if commentaire else None,
            })
            id_activite += 1

    df = pd.DataFrame(lignes)
    return df


def injecter_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Introduit volontairement des anomalies pour Great Expectations."""
    nb_anomalies = int(len(df) * TAUX_ANOMALIES)
    indices = random.sample(range(len(df)), nb_anomalies)

    for i in indices:
        type_anomalie = random.choice(["distance_neg", "date_futur", "id_inexistant", "duree_zero"])

        if type_anomalie == "distance_neg":
            df.at[i, "distance_km"] = round(random.uniform(-10, -1), 2)
        elif type_anomalie == "date_futur":
            df.at[i, "date_activite"] = datetime.now() + timedelta(days=random.randint(10, 90))
        elif type_anomalie == "id_inexistant":
            df.at[i, "id_salarie"] = random.randint(900000, 999999)  # ID hors référentiel RH
        elif type_anomalie == "duree_zero":
            df.at[i, "duree_min"] = 0

    print(f"  -> {nb_anomalies} anomalies injectées (pour Great Expectations).")
    return df


# ----------------------------------------------------------------------
# 3. Exécution
# ----------------------------------------------------------------------
def main():
    if not DB_PASSWORD:
        raise RuntimeError("DATA_DB_PASSWORD introuvable. Vérifie le fichier .env.")

    engine = create_engine(ENGINE_URL)

    # Test connexion
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(f"Connexion OK à {DB_NAME}@{DB_HOST}:{DB_PORT}\n")

    # 1. Sportifs
    df_sportifs = charger_sportifs(engine)
    print(f"Sportifs chargés : {len(df_sportifs)}")

    # 2. Génération
    df_activites = generer_activites(df_sportifs)
    print(f"Activités générées : {len(df_activites)}")

    # 3. Anomalies
    df_activites = injecter_anomalies(df_activites)

    # 4. Chargement dans raw.activites (remplace la table à chaque run)
    df_activites.to_sql(
        "activites",
        engine,
        schema="raw",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=500,
    )
    print(f"\nTerminé. {len(df_activites)} activités chargées dans raw.activites.")

    # Petit récap
    nb_par_profil = (
        df_activites.groupby("id_salarie").size().reset_index(name="nb")
    )
    eligibles_bien_etre = (nb_par_profil["nb"] >= 15).sum()
    print(f"Salariés avec >= 15 activités (éligibles bien-être) : {eligibles_bien_etre}")


if __name__ == "__main__":
    main()
