"""
Évaluation chiffrée du retrieval du système RAG (Puls-Events).

Ce script mesure la qualité de la RECHERCHE (retrieval) du système, qui est le
déterminant principal de la pertinence d'un RAG. Il s'appuie sur un jeu de
questions annotées (data/eval_questions.json) où chaque question est associée aux
UID des événements réellement pertinents (vérité terrain établie manuellement).

Approche « semi-automatique » : on n'évalue pas la formulation exacte du LLM
(non déterministe et coûteuse en quota), mais on vérifie objectivement que le
moteur de recherche ramène les bons événements et refuse correctement les
questions hors périmètre. Cette approche est reproductible et déterministe.

Métriques produites :
  - Precision@k : proportion de documents récupérés qui sont pertinents ;
  - Recall@k    : proportion de documents pertinents qui ont été récupérés ;
  - Taux de refus correct : pour les questions hors périmètre, le système
    renvoie-t-il bien aucun résultat (grâce au seuil de similarité) ;
  - Latence moyenne de la recherche (en millisecondes).

Prérequis : index FAISS construit (build_index.py) et clé API Mistral dans .env
(l'embedding de la question nécessite un appel à l'API Mistral).

Exécution depuis la racine du projet :
    python evaluate.py
"""

import json
import os
import sys
import time

from dotenv import load_dotenv

# Importe la logique de recherche depuis le module RAG.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "rag"))
from build_rag import load_index, filter_by_threshold, NB_RESULTS

# Chemin du jeu de questions annotées.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_PATH = os.path.join(BASE_DIR, "data", "eval_questions.json")


def load_eval_set(path):
    """Charge le jeu de questions annotées depuis le fichier JSON.

    Args:
        path (str): Chemin vers le fichier d'évaluation.

    Returns:
        list[dict]: Liste de questions annotées (question, type, uids_pertinents).
    """
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def retrieved_uids(results):
    """Extrait la liste des UID des documents récupérés.

    Args:
        results (list): Documents retenus (exposant metadata).

    Returns:
        list: Liste des UID récupérés.
    """
    return [r.metadata.get("uid") for r in results]


def precision_recall(retrieved, relevant):
    """Calcule la précision et le rappel d'une recherche.

    Args:
        retrieved (list): UID effectivement récupérés (après seuil).
        relevant (list): UID pertinents attendus (vérité terrain).

    Returns:
        tuple[float, float]: (precision, recall) dans [0, 1].
    """
    retrieved_set = set(retrieved)
    relevant_set = set(relevant)

    if not retrieved_set:
        precision = 1.0 if not relevant_set else 0.0
    else:
        precision = len(retrieved_set & relevant_set) / len(retrieved_set)

    if not relevant_set:
        # Aucun document attendu (question hors périmètre) : le rappel n'a pas
        # de sens ; on le fixe à 1.0 si rien n'a été récupéré, 0.0 sinon.
        recall = 1.0 if not retrieved_set else 0.0
    else:
        recall = len(retrieved_set & relevant_set) / len(relevant_set)

    return precision, recall


def evaluate():
    """Exécute l'évaluation complète et affiche un rapport chiffré.

    Pour chaque question : effectue la recherche avec scores, applique le seuil
    de pertinence, mesure la latence, puis calcule précision et rappel par
    rapport à la vérité terrain. Agrège enfin les métriques globales, dont le
    taux de refus correct sur les questions hors périmètre.
    """
    load_dotenv()
    index = load_index()
    eval_set = load_eval_set(EVAL_PATH)

    precisions = []
    recalls = []
    latences_ms = []
    refus_attendus = 0
    refus_corrects = 0

    print("=" * 70)
    print("ÉVALUATION DU RETRIEVAL — RAG Puls-Events")
    print("=" * 70)

    for item in eval_set:
        question = item["question"]
        relevant = item.get("uids_pertinents", [])
        type_q = item.get("type", "")

        debut = time.perf_counter()
        results_with_scores = index.similarity_search_with_score(question, k=NB_RESULTS)
        results = filter_by_threshold(results_with_scores)
        latence = (time.perf_counter() - debut) * 1000
        latences_ms.append(latence)

        retrieved = retrieved_uids(results)
        precision, recall = precision_recall(retrieved, relevant)
        precisions.append(precision)
        recalls.append(recall)

        # Suivi spécifique des questions hors périmètre (refus attendu).
        if type_q == "hors_perimetre":
            refus_attendus += 1
            if not results:
                refus_corrects += 1

        statut = "REFUS" if not results else f"{len(results)} résultat(s)"
        print(f"\n[Q{item['id']}] {question}")
        print(f"   Type : {type_q} | {statut} | latence : {latence:.0f} ms")
        print(f"   Precision : {precision:.2f} | Recall : {recall:.2f}")

    n = len(eval_set)
    print("\n" + "=" * 70)
    print("RÉSULTATS GLOBAUX")
    print("=" * 70)
    print(f"Questions évaluées        : {n}")
    print(f"Precision@{NB_RESULTS} moyenne     : {sum(precisions) / n:.2f}")
    print(f"Recall@{NB_RESULTS} moyen         : {sum(recalls) / n:.2f}")
    print(f"Latence moyenne (recherche) : {sum(latences_ms) / n:.0f} ms")
    if refus_attendus:
        taux_refus = refus_corrects / refus_attendus
        print(f"Taux de refus correct     : {taux_refus:.2f} "
              f"({refus_corrects}/{refus_attendus} questions hors périmètre)")
    print("=" * 70)


if __name__ == "__main__":
    evaluate()
