import os
import sys
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from langchain_community.vectorstores import FAISS

# Permet d'importer la constante EMBEDDING_MODEL depuis le module d'indexation
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "indexing"))
from build_index import EMBEDDING_MODEL

# --- Configuration ---
CHAT_MODEL = "mistral-small-latest"
NB_RESULTS = 10

# Chemin absolu vers l'index créé par build_index.py (dans src/indexing/faiss_index)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(BASE_DIR, "..", "indexing", "faiss_index")


def load_index():
    """Charge l'index FAISS avec le même modèle d'embedding qu'à l'indexation."""
    embeddings = MistralAIEmbeddings(model=EMBEDDING_MODEL)
    return FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)


def format_context(results):
    """Met en forme les résultats de la recherche pour le LLM."""
    blocks = []
    for r in results:
        meta = r.metadata
        block = (
            f"Événement : {r.page_content}\n"
            f"Lieu : {meta.get('place', '')}, {meta.get('city', '')}\n"
            f"Date : du {meta.get('start_date', '')} au {meta.get('end_date', '')}"
        )
        blocks.append(block)
    return "\n\n".join(blocks)


def generate_answer(question, context, llm):
    """Génère une réponse à partir de la question et du contexte."""
    prompt = (
        f"Tu es un assistant qui recommande des événements culturels à Montpellier.\n"
        f"En te basant UNIQUEMENT sur les événements suivants, réponds à la question de l'utilisateur.\n"
        f"Tu ne dois ni inventer ni déduire d'informations.\n"
        f"Si une information n'est pas précisée, réponds 'non précisé'.\n"
        f"Si aucun événement ne correspond, dis-le honnêtement.\n\n"
        f"Événements disponibles :\n{context}\n\n"
        f"Question : {question}\n\n"
        f"Réponse :"
    )
    answer = llm.invoke(prompt)
    return answer.content


def main():
    load_dotenv()
    index = load_index()
    llm = ChatMistralAI(model=CHAT_MODEL)

    while True:
        question = input("Pose ta question (Entrée pour quitter) : ")
        if not question:
            break

        results = index.similarity_search(question, k=NB_RESULTS)
        context = format_context(results)
        answer = generate_answer(question, context, llm)
        print("\nRéponse :\n", answer, "\n")


if __name__ == "__main__":
    main()
