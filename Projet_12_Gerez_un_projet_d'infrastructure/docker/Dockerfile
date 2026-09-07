# Image "runner" : Python + dépendances + dbt + code du projet, pour Kestra
FROM python:3.12-slim

# Évite les fichiers .pyc et force les logs non bufferisés
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dépendances système minimales (psycopg2, git pour dbt deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installe les dépendances Python (mêmes versions que le venv local)
COPY python/requirements.txt /app/requirements.txt

# POC : réseau d'entreprise avec inspection SSL -> pip fait confiance aux hôtes.
# À NE PAS reproduire en production.
RUN pip config set global.trusted-host "pypi.org files.pythonhosted.org github.com objects.githubusercontent.com" \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Certificats système (utile si réseau d'entreprise avec inspection SSL)
RUN pip install --no-cache-dir pip-system-certs

# Copie le code du projet dans l'image (après les deps -> meilleur cache)
COPY python/ /app/python/
COPY dbt/ /app/dbt/
COPY great_expectations/ /app/great_expectations/
COPY data/ /app/data/

# Pré-installe les packages dbt (dbt_utils, dbt_expectations) dans l'image
RUN cd /app/dbt && dbt deps || true

CMD ["bash"]
