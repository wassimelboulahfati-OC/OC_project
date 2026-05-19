FROM python:3.12-slim

WORKDIR /app

# Installer les dépendances système pour confluent-kafka
RUN apt-get update && apt-get install -y --no-install-recommends \
    librdkafka-dev gcc \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY producer.py /app/producer.py

CMD ["python", "-u", "producer.py"]
