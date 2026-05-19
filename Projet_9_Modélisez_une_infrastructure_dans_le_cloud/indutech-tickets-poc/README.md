# 🎫 PoC InduTechData – Pipeline de gestion de tickets en temps réel

Pipeline de traitement de tickets client en streaming avec **Redpanda** (broker Kafka-compatible) et **Apache Spark Structured Streaming**, entièrement conteneurisé avec Docker Compose.

> **Contexte** : Projet 9 OpenClassrooms – Modélisation d'une infrastructure dans le cloud (InduTechData). Ce PoC démontre la faisabilité d'une architecture de streaming temps réel pour la gestion des demandes client.

---

## 📐 Architecture du pipeline

```mermaid
flowchart LR
    subgraph PROD["🐍 Producer (Python 3.12)"]
        P1[Faker - Génération aléatoire] --> P2[confluent-kafka Producer]
    end
    subgraph RP["📡 Redpanda Broker"]
        T[(Topic: client_tickets<br/>3 partitions)]
    end
    subgraph SPARK["⚡ Consumer PySpark 3.5.3"]
        S1[Structured Streaming] --> S2[Parsing JSON] --> S3[+ equipe_support] --> S4[Agrégation fenêtrée]
    end
    subgraph OUT["💾 Sorties"]
        O1[(Parquet enrichi)]
        O2[Console agrégations]
    end
    P2 -->|JSON / Kafka| T
    T -->|subscribe| S1
    S3 --> O1
    S4 --> O2
