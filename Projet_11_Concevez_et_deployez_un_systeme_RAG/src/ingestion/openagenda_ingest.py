import dotenv
import os
import requests
import json
from datetime import datetime, timedelta

# --- Configuration ---
API_BASE_URL = "https://api.openagenda.com/v2"
AGENDA_UID = "76294001"
DAYS_LOOKBACK = 365
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "..", "..", "data", "events.json")
ENV_KEY_NAME = "OpenAgendaKey"


def date_limite_recente():
    """Retourne la date (YYYY-MM-DD) d'il y a DAYS_LOOKBACK jours."""
    date_limit = datetime.now() - timedelta(days=DAYS_LOOKBACK)
    return date_limit.strftime("%Y-%m-%d")


def load_env_variables():
    """Charge la clé API OpenAgenda depuis le fichier .env."""
    dotenv.load_dotenv()
    openagenda_key = os.getenv(ENV_KEY_NAME)
    if openagenda_key is None:
        raise ValueError(f"{ENV_KEY_NAME} not found in environment variables.")
    return openagenda_key


def api_request(params=None):
    """Envoie une requête GET à l'API OpenAgenda."""
    openagenda_key = load_env_variables()
    url = f"{API_BASE_URL}/agendas/{AGENDA_UID}/events"
    response = requests.get(url, params=params, headers={"key": openagenda_key})
    return response


def fetch_all_events():
    """Récupère tous les événements récents via pagination."""
    all_events = []
    after = None
    date_limit = date_limite_recente()
    while True:
        params = {"timings[gte]": date_limit}
        if after is not None:
            params["after"] = after
        response = api_request(params=params)
        data = response.json()
        events = data["events"]
        if len(events) == 0:
            break
        all_events.extend(events)
        after = data["after"]
    return all_events


def extract_event_details(e):
    """Extrait texte enrichi et métadonnées d'un événement."""
    title = e.get("title", {}).get("fr", "")
    description = e.get("description", {}).get("fr", "")
    keywords_list = e.get("keywords", {}).get("fr", [])
    keywords = ", ".join(keywords_list)

    return {
        "text": f"{title}. {description}. Mots-clés : {keywords}",
        "metadata": {
            "uid": e.get("uid"),
            "city": e.get("location", {}).get("city", ""),
            "place": e.get("location", {}).get("name", ""),
            "start_date": e.get("firstTiming", {}).get("begin", ""),
            "end_date": e.get("lastTiming", {}).get("end", ""),
        },
    }


def is_valid(document):
    """Rejette l'événement si text, city ou start_date est absent ou vide."""
    text = document.get("text", "")
    metadata = document.get("metadata", {})
    city = metadata.get("city", "")
    start_date = metadata.get("start_date", "")
    return bool(text and city and start_date)



def save_documents(documents, path):
    """Sauvegarde la liste de documents au format JSON."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    all_events = fetch_all_events()
    print(f"Événements récupérés : {len(all_events)}")

    documents = [extract_event_details(e) for e in all_events]
    documents = [doc for doc in documents if is_valid(doc)]
    print(f"Événements après filtrage : {len(documents)}")

    save_documents(documents, OUTPUT_PATH)
