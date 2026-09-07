# POC RAG – Recommandation d'événements culturels (Puls-Events)

## Présentation

Ce projet est une **preuve de concept (POC)** d'un système de **RAG (Retrieval-Augmented Generation)** développé pour **Puls-Events**. Il s'agit d'un chatbot capable de recommander des événements culturels à **Montpellier** en langage naturel, à partir des données ouvertes de l'**API OpenAgenda**.

Le système récupère les événements récents (**moins d'un an**), les nettoie, les dédoublonne et les enrichit, les vectorise dans un **index FAISS** à l'aide des **embeddings Mistral**, puis répond aux questions de l'utilisateur en s'appuyant **uniquement** sur les événements retrouvés — avec un garde-fou anti-hallucination et un **seuil de pertinence** qui permet de refuser de répondre lorsqu'aucun événement pertinent n'est trouvé. Chaque réponse cite ses sources (titre et URL de l'événement).

La chaîne technique repose sur la stack imposée : **OpenAgenda** (données), **Mistral** (embeddings + génération), **FAISS** (recherche vectorielle) et **LangChain** (orchestration).

## Objectifs

- Récupérer les événements culturels de Montpellier de moins d'un an via l'API OpenAgenda.
- Nettoyer, valider, dédoublonner et structurer les données (séparation texte à vectoriser / métadonnées).
- Construire un index vectoriel FAISS reconstructible à la demande.
- Fournir un chatbot en ligne de commande qui répond aux questions à partir des événements retrouvés.
- Garantir la fiabilité des réponses (contrôle des hallucinations, seuil de pertinence, traçabilité des sources).
- Évaluer la qualité du retrieval sur un jeu de questions annotées (métriques chiffrées).
- Assurer la qualité du code par des tests unitaires reproductibles.

## Prérequis

- **Python 3.10+**
- Une **clé API OpenAgenda**
- Une **clé API Mistral**
- Un fichier `.env` à la racine du projet (voir section Configuration)

## Structure du projet

```
Projet_11_Concevez_et_deployez_un_systeme_RAG/
│
├── data/
│   ├── events.json               # Données d'événements nettoyées (généré par l'ingestion)
│   └── eval_questions.json       # Jeu de questions annotées pour l'évaluation
│
├── src/
│   ├── ingestion/
│   │   └── openagenda_ingest.py  # Récupération, filtrage, dédoublonnage et sauvegarde des événements
│   │
│   ├── indexing/
│   │   ├── build_index.py        # Construction et sauvegarde de l'index vectoriel FAISS
│   │   └── faiss_index/          # Index FAISS généré (index.faiss + index.pkl)
│   │
│   └── rag/
│       └── build_rag.py          # Système RAG interactif (recherche + seuil + génération)
│
├── tests/
│   ├── test_ingestion.py         # Tests unitaires de l'ingestion
│   └── test_rag.py               # Tests unitaires du RAG
│
├── evaluate.py                   # Évaluation chiffrée du retrieval (Precision/Recall@k, refus, latence)
├── update_data.py                # Orchestration : ingestion puis indexation
├── requirements.txt              # Dépendances Python du projet
├── .env                          # Clés API (NON versionné)
├── .env.example                  # Modèle de fichier .env (sans les valeurs)
├── .gitignore
└── README.md
```

## Description des fichiers principaux

| Fichier | Rôle |
|---|---|
| `src/ingestion/openagenda_ingest.py` | Interroge l'API OpenAgenda (pagination + filtre temporel < 1 an) de façon robuste (timeout, gestion des erreurs HTTP), extrait le texte enrichi (titre + description + mots-clés) et les métadonnées (uid, titre, url, ville, lieu, dates), écarte les événements incomplets (y compris les textes vides de sens), supprime les doublons par uid, puis sauvegarde le tout dans `data/events.json`. |
| `src/indexing/build_index.py` | Charge `data/events.json`, sépare textes et métadonnées, vectorise les textes avec le modèle `mistral-embed`, construit un index FAISS et l'enregistre dans `src/indexing/faiss_index/`. |
| `src/rag/build_rag.py` | Charge l'index FAISS, vectorise la question, récupère les 10 événements les plus proches avec leur score, écarte ceux qui dépassent un **seuil de similarité** (refus si aucun résultat pertinent), met en forme le contexte tracé (titre, uid, url) et génère une réponse via `mistral-small-latest` avec un prompt strict anti-hallucination. Boucle interactive en ligne de commande, avec citation des sources. |
| `evaluate.py` | Évalue la qualité du retrieval sur `data/eval_questions.json` (vérité terrain annotée) : Precision@k, Recall@k, taux de refus correct sur les questions hors périmètre, latence moyenne de recherche. |
| `update_data.py` | Script d'orchestration : lance l'ingestion puis l'indexation dans le bon ordre pour rafraîchir les données et reconstruire l'index. |
| `tests/test_ingestion.py` | Tests unitaires de l'ingestion : validation, extraction, dédoublonnage, conformité du périmètre (ville, dates), pagination et erreurs HTTP via mocks. |
| `tests/test_rag.py` | Tests unitaires du RAG : mise en forme du contexte et des sources, filtrage par seuil et cas de refus. |

## Installation

1. **Cloner le dépôt et se placer à la racine du projet :**

```bash
git clone <url_du_depot>
cd Projet_11_Concevez_et_deployez_un_systeme_RAG
```

2. **Créer et activer un environnement virtuel :**

Windows (PowerShell) :
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS / Linux :
```bash
python -m venv venv
source venv/bin/activate
```

3. **Installer les dépendances :**

```bash
pip install -r requirements.txt
```

Principales dépendances : `langchain`, `langchain-mistralai`, `langchain-community`, `faiss-cpu`, `requests`, `python-dotenv`.

## Configuration

Créer un fichier `.env` à la racine du projet contenant vos clés API (un modèle est fourni dans `.env.example`) :

```env
OpenAgendaKey=votre_cle_openagenda
MISTRAL_API_KEY=votre_cle_mistral
```

> ⚠️ Le fichier `.env` contient des secrets : il ne doit **jamais** être versionné (il est exclu via `.gitignore`).

## Utilisation (reproduction)

L'exécution suit trois étapes, dans cet ordre.

### 1. Ingestion des données

Récupère les événements OpenAgenda et génère `data/events.json` :

```bash
py src\ingestion\openagenda_ingest.py
```

Sortie attendue (le nombre d'événements dépend de l'agenda) :
```
Événements récupérés : ...
Événements après filtrage : ...
Événements après dédoublonnage : ...
Fichier sauvegardé : ...\data\events.json
```

### 2. Construction de l'index vectoriel

Vectorise les événements et crée l'index FAISS dans `src/indexing/faiss_index/` :

```bash
py src\indexing\build_index.py
```

Sortie attendue :
```
Nombre de documents chargés : ...
Exemple de texte : ...
Index FAISS construit et sauvegardé.
```

### 3. Lancement du chatbot RAG

Démarre la boucle interactive de questions-réponses :

```bash
py src\rag\build_rag.py
```

Exemples de questions :
- `Je cherche un événement en plein air pour toute la famille`
- `Donne-moi 3 ateliers pour enfants`
- `Parle-moi du carnaval de Celleneuve`

Appuyer sur **Entrée** (question vide) pour quitter.

### Mise à jour groupée (ingestion + indexation)

Pour rafraîchir les données et reconstruire l'index en une seule commande :

```bash
py update_data.py
```

> Tous les scripts utilisent des chemins absolus construits depuis leur emplacement : ils peuvent être lancés depuis la racine du projet comme depuis leur propre dossier.

## Évaluation

Un jeu de questions annotées (`data/eval_questions.json`) associe à chaque question les identifiants (UID) des événements réellement pertinents (vérité terrain). Le script `evaluate.py` mesure la qualité du retrieval de façon reproductible, sans juger la formulation non déterministe du LLM.

Exécution depuis la racine du projet (l'index FAISS doit avoir été construit et la clé Mistral configurée) :

```bash
py evaluate.py
```

Métriques produites : **Precision@k**, **Recall@k**, **taux de refus correct** sur les questions hors périmètre, et **latence moyenne de recherche**. Le seuil de similarité utilisé pour le refus est calibré empiriquement (constante `SIMILARITY_THRESHOLD` dans `build_rag.py`).

## Tests

La suite de tests unitaires vérifie la logique métier : validation (dont le rejet des textes vides), extraction, dédoublonnage, conformité du périmètre (ville, dates), pagination et erreurs HTTP (via mocks) côté ingestion ; mise en forme du contexte et des sources, filtrage par seuil et cas de refus côté RAG. Les tests sont rapides, déterministes et n'effectuent aucun appel réseau réel ni au LLM.

Exécution depuis la racine du projet :

```bash
py -m unittest discover -s tests -v
```

Résultat attendu : tous les tests passent (`OK`).

> Les appels réels au LLM Mistral ne sont volontairement pas testés (non déterministes, coûteux en quota). L'API OpenAgenda est en revanche couverte par mocking.

## Choix techniques

- **OpenAgenda** : base d'événements culturels français riche, avec filtres par date et localisation et pagination.
- **Mistral** (`mistral-embed` + `mistral-small-latest`) : embeddings et génération de bonne qualité en français, offre gratuite adaptée à un POC.
- **FAISS (CPU)** : recherche de similarité vectorielle rapide et locale, sans dépendance à un service externe.
- **LangChain** : orchestration des composants (embeddings, index, LLM) et interchangeabilité des briques.

## Limites et perspectives

- **Couverture géographique** : le POC s'appuie sur un agenda de référence mono-ville (Montpellier). Une agrégation multi-agendas avec dédoublonnage constitue une évolution future.
- **Mise à jour** : le rafraîchissement est manuel (`update_data.py`). Il pourrait être automatisé via un planificateur (cron / Task Scheduler) et une synchronisation incrémentale en production.
- **Passage à l'échelle** : FAISS local (mono-machine, en mémoire, recherche exacte) et un seuil de pertinence calibré à la main ne tiennent pas à grande échelle. Pour un corpus volumineux, envisager une migration vers une base vectorielle dédiée (Qdrant, Milvus, pgvector) offrant persistance, scalabilité et filtrage.
- **Évaluation & supervision** : une première base d'évaluation existe (jeu annoté + métriques). À étendre : échantillon plus large, monitoring continu (latence, taux d'hallucination, pertinence, coût, dérive).
- **Tests** : extension de la couverture, notamment via des tests d'intégration sur les appels au LLM.
