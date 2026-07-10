import json
import os
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
EMBEDDING_MODEL = "mistral-embed"

# Chemins absolus construits depuis l'emplacement de ce fichier (robustes)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "..", "data", "events.json")
INDEX_DIR = os.path.join(BASE_DIR, "faiss_index")



def load_documents(path):
    """Charge la liste de documents depuis un fichier JSON."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def split_texts_and_metadata(documents):
    """Sépare les documents en deux listes parallèles : textes et métadonnées."""
    texts = [doc["text"] for doc in documents]
    metadata = [doc["metadata"] for doc in documents]
    return texts, metadata


def build_index(texts, metadata):
    """Construit un index FAISS à partir des textes et métadonnées."""
    embeddings = MistralAIEmbeddings(model=EMBEDDING_MODEL)
    return FAISS.from_texts(texts, embeddings, metadatas=metadata)


if __name__ == "__main__":
    documents = load_documents(DATA_PATH)
    texts, metadata = split_texts_and_metadata(documents)
    print(f"Nombre de documents chargés : {len(texts)}")
    print(f"Exemple de texte : {texts[0]}")

    index = build_index(texts, metadata)
    os.makedirs(INDEX_DIR, exist_ok=True)
    index.save_local(INDEX_DIR)
    print("Index FAISS construit et sauvegardé.")

