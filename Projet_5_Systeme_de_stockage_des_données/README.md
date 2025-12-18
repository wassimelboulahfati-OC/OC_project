# Projet 5 – Système de stockage des données (HealthcareDB)

Ce projet met en place un système de stockage de données avec **MongoDB** dans Docker, et un script Python pour migrer et gérer les données patients (SCD2).  
Il inclut la configuration Docker, la migration des données, la visualisation via MongoDB Compass, et des bonnes pratiques de sécurité.

--- 

##  Prérequis Avant de lancer le projet, assurez‑vous d’avoir installé et configuré : 

- **Docker Desktop** (Windows/Mac/Linux) → [Télécharger Docker](https://www.docker.com/products/docker-desktop) 
- **Docker Compose** (inclus dans Docker Desktop) 
- **MongoDB Compass** → [Télécharger Compass](https://www.mongodb.com/products/compass) 
- **Git** (optionnel, pour cloner le projet) 
- **Python 3.12** (optionnel, uniquement si vous voulez tester le script en dehors de Docker) 

---

##  Structure du projet

- `docker-compose.yml` : orchestration des services MongoDB et migration.
- `Dockerfile` : image pour exécuter le script Python.
- `requirements.txt` : dépendances Python.
- `script_tests.py` : script de migration et gestion des données.
- `healthcare_dataset.csv` : fichier source des données patients.

---

## Lancer le projet

1- Construire et démarrer les conteneurs :

```bash
docker-compose up -d --build
```
2- Vérifier que MongoDB est bien lancé :

```bash
docker ps
```
## Exécution du script de migration

Exécution automatique au démarrage :

    Le conteneur migration lance python script_tests.py dès que mongo est prêt (via depends_on et le CMD du Dockerfile).

1- Voir les logs du script :

```bash
docker logs -f migration_script
```
1- Relancer manuellement le script sans recréer l’image :

```bash
docker-compose run --rm migration
```
Cette commande exécute script_tests.py dans un conteneur éphémère basé sur l’image déjà construite.
Idéal si vous voulez rejouer la migration sans reconstruire ni redéployer MongoDB.

Relancer le conteneur existant et rejouer le script :

```bash
docker restart migration_script
```
Comme CMD est défini, le script est relancé à chaque redémarrage.

## Visualisation dans MongoDB Compass

1- Connexion Compass :

mongodb://localhost:27018/healthcareDB

2- Rafraîchir les bases : healthcareDB apparaît avec :

patients : données migrées.

import_logs : logs des opérations de migration.