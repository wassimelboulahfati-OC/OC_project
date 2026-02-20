# Projet – Prédiction du SiteEnergyUse

Ce projet met en place un pipeline complet de Machine Learning pour prédire le **SiteEnergyUse** d’un bâtiment.  
Il inclut la préparation des données sur Google Colab, le réentraînement du modèle en local, la création d’une API avec BentoML, ainsi que la dockerisation et le déploiement éventuel de cette API.

---

## Prérequis

Avant de lancer le projet, assurez‑vous d’avoir installé :

- Python 3.10+
- Docker Desktop
- Git (optionnel)
- AWS CLI (optionnel, uniquement si vous souhaitez déployer l’API)

---

## Structure du projet

- `siteeui_service.py` : service BentoML exposant l’API de prédiction  
- `bentofile.yaml` : configuration BentoML  
- `Dockerfile` : image Docker pour l’API  
- `requirements.txt` : dépendances Python  
- `bentoml/models/...` : modèle XGBoost packagé  


---

## Pipeline ML (Google Colab → Local)

1. Préparation, nettoyage et feature engineering sur Google Colab  
2. Entraînement d’un modèle XGBoost pour prédire **SiteEnergyUse**  
3. Export des données finales (`X_final_cleaned_encoded.csv`, `y_target.csv`)  
4. Réentraînement local du modèle  
5. Packaging du modèle avec BentoML  
6. Création du service API (`siteeui_service.py`)

---

## Dockerisation de l’API

### 1. Construire l’image Docker

```bash
docker build -t siteeui_service:latest .
```

### 2. Lancer le conteneur

```bash
docker run -p 3000:3000 siteeui_service:latest
```

L’API est accessible à l’adresse :

```
http://localhost:3000
```

---

## Déploiement de l’API (optionnel)

L’image Docker peut être poussée sur Amazon ECR, puis déployée via AWS App Runner afin d’obtenir une URL publique.

---
