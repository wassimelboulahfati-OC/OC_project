"""
build_index.py — Construction de l'index vectoriel FAISS.

Ce module constitue l'étape d'indexation (batch) du pipeline RAG.
Il charge les événements nettoyés produits par l'ingestion, transforme
chaque texte en vecteur via le modèle d'embedding Mistral, puis construit
et sauvegarde un index FAISS sur disque.

L'index sauvegardé (index.faiss + index.pkl) est ensuite rechargé par le
module d'interrogation (build_rag.py) sans nécessiter de re-vectorisation,
ce qui économise du temps et du quota API.

Règle de cohérence : le modèle d'embedding défini ici (EMBEDDING_MODEL)
doit être identique à celui utilisé lors de la requête, sinon les vecteurs
seraient incomparables.

Exécution :
    python build_index.py
"""

import json
import os
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# Charge les variables d'environnement (.env), notamment la clé API Mistral
load_dotenv()

# --- Configuration ---

# Modèle d'embedding Mistral. Doit être identique à celui utilisé côté requête
# (build_rag.py importe cette constante pour garantir la cohérence).
EMBEDDING_MODEL = "mistral-embed"

# Chemins absolus construits depuis l'emplacement de ce fichier, afin que le
# script fonctionne quel que soit le répertoire depuis lequel il est lancé.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "..", "data", "events.json")
INDEX_DIR = os.path.join(BASE_DIR, "faiss_index")


def load_documents(path):
    """Charge la liste de documents depuis un fichier JSON.

    Args:
        path (str): Chemin vers le fichier JSON des événements.

    Returns:
        list[dict]: Liste de documents, chacun contenant les clés
            "text" (texte vectorisable) et "metadata" (données exactes).
    """
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def split_texts_and_metadata(documents):
    """Sépare les documents en deux listes parallèles : textes et métadonnées.

    Les deux listes sont alignées par position : le texte à l'indice i
    correspond aux métadonnées à l'indice i. Cet alignement est indispensable
    pour que FAISS associe correctement chaque vecteur à ses métadonnées.

    Args:
        documents (list[dict]): Liste de documents à séparer.

    Returns:
        tuple[list[str], list[dict]]: Un tuple (textes, métadonnées).
    """
    texts = [doc["text"] for doc in documents]
    metadata = [doc["metadata"] for doc in documents]
    return texts, metadata


def build_index(texts, metadata):
    """Construit un index FAISS à partir des textes et de leurs métadonnées.

    Chaque texte est vectorisé via le modèle d'embedding Mistral, puis
    indexé dans FAISS en conservant les métadonnées associées.

    Args:
        texts (list[str]): Textes à vectoriser (un par événement).
        metadata (list[dict]): Métadonnées associées, alignées avec texts.

    Returns:
        FAISS: L'index vectoriel construit, prêt à être sauvegardé ou requêté.
    """
    embeddings = MistralAIEmbeddings(model=EMBEDDING_MODEL)
    return FAISS.from_texts(texts, embeddings, metadatas=metadata)


if __name__ == "__main__":
    # 1. Charger les événements nettoyés produits par l'ingestion
    documents = load_documents(DATA_PATH)

    # 2. Séparer le contenu vectorisable des métadonnées exactes
    texts, metadata = split_texts_and_metadata(documents)
    print(f"Nombre de documents chargés : {len(texts)}")
    print(f"Exemple de texte : {texts[0]}")

    # 3. Construire l'index vectoriel FAISS
    index = build_index(texts, metadata)

    # 4. Sauvegarder l'index sur disque (crée le dossier si besoin)
    os.makedirs(INDEX_DIR, exist_ok=True)
    index.save_local(INDEX_DIR)
    print("Index FAISS construit et sauvegardé.")
