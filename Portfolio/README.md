# 📊 Portfolio Data Engineer (Streamlit)

Application Streamlit qui présente les projets réalisés durant le parcours **Data Engineer** : récapitulatif, description détaillée (outils, résultats, livrables) et compétences démontrées avec la valeur ajoutée.

Le contenu est repris des README et du code des dossiers `Projet_2` à `Projet_12` du dépôt.

---

## Accéder au portfolio

### En local (Windows / PowerShell)

Prérequis : **Python 3.10+**.

```powershell
# 1. Se placer dans le dossier du portfolio
cd OC_project/Portfolio

# 2. Créer et activer un environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
streamlit run app.py
```

Streamlit ouvre automatiquement le navigateur. Sinon, aller sur **http://localhost:8501**.

Pour changer de port : `streamlit run app.py --server.port 8600`.

Pour arrêter l'application : `Ctrl + C` dans le terminal.

> Si `Activate.ps1` est bloqué par la politique d'exécution, lancer une fois : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### En ligne (Streamlit Community Cloud, gratuit)

Pour obtenir une URL publique à partager (CV, LinkedIn) :

1. Pousser le dépôt sur GitHub (le dossier `Portfolio/` doit y figurer).
2. Se connecter sur [share.streamlit.io](https://share.streamlit.io) avec son compte GitHub.
3. **Create app** → choisir le dépôt et la branche `main`.
4. **Main file path** : `Portfolio/app.py`.
5. **Deploy**. L'URL publique est de la forme `https://<nom-choisi>.streamlit.app`.

Aucun secret n'est nécessaire : l'application ne lit que des fichiers locaux.

---

## Contenu des pages

| Page | Contenu |
|---|---|
| **Accueil** | Présentation, chiffres clés, parcours par domaine, outils les plus utilisés |
| **Récapitulatif des projets** | Tableau des 11 projets, filtres par domaine / outil / compétence, fiches synthétiques |
| **Détail d'un projet** | Contexte, démarche, outils, résultats, limites, compétences, valeur ajoutée, liens vers les livrables |
| **Compétences & valeur ajoutée** | Matrice compétences × projets, poids de chaque compétence, ce qui a été fait et la valeur apportée |

---

## Structure

```
Portfolio/
├── app.py                  # Point d'entrée : configuration et navigation
├── utils.py                # Fonctions partagées (liens GitHub, agrégations)
├── requirements.txt
├── data/
│   ├── profile.py          # Nom, titre, présentation, liens
│   └── projects.py         # Catalogue des projets et des compétences
├── views/                  # Une page par fichier
│   ├── accueil.py
│   ├── projets.py
│   ├── detail.py
│   └── competences.py
├── assets/                 # Images affichées dans les fiches
├── tests/test_app.py       # Tests des pages (Streamlit AppTest)
└── .streamlit/config.toml  # Thème
```

---

## Personnaliser

- **Profil** : modifier `data/profile.py` (nom, titre, texte de présentation, liens GitHub / LinkedIn / email). Un lien vide n'est pas affiché.
- **Projets** : modifier `data/projects.py`. Chaque projet est un dictionnaire (titre, contexte, démarche, outils, résultats, compétences, valeur ajoutée, livrables). Ajouter un projet = ajouter un élément à la liste `PROJECTS`.
- **Compétences** : toute compétence citée dans un projet doit exister dans `SKILL_DESCRIPTIONS` (vérifié par les tests).
- **Liens GitHub** : construits à partir de `REPO_TREE_URL` dans `data/profile.py` et du nom de dossier du projet. Ils supposent que les dossiers ont le même nom sur GitHub.
- **Images** : placer le fichier dans `assets/` et le référencer dans le champ `images` du projet.

---

## Tests

```powershell
pip install pytest
python -m pytest tests -q
```

Les tests vérifient que chaque page s'affiche sans erreur, que les 11 fiches détail se chargent, que la navigation fonctionne et que les données sont cohérentes.

---

## Stack

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)
![Altair](https://img.shields.io/badge/Altair-1F77B4)
