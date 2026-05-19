"""
Producer Redpanda pour InduTechData - POC Gestion de tickets clients
Génère des tickets clients aléatoires et les envoie dans le topic 'client_tickets'.
"""

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from confluent_kafka import Producer
from faker import Faker

# ============================================================
# Configuration
# ============================================================
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:19092")
TOPIC = os.getenv("KAFKA_TOPIC", "client_tickets")
INTERVAL_MIN = float(os.getenv("INTERVAL_MIN", "0.5"))   # délai mini entre 2 tickets
INTERVAL_MAX = float(os.getenv("INTERVAL_MAX", "2.0"))   # délai maxi entre 2 tickets

# ============================================================
# Référentiels métier
# ============================================================
TYPES_DEMANDE = ["facturation", "technique", "commercial", "réclamation", "information"]
PRIORITES = ["basse", "moyenne", "haute", "critique"]
PRIORITES_WEIGHTS = [0.4, 0.35, 0.20, 0.05]  # distribution réaliste

fake = Faker("fr_FR")

# ============================================================
# Génération d'un ticket
# ============================================================
def generate_ticket() -> dict:
    """Génère un ticket client aléatoire au format dictionnaire."""
    return {
        "ticket_id": str(uuid.uuid4()),
        "client_id": f"CLI-{random.randint(1000, 9999)}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "demande": fake.sentence(nb_words=random.randint(8, 20)),
        "type_demande": random.choice(TYPES_DEMANDE),
        "priorite": random.choices(PRIORITES, weights=PRIORITES_WEIGHTS, k=1)[0],
    }

# ============================================================
# Callback de livraison Kafka
# ============================================================
def delivery_report(err, msg):
    """Callback appelé pour chaque message produit (succès ou erreur)."""
    if err is not None:
        print(f"[ERREUR] Échec livraison : {err}")
    else:
        key = msg.key().decode("utf-8") if msg.key() else "no-key"
        print(
            f"[OK] Ticket envoyé | topic={msg.topic()} "
            f"partition={msg.partition()} offset={msg.offset()} key={key}"
        )

# ============================================================
# Boucle principale
# ============================================================
def main():
    print(f"=== Producer Redpanda démarré ===")
    print(f"Broker  : {KAFKA_BROKER}")
    print(f"Topic   : {TOPIC}")
    print(f"Intervalle : {INTERVAL_MIN}s à {INTERVAL_MAX}s")
    print("Appuyez sur Ctrl+C pour arrêter.\n")

    producer_config = {
        "bootstrap.servers": KAFKA_BROKER,
        "client.id": "indutech-ticket-producer",
        "acks": "all",
        "retries": 3,
    }
    producer = Producer(producer_config)

    count = 0
    try:
        while True:
            ticket = generate_ticket()
            producer.produce(
                topic=TOPIC,
                key=ticket["ticket_id"],
                value=json.dumps(ticket, ensure_ascii=False),
                callback=delivery_report,
            )
            producer.poll(0)  # déclenche les callbacks en attente
            count += 1
            time.sleep(random.uniform(INTERVAL_MIN, INTERVAL_MAX))
    except KeyboardInterrupt:
        print(f"\n=== Arrêt demandé. {count} tickets envoyés au total. ===")
    finally:
        print("Flush des messages restants...")
        producer.flush(timeout=10)
        print("Producer arrêté proprement.")


if __name__ == "__main__":
    main()
