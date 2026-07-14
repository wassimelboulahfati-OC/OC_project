import dotenv
import os
import requests
from datetime import datetime, timedelta

# --- Configuration ---
API_BASE_URL = "https://api.openagenda.com/v2"
ENV_KEY_NAME = "OpenAgendaKey"
CITY = "Sète"
DAYS_LOOKBACK = 365


def load_key():
    dotenv.load_dotenv()
    key = os.getenv(ENV_KEY_NAME)
    if key is None:
        raise ValueError(f"{ENV_KEY_NAME} not found in environment variables.")
    return key


def date_limite():
    return (datetime.now() - timedelta(days=DAYS_LOOKBACK)).strftime("%Y-%m-%d")


def lister_tous_les_agendas(key):
    """Récupère tous les uid d'agendas correspondant à 'Sète' (paginé)."""
    uids = []
    offset = 0
    while True:
        url = f"{API_BASE_URL}/agendas"
        params = {"search": CITY, "size": 20, "offset": offset}
        print(f"  [log] Appel agendas offset={offset}...")
        response = requests.get(url, params=params, headers={"key": key})
        print(f"  [log] status={response.status_code}")
        data = response.json()

        total = data.get("total")
        agendas = data.get("agendas", [])
        print(f"  [log] total annoncé={total}, reçus dans cette page={len(agendas)}")

        if not agendas:
            print("  [log] page vide -> arrêt")
            break

        for a in agendas:
            uids.append(a.get("uid"))

        # Sécurité : on arrête quand on a atteint le total annoncé
        if total is not None and len(uids) >= total:
            print(f"  [log] total atteint ({len(uids)}/{total}) -> arrêt")
            break

        offset += 20
    return uids



def compter_evenements(key, agenda_uid):
    """Compte les événements Montpellier de moins d'un an dans un agenda."""
    url = f"{API_BASE_URL}/agendas/{agenda_uid}/events"
    params = {
        "adminLevel4[]": CITY,
        "timings[gte]": date_limite(),
        "size": 1,
    }
    try:
        response = requests.get(url, params=params, headers={"key": key})
        data = response.json()
        return data.get("total", 0) or 0
    except Exception:
        return 0


if __name__ == "__main__":
    key = load_key()

    print("Récupération de la liste des agendas...")
    uids = lister_tous_les_agendas(key)
    print(f"Agendas récupérés : {len(uids)}")

    total_global = 0
    agendas_avec_evenements = 0

    for i, uid in enumerate(uids, start=1):
        total = compter_evenements(key, uid)
        total_global += total
        if total > 0:
            agendas_avec_evenements += 1
            print(f"  [{i}/{len(uids)}] agenda {uid} : {total} événements")

    print("\n--- RÉSULTAT GLOBAL ---")
    print(f"Agendas parcourus : {len(uids)}")
    print(f"Agendas avec au moins 1 événement Montpellier < 1 an : {agendas_avec_evenements}")
    print(f"TOTAL événements Montpellier < 1 an (avec doublons possibles) : {total_global}")
