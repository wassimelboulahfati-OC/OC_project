# Utilise l'image officielle Python 3.12 en version slim (plus légère, adaptée pour la production)
FROM python:3.12-slim

# Définit le répertoire de travail à l'intérieur du conteneur
WORKDIR /app

# Copie le fichier requirements.txt dans le répertoire de travail
COPY requirements.txt .

# Copie le script principal de tests dans le répertoire de travail
COPY script_tests.py .

# Installe les dépendances Python listées dans requirements.txt sans conserver le cache (réduit la taille de l'image)
RUN pip install --no-cache-dir -r requirements.txt

# Définit la commande par défaut : exécute le script script_tests.py avec Python
CMD ["python", "script_tests.py"]

