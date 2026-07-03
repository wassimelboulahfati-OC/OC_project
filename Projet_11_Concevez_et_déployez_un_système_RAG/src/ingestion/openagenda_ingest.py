import dotenv
import os
import requests
import json
from datetime import datetime, timedelta


def date_il_y_a_un_an():
    date_limite = datetime.now() - timedelta(days=365)
    return date_limite.strftime("%Y-%m-%d")

def load_env_variables():
    # Load environment variables from .env file
    dotenv.load_dotenv()

    # Retrieve the OpenAgenda API key from environment variables
    openagenda_key = os.getenv("OpenAgendaKey")

    if openagenda_key is None:
        raise ValueError("OpenAgendaKey not found in environment variables.")

    return openagenda_key

def api_request(params=None):
    # Load environment variables
    openagenda_key = load_env_variables()
    agenda_uid = '76294001'
    url = f"https://api.openagenda.com/v2/agendas/{agenda_uid}/events"

    response = requests.get(url, params=params, headers={"key": f"{openagenda_key}"}, verify=False)

    return response

def fetch_all_events():
    tous_les_evenements = []
    after = None
    date_limite = date_il_y_a_un_an()
    while True:
        params = {"timings[gte]": date_limite}
        if after is not None:
            params["after"] = after
        response = api_request(params=params)
        data = response.json()
        evenements = data["events"]
        if len(evenements) == 0:
            break
        tous_les_evenements.extend(evenements)
        after = data["after"]
    return tous_les_evenements


def extract_event_details(e):
    titre = e.get("title", {}).get("fr", "")
    description = e.get("description", {}).get("fr", "")
    event_details = {
        "texte": f"{titre}. {description}",
        "metadata": {
            "uid": e.get("uid"),
            "ville": e.get("location", {}).get("city", ""),
            "lieu": e.get("location", {}).get("name", ""),
            "date_debut": e.get("firstTiming", {}).get("begin", ""),
            "date_fin": e.get("lastTiming", {}).get("end", ""),
        }
    }
    return event_details

def sauvegarder_documents(documents, chemin):
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump(documents, fichier, ensure_ascii=False, indent=2)

tous_les_evenements = fetch_all_events()
print(len(tous_les_evenements))

documents = [extract_event_details(e) for e in tous_les_evenements]
print(documents[0])

sauvegarder_documents(documents, "../../data/evenements.json")


# if response.status_code == 200:
#     data = response.json()
#     print("API request successful. Data received:")
#     print(data)
# else:
#     print(f"API request failed with status code: {response.status_code}")
#     print("Response content:")
#     print(response.content)