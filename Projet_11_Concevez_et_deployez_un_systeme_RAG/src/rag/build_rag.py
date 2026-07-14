"""
Système RAG interactif pour la recommandation d'événements culturels (Puls-Events).

Ce script constitue l'étage temps réel de la chaîne RAG. Il charge l'index FAISS
produit par build_index.py, puis, pour chaque question de l'utilisateur :
  1. vectorise la question avec le même modèle d'embedding qu'à l'indexation ;
  2. récupère les NB_RESULTS événements les plus proches, avec leur score ;
  3. écarte les résultats jugés non pertinents (seuil de similarité) ;
  4. met en forme les événements retenus en un contexte textuel tracé ;
  5. envoie ce contexte à un LLM Mistral via un prompt strict anti-hallucination
     qui interdit d'inventer ou de déduire des informations absentes.

Si aucun événement ne franchit le seuil de pertinence, le système refuse de
répondre sans appeler le LLM (stratégie de refus explicite).

Points clés :
  - Le modèle d'embedding est importé depuis build_index.py (EMBEDDING_MODEL) afin
    de garantir la cohérence entre l'indexation et l'interrogation.
  - Le chemin de l'index est construit en absolu pour pointer vers
    src/indexing/faiss_index/ quel que soit le dossier de lancement.
  - Chaque réponse est accompagnée des sources réellement utilisées (traçabilité).
  - Aucun historique de conversation n'est conservé (chaque question est isolée).

Prérequis : la clé API Mistral doit être disponible via le fichier .env, et
l'index FAISS doit déjà avoir été construit (voir build_index.py).
"""

import os
import sys
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from langchain_community.vectorstores import FAISS

# Permet d'importer la constante EMBEDDING_MODEL depuis le module d'indexation.
# On ajoute le dossier src/indexing au path pour que l'import fonctionne quel que
# soit le répertoire depuis lequel le script est lancé.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "indexing"))
from build_index import EMBEDDING_MODEL

# --- Configuration ---
CHAT_MODEL = "mistral-small-latest"   # Modèle de génération utilisé pour formuler la réponse
NB_RESULTS = 10                     # Nombre d'événements les plus proches renvoyés par la recherche

# Seuil de distance FAISS (métrique L2 par défaut) au-delà duquel un résultat est
# jugé non pertinent et écarté. ATTENTION : avec la distance L2, un score BAS
# signifie une forte proximité (0 = identique). Cette valeur est un point de
# départ ; elle doit être CALIBRÉE empiriquement en observant les scores réels
# renvoyés pour des requêtes pertinentes et non pertinentes sur vos données.
SIMILARITY_THRESHOLD = 0.53

# Chemin absolu vers l'index créé par build_index.py (dans src/indexing/faiss_index)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(BASE_DIR, "..", "indexing", "faiss_index")


def load_index():
    """Charge l'index FAISS depuis le disque.

    Instancie le modèle d'embedding avec EMBEDDING_MODEL (identique à celui utilisé
    lors de l'indexation, condition indispensable pour que la recherche soit
    cohérente) et recharge l'index sauvegardé dans INDEX_DIR.

    Note:
        allow_dangerous_deserialization=True est requis par LangChain pour
        recharger un index FAISS local (désérialisation d'un fichier pickle).
        C'est acceptable ici car l'index est produit et maîtrisé en interne.

    Returns:
        FAISS: L'index vectoriel prêt pour la recherche de similarité.
    """
    embeddings = MistralAIEmbeddings(model=EMBEDDING_MODEL)
    return FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)


def filter_by_threshold(results_with_scores, threshold=SIMILARITY_THRESHOLD):
    """Filtre les résultats de recherche selon le seuil de pertinence.

    Chaque résultat est un couple (document, score). Avec la distance L2 de FAISS,
    un score faible indique une forte proximité ; on ne conserve donc que les
    résultats dont le score est inférieur ou égal au seuil. Ce filtrage permet au
    système de détecter l'absence de résultat réellement pertinent et de refuser
    de répondre plutôt que de forcer une réponse sur des documents hors-sujet.

    Args:
        results_with_scores (list[tuple]): Couples (document, score) renvoyés par
            similarity_search_with_score.
        threshold (float): Distance maximale acceptée. Par défaut
            SIMILARITY_THRESHOLD.

    Returns:
        list: Liste des documents retenus (sans le score), ordre préservé.
    """
    return [doc for doc, score in results_with_scores if score <= threshold]


def format_context(results):
    """Met en forme les résultats retenus en un contexte textuel tracé.

    Chaque événement est transformé en un bloc lisible reprenant son texte
    (page_content) et ses métadonnées de traçabilité : titre, identifiant (UID),
    lieu, ville, dates et URL de la source OpenAgenda. Ces informations permettent
    au LLM de citer ses sources et à l'utilisateur de les vérifier.

    Les métadonnées sont lues via .get() avec une valeur par défaut vide afin
    d'éviter toute erreur si un champ est absent.

    Args:
        results (list): Liste d'objets exposant page_content et metadata.

    Returns:
        str: Le contexte formaté, blocs séparés par une ligne vide.
    """
    blocks = []
    for r in results:
        meta = r.metadata
        block = (
            f"Titre : {meta.get('title', '')}\n"
            f"UID : {meta.get('uid', '')}\n"
            f"Description : {r.page_content}\n"
            f"Lieu : {meta.get('place', '')}, {meta.get('city', '')}\n"
            f"Date : du {meta.get('start_date', '')} au {meta.get('end_date', '')}\n"
            f"Source : {meta.get('url', '')}"
        )
        blocks.append(block)
    return "\n\n".join(blocks)


def format_sources(results):
    """Construit la liste lisible des sources réellement utilisées.

    Restitue, pour chaque événement retenu, son titre et son URL OpenAgenda afin
    d'assurer la traçabilité de la réponse côté utilisateur.

    Args:
        results (list): Liste d'objets exposant metadata.

    Returns:
        str: Liste des sources formatée, ou chaîne vide si aucune source.
    """
    lines = []
    for r in results:
        meta = r.metadata
        title = meta.get("title", "") or "(sans titre)"
        url = meta.get("url", "") or "(URL non disponible)"
        lines.append(f"- {title} : {url}")
    return "\n".join(lines)


def generate_answer(question, context, llm):
    """Génère la réponse du chatbot à partir de la question et du contexte.

    Construit un prompt strict qui cadre le comportement du modèle : répondre
    uniquement à partir des événements fournis, sans rien inventer ni déduire,
    utiliser 'non précisé' pour une information absente, signaler honnêtement
    l'absence d'événement correspondant, et citer ses sources (titre + URL).
    Ce cadrage constitue le garde-fou anti-hallucination du système.

    Args:
        question (str): La question de l'utilisateur.
        context (str): Le contexte formaté par format_context.
        llm (ChatMistralAI): L'instance du modèle de génération.

    Returns:
        str: Le texte de la réponse générée par le LLM.
    """
    prompt = (
        f"Tu es un assistant qui recommande des événements culturels à Montpellier.\n"
        f"En te basant UNIQUEMENT sur les événements suivants, réponds à la question de l'utilisateur.\n"
        f"Tu ne dois ni inventer ni déduire d'informations.\n"
        f"Si une information n'est pas précisée, réponds 'non précisé'.\n"
        f"Si aucun événement ne correspond, dis-le honnêtement.\n"
        f"Cite les sources sur lesquelles tu t'appuies (titre et URL de l'événement).\n\n"
        f"Événements disponibles :\n{context}\n\n"
        f"Question : {question}\n\n"
        f"Réponse :"
    )
    answer = llm.invoke(prompt)
    return answer.content


def answer_question(question, index, llm):
    """Traite une question de bout en bout : recherche, filtrage, génération.

    Effectue la recherche avec scores, applique le seuil de pertinence, puis :
      - si aucun événement pertinent n'est retenu, renvoie un message de refus
        sans appeler le LLM (économie d'appel et refus fiable) ;
      - sinon, génère la réponse et y ajoute la liste des sources utilisées.

    Args:
        question (str): La question de l'utilisateur.
        index (FAISS): L'index vectoriel chargé.
        llm (ChatMistralAI): L'instance du modèle de génération.

    Returns:
        str: La réponse finale (avec sources) ou le message de refus.
    """
    results_with_scores = index.similarity_search_with_score(question, k=NB_RESULTS)
    results = filter_by_threshold(results_with_scores)

    if not results:
        return ("Aucun événement suffisamment pertinent n'a été trouvé pour cette "
                "demande. Essayez de reformuler ou d'élargir votre recherche.")

    context = format_context(results)
    answer = generate_answer(question, context, llm)
    sources = format_sources(results)
    return f"{answer}\n\nSources :\n{sources}"


def main():
    """Point d'entrée : boucle interactive de questions-réponses.

    Charge les variables d'environnement, l'index FAISS et le modèle de
    génération, puis lit les questions de l'utilisateur en boucle. Pour chaque
    question, délègue le traitement à answer_question et affiche le résultat.
    La boucle s'arrête sur une entrée vide.
    """
    load_dotenv()
    index = load_index()
    llm = ChatMistralAI(model=CHAT_MODEL)

    while True:
        question = input("Pose ta question (Entrée pour quitter) : ")
        if not question:
            break

        response = answer_question(question, index, llm)
        print("\nRéponse :\n", response, "\n")


if __name__ == "__main__":
    main()
