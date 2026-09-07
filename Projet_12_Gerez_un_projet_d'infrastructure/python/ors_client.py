# -*- coding: utf-8 -*-
"""
ors_client.py
-------------

Pour chaque salarié à mode de déplacement "sportif" (marche/running, vélo...),
géocode son adresse (Nominatim) puis calcule la distance routière réelle
jusqu'à l'entreprise via OpenRouteService (Directions v2, api.heigit.org),
avec un profil adapté au mode de déplacement.

Robustesse :
  - User-Agent obligatoire + throttling 1 req/s pour Nominatim
  - Géocodage en 2 passes (adresse complète nettoyée, puis ville + CP)
  - Gestion des erreurs (timeout, HTTP, adresse introuvable)
  - Fallback distance à vol d'oiseau (Haversine) si l'API ORS échoue
  - Résultats écrits dans la table raw.distances_domicile_travail
"""

import os
import time
import math
import re

import requests

import pandas as pd
from sqlalchemy import create_engine, text, true
from dotenv import load_dotenv


# Vérification SSL pilotée par variable d'environnement.
# true (défaut) en local ; false dans Kestra (inspection SSL entreprise
# non gérée dans le conteneur runner).
VERIFY_SSL = os.getenv("ORS_VERIFY_SSL", "true").lower() != "false"

if not VERIFY_SSL:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ----------------------------------------------------------------------
# 0. Configuration
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_NAME = os.getenv("DATA_DB_NAME", "sport_data")
DB_USER = os.getenv("DATA_DB_USER", "sds_admin")
DB_PASSWORD = os.getenv("DATA_DB_PASSWORD")
DB_HOST = os.getenv("DATA_DB_HOST", "localhost")
DB_PORT = os.getenv("DATA_DB_PORT", "5433")
ORS_API_KEY = os.getenv("ORS_API_KEY")

ENGINE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Adresse de l'entreprise (cible commune à tous les trajets)
ADRESSE_ENTREPRISE = "1362 Avenue des Platanes, 34970 Lattes, France"

# Endpoints
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ORS_DIRECTIONS_URL = "https://api.heigit.org/openrouteservice/v2/directions/{profile}"

# User-Agent obligatoire pour Nominatim (identifie l'application)
USER_AGENT = "sport-data-solution-poc/1.0 (contact: poc@sportdata.local)"

# Correspondance mode de déplacement -> profil ORS
PROFIL_ORS = {
    "Marche/running": "foot-walking",
    "Vélo/Trottinette/Autres": "cycling-regular",
}

# Throttling Nominatim : 1 requête / seconde minimum
DELAI_NOMINATIM = 1.1

# Développe les abréviations courantes que Nominatim comprend mal
ABREVIATIONS = {
    r"\bAv\.": "Avenue",
    r"\bAv\b": "Avenue",
    r"\bBd\.": "Boulevard",
    r"\bBd\b": "Boulevard",
    r"\bChem\.": "Chemin",
    r"\bPl\.": "Place",
    r"\bRte\.": "Route",
    r"\bImp\.": "Impasse",
    r"\bAll\.": "Allée",
    r"\bRue du N\b": "Rue du Nord",  # "N" isolé -> Nord (cas observé)
}


def nettoyer_adresse(adresse: str) -> str:
    """Développe les abréviations pour améliorer le géocodage."""
    resultat = adresse
    for motif, remplacement in ABREVIATIONS.items():
        resultat = re.sub(motif, remplacement, resultat, flags=re.IGNORECASE)
    return resultat.strip()


# ----------------------------------------------------------------------
# 1. Géocodage (adresse -> lon, lat) via Nominatim
# ----------------------------------------------------------------------
def geocoder(adresse: str):
    """
    Géocode une adresse (lon, lat).
    Passe 1 : adresse complète nettoyée des abréviations.
    Passe 2 (fallback) : code postal + ville uniquement.
    Retourne (lon, lat, precision) ou (None, None, None).
    """
    headers = {"User-Agent": USER_AGENT}

    # --- Passe 1 : adresse complète nettoyée ---
    adresse_propre = nettoyer_adresse(adresse)
    params = {"q": adresse_propre, "format": "json", "limit": 1, "countrycodes": "fr"}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers,
                            timeout=15, verify=VERIFY_SSL)
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[0]["lon"]), float(data[0]["lat"]), "adresse_complete"
    except Exception as e:
        print(f"    [passe1 KO] {adresse_propre[:40]}... -> {e}")

    time.sleep(DELAI_NOMINATIM)  # throttling entre les deux passes

    # --- Passe 2 : code postal + ville (extraction par regex) ---
    match = re.search(r"(\d{5})\s+(.+)$", adresse_propre)
    if match:
        cp_ville = f"{match.group(1)} {match.group(2)}"
        params = {"q": cp_ville, "format": "json", "limit": 1, "countrycodes": "fr"}
        try:
            resp = requests.get(NOMINATIM_URL, params=params, headers=headers,
                                timeout=15, verify=VERIFY_SSL)
            resp.raise_for_status()
            data = resp.json()
            if data:
                print(f"    [fallback ville] {cp_ville}")
                return float(data[0]["lon"]), float(data[0]["lat"]), "ville_approx"
        except Exception as e:
            print(f"    [passe2 KO] {cp_ville} -> {e}")

    return None, None, None


# ----------------------------------------------------------------------
# 2. Distance routière via ORS Directions
# ----------------------------------------------------------------------
def distance_ors(lon1, lat1, lon2, lat2, profile: str):
    """Distance routière en km via ORS, ou None si échec."""
    url = ORS_DIRECTIONS_URL.format(profile=profile)
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json",
    }
    body = {"coordinates": [[lon1, lat1], [lon2, lat2]]}
    try:
        resp = requests.post(url, json=body, headers=headers,
                             timeout=20, verify=VERIFY_SSL)
        resp.raise_for_status()
        data = resp.json()
        metres = data["routes"][0]["summary"]["distance"]
        return round(metres / 1000, 2)
    except Exception as e:
        print(f"    [ORS KO] profil={profile} -> {e}")
    return None


# ----------------------------------------------------------------------
# 3. Fallback : distance à vol d'oiseau (Haversine)
# ----------------------------------------------------------------------
def distance_haversine(lon1, lat1, lon2, lat2):
    """Distance à vol d'oiseau en km (secours si ORS échoue)."""
    R = 6371  # rayon Terre en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return round(R * 2 * math.asin(math.sqrt(a)), 2)


# ----------------------------------------------------------------------
# 4. Traitement principal
# ----------------------------------------------------------------------
def main():
    if not DB_PASSWORD:
        raise RuntimeError("DATA_DB_PASSWORD introuvable. Vérifie le .env.")
    if not ORS_API_KEY:
        raise RuntimeError("ORS_API_KEY introuvable. Vérifie le .env.")

    engine = create_engine(ENGINE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(f"Connexion OK à {DB_NAME}@{DB_HOST}:{DB_PORT}\n")

    # Géocodage de l'entreprise (une seule fois)
    print("Géocodage de l'entreprise...")
    lon_ent, lat_ent, _ = geocoder(ADRESSE_ENTREPRISE)
    time.sleep(DELAI_NOMINATIM)
    if lon_ent is None:
        raise RuntimeError("Impossible de géocoder l'adresse de l'entreprise.")
    print(f"  Entreprise -> lon={lon_ent}, lat={lat_ent}\n")

    # Salariés à mode sportif uniquement
    query = """
        select id_salarie, adresse_domicile, moyen_deplacement, plafond_distance_km
        from intermediate.int_coherence_deplacement
        where mode_sportif = true
        order by id_salarie
    """
    df = pd.read_sql(query, engine)
    print(f"Salariés à traiter (mode sportif) : {len(df)}\n")

    resultats = []
    for i, row in df.iterrows():
        id_sal = int(row["id_salarie"])
        adresse = row["adresse_domicile"]
        mode = row["moyen_deplacement"]
        profile = PROFIL_ORS.get(mode, "foot-walking")

        print(f"[{i+1}/{len(df)}] Salarié {id_sal} ({mode})")

        lon_dom, lat_dom, precision_geo = geocoder(adresse)
        time.sleep(DELAI_NOMINATIM)

        distance_km = None
        methode = None

        if lon_dom is not None:
            distance_km = distance_ors(lon_dom, lat_dom, lon_ent, lat_ent, profile)
            methode = "ors_routier"
            if distance_km is None:  # fallback
                distance_km = distance_haversine(lon_dom, lat_dom, lon_ent, lat_ent)
                methode = "haversine_fallback"
        else:
            methode = "geocodage_echoue"

        resultats.append({
            "id_salarie": id_sal,
            "adresse_domicile": adresse,
            "moyen_deplacement": mode,
            "profil_ors": profile,
            "lon_domicile": lon_dom,
            "lat_domicile": lat_dom,
            "precision_geocodage": precision_geo,
            "distance_km": distance_km,
            "methode_calcul": methode,
        })

    # Écriture en base
    df_out = pd.DataFrame(resultats)
    df_out.to_sql(
        "distances_domicile_travail",
        engine,
        schema="raw",
        if_exists="replace",
        index=False,
    )
    print(f"\nTerminé. {len(df_out)} distances écrites dans raw.distances_domicile_travail.")

    # Petit récap
    nb_ok = (df_out["methode_calcul"] == "ors_routier").sum()
    nb_fallback = (df_out["methode_calcul"] == "haversine_fallback").sum()
    nb_ko = (df_out["methode_calcul"] == "geocodage_echoue").sum()
    print(f"  - ORS routier             : {nb_ok}")
    print(f"  - Fallback vol d'oiseau   : {nb_fallback}")
    print(f"  - Géocodage échoué        : {nb_ko}")

    # Répartition par précision de géocodage
    print("\n  Précision du géocodage :")
    for prec, cnt in df_out["precision_geocodage"].value_counts(dropna=False).items():
        print(f"    - {prec}: {cnt}")


if __name__ == "__main__":
    main()
