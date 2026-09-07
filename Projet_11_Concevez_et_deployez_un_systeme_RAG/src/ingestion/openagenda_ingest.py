"""
Ingestion des événements OpenAgenda pour le POC RAG Puls-Events.

Ce script récupère les événements d'un agenda OpenAgenda, les filtre sur une
fenêtre temporelle (moins d'un an), nettoie et dédoublonne les données, enrichit
le texte avec les mots-clés, puis sauvegarde le résultat dans un fichier JSON.

Ce JSON (data/events.json) constitue la source unique consommée ensuite par
l'étape d'indexation (build_index.py) qui vectorise le champ "text".

Structure d'un document produit :
    {
        "text": "<titre>. <description>. Mots-clés : <mots-clés>",  # vectorisé
        "metadata": { uid, title, url, city, place, start_date, end_date }  # non vectorisé
    }

Chaque événement doit posséder au minimum un texte non vide, une ville et une
date de début pour être conservé (voir is_valid).

Prérequis : la clé API OpenAgenda doit être définie dans un fichier .env
sous la variable OpenAgendaKey.
"""

import dotenv
import os
import requests
import json
from datetime import datetime, timedelta

# --- Configuration ---
API_BASE_URL = "https://api.openagenda.com/v2"   # Racine de l'API OpenAgenda v2
AGENDA_UID = "76294001"                          # Identifiant de l'agenda de référence (Montpellier)
DAYS_LOOKBACK = 365                              # Fenêtre temporelle : événements de moins d'un an
REQUEST_TIMEOUT = 30                             # Délai maximal (secondes) d'un appel HTTP
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Chemin absolu de sortie, construit depuis l'emplacement du fichier (robuste au dossier de lancement)
OUTPUT_PATH = os.path.join(BASE_DIR, "..", "..", "data", "events.json")
ENV_KEY_NAME = "OpenAgendaKey"                    # Nom de la variable d'environnement contenant la clé API


def date_limite_recente():
    """Retourne la date limite au format YYYY-MM-DD.

    La date correspond au jour d'il y a DAYS_LOOKBACK jours. Elle sert de borne
    inférieure au filtre temporel de l'API (paramètre timings[gte]) pour ne
    récupérer que les événements récents.

    Returns:
        str: Date limite formatée "YYYY-MM-DD".
    """
    date_limit = datetime.now() - timedelta(days=DAYS_LOOKBACK)
    return date_limit.strftime("%Y-%m-%d")


def load_env_variables():
    """Charge la clé API OpenAgenda depuis le fichier .env.

    Lit le fichier .env, récupère la valeur de la variable ENV_KEY_NAME et la
    renvoie. La clé est un secret : elle n'est jamais codée en dur dans le script.

    Returns:
        str: La clé API OpenAgenda.

    Raises:
        ValueError: Si la variable d'environnement est absente.
    """
    dotenv.load_dotenv()
    openagenda_key = os.getenv(ENV_KEY_NAME)
    if openagenda_key is None:
        raise ValueError(f"{ENV_KEY_NAME} not found in environment variables.")
    return openagenda_key


def api_request(params=None):
    """Envoie une requête GET à l'endpoint événements de l'agenda.

    Construit l'URL à partir de API_BASE_URL et AGENDA_UID, puis effectue l'appel
    en passant la clé API dans l'en-tête HTTP "key". La réponse est validée :
    un délai maximal est imposé et un statut HTTP d'erreur lève une exception.

    Args:
        params (dict, optional): Paramètres de requête (ex. filtre temporel,
            curseur de pagination). Par défaut None.

    Returns:
        requests.Response: La réponse HTTP validée de l'API.

    Raises:
        requests.exceptions.RequestException: En cas d'erreur réseau, de délai
            dépassé ou de statut HTTP d'erreur (4xx/5xx).
    """
    openagenda_key = load_env_variables()
    url = f"{API_BASE_URL}/agendas/{AGENDA_UID}/events"
    response = requests.get(
        url,
        params=params,
        headers={"key": openagenda_key},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response


def fetch_all_events():
    """Récupère l'ensemble des événements récents via pagination.

    Boucle sur les pages de résultats en utilisant le curseur "after" fourni par
    l'API et applique le filtre temporel timings[gte] (événements de moins d'un
    an). La boucle s'arrête lorsqu'une page ne contient plus d'événements ou
    lorsque l'API cesse de fournir un curseur.

    L'accès aux clés de la réponse est défensif (.get) afin de ne pas planter si
    la structure JSON renvoyée est inattendue.

    Returns:
        list[dict]: La liste brute de tous les événements récupérés.

    Raises:
        requests.exceptions.RequestException: Propagée depuis api_request en cas
            d'erreur réseau ou HTTP.
    """
    all_events = []
    after = None
    date_limit = date_limite_recente()
    while True:
        params = {"timings[gte]": date_limit}
        if after is not None:
            params["after"] = after

        response = api_request(params=params)

        try:
            data = response.json()
        except ValueError:
            # Réponse non-JSON : on interrompt proprement plutôt que de planter.
            print("Réponse API non exploitable (JSON invalide). Arrêt de la pagination.")
            break

        events = data.get("events", [])
        if not events:
            break

        all_events.extend(events)

        after = data.get("after")
        if after is None:
            # Plus de curseur de pagination fourni par l'API : fin des résultats.
            break

    return all_events


def build_text(title, description, keywords):
    """Construit le texte vectorisable à partir des champs textuels.

    Ne conserve que les champs réellement renseignés, puis les assemble. Si
    aucun des trois champs (titre, description, mots-clés) n'est présent, la
    fonction renvoie une chaîne vide afin qu'un événement sans contenu textuel
    exploitable soit ensuite écarté par is_valid.

    Args:
        title (str): Titre de l'événement.
        description (str): Description de l'événement.
        keywords (str): Mots-clés concaténés (séparés par des virgules).

    Returns:
        str: Texte enrichi, ou chaîne vide si aucun contenu n'est disponible.
    """
    parts = []
    if title:
        parts.append(title)
    if description:
        parts.append(description)
    if keywords:
        parts.append(f"Mots-clés : {keywords}")
    return ". ".join(parts)


def build_event_url(e):
    """Détermine l'URL publique de l'événement pour la traçabilité.

    Tente d'abord de lire une URL canonique fournie par l'API. À défaut, une URL
    de secours est reconstruite à partir de l'UID de l'agenda et du slug de
    l'événement lorsque ces informations sont disponibles.

    NOTE : le nom exact du champ d'URL peut varier selon la version d'OpenAgenda.
    Vérifier sur une réponse réelle et ajuster si nécessaire.

    Args:
        e (dict): Un événement brut renvoyé par l'API OpenAgenda.

    Returns:
        str: URL de l'événement, ou chaîne vide si indéterminable.
    """
    url = e.get("canonicalUrl") or e.get("originAgenda", {}).get("url", "")
    if url:
        return url

    slug = e.get("slug", "")
    if slug:
        return f"https://openagenda.com/agendas/{AGENDA_UID}/events/{slug}"

    return ""


def extract_event_details(e):
    """Extrait le texte enrichi et les métadonnées d'un événement brut.

    Sépare l'information en deux parties :
      - "text" : titre + description + mots-clés, destiné à la vectorisation ;
      - "metadata" : identifiants, source, lieu et dates, conservés mais non
        vectorisés (utilisés pour la restitution et la traçabilité).

    Les accès se font via .get() avec des valeurs par défaut afin d'éviter toute
    KeyError sur un champ absent dans la réponse de l'API.

    Args:
        e (dict): Un événement brut renvoyé par l'API OpenAgenda.

    Returns:
        dict: Document structuré {"text": str, "metadata": dict}.
    """
    title = e.get("title", {}).get("fr", "")
    description = e.get("description", {}).get("fr", "")
    keywords_list = e.get("keywords", {}).get("fr", [])
    keywords = ", ".join(keywords_list)

    return {
        "text": build_text(title, description, keywords),
        "metadata": {
            "uid": e.get("uid"),
            "title": title,
            "url": build_event_url(e),
            "city": e.get("location", {}).get("city", ""),
            "place": e.get("location", {}).get("name", ""),
            "start_date": e.get("firstTiming", {}).get("begin", ""),
            "end_date": e.get("lastTiming", {}).get("end", ""),
        },
    }


def is_valid(document):
    """Vérifie qu'un document possède les champs indispensables.

    Un document est rejeté si son texte, sa ville ou sa date de début est absent
    ou vide. Grâce à build_text, un événement sans aucun contenu textuel produit
    un texte vide et est donc correctement écarté ici. L'usage de .get() garantit
    qu'un document mal formé (clé manquante) est simplement rejeté sans exception.

    Args:
        document (dict): Document produit par extract_event_details.

    Returns:
        bool: True si text, city et start_date sont tous renseignés, False sinon.
    """
    text = document.get("text", "")
    metadata = document.get("metadata", {})
    city = metadata.get("city", "")
    start_date = metadata.get("start_date", "")
    return bool(text and city and start_date)


def deduplicate_documents(documents):
    """Supprime les doublons d'événements sur la base de l'UID.

    Parcourt les documents dans l'ordre et ne conserve que la première occurrence
    de chaque UID. Les documents sans UID exploitable sont conservés tels quels
    (ils ne peuvent pas être identifiés comme doublons de façon fiable).

    Args:
        documents (list[dict]): Documents produits par extract_event_details.

    Returns:
        list[dict]: Liste dédoublonnée, ordre d'apparition préservé.
    """
    seen_uids = set()
    unique_documents = []
    for doc in documents:
        uid = doc.get("metadata", {}).get("uid")
        if uid is None:
            unique_documents.append(doc)
            continue
        if uid in seen_uids:
            continue
        seen_uids.add(uid)
        unique_documents.append(doc)
    return unique_documents


def save_documents(documents, path):
    """Sauvegarde la liste de documents au format JSON.

    Crée d'abord le dossier parent s'il n'existe pas (robustesse en première
    installation), puis écrit le fichier en UTF-8 avec indentation et sans
    échappement Unicode (ensure_ascii=False) afin de conserver les accents.

    Args:
        documents (list[dict]): Liste des documents validés à sauvegarder.
        path (str): Chemin du fichier JSON de sortie.
    """
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    all_events = fetch_all_events()
    print(f"Événements récupérés : {len(all_events)}")

    documents = [extract_event_details(e) for e in all_events]
    documents = [doc for doc in documents if is_valid(doc)]
    print(f"Événements après filtrage : {len(documents)}")

    documents = deduplicate_documents(documents)
    print(f"Événements après dédoublonnage : {len(documents)}")

    save_documents(documents, OUTPUT_PATH)
    print(f"Fichier sauvegardé : {OUTPUT_PATH}")
