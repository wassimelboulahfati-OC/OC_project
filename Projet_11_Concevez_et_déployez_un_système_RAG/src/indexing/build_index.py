import json
import os
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

def charger_documents(chemin):
    with open(chemin, "r", encoding="utf-8") as fichier:
        documents = json.load(fichier)
    return documents

def separer_textes_et_metadonnees(documents):
    textes = [doc["texte"] for doc in documents]
    metadonnees = [doc["metadata"] for doc in documents]
    return textes, metadonnees

def construire_index(textes, metadonnees):
    embeddings = MistralAIEmbeddings(model="mistral-embed")
    index = FAISS.from_texts(textes, embeddings, metadatas=metadonnees)
    return index

documents = charger_documents("../../data/evenements.json")
textes, metadonnees = separer_textes_et_metadonnees(documents)
print(f"Nombre de documents chargés : {len(textes)}")
print(f"Exemple de texte : {textes[0]}")

index = construire_index(textes, metadonnees)
index.save_local("faiss_index")
print("Index FAISS construit et sauvegardé.")