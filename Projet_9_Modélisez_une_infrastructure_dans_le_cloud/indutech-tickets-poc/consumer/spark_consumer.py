"""
Consumer PySpark pour InduTechData - POC Gestion de tickets clients
Lit les tickets depuis Redpanda, les enrichit, les agrège
et écrit les résultats en Parquet.
"""

import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, when, window, count, current_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType
)

# ============================================================
# Configuration via variables d'environnement
# ============================================================
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "client_tickets")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "/app/output")

# ============================================================
# Schéma des tickets (doit matcher le JSON du producer)
# ============================================================
ticket_schema = StructType([
    StructField("ticket_id",    StringType(),    True),
    StructField("client_id",    StringType(),    True),
    StructField("created_at",   StringType(),    True),
    StructField("demande",      StringType(),    True),
    StructField("type_demande", StringType(),    True),
    StructField("priorite",     StringType(),    True),
])

# ============================================================
# Mapping type_demande -> équipe de support
# ============================================================
def assigner_equipe(df):
    """Ajoute la colonne 'equipe_support' selon le type de demande."""
    return df.withColumn(
        "equipe_support",
        when(col("type_demande") == "facturation",  "Team Finance")
        .when(col("type_demande") == "technique",   "Team Tech")
        .when(col("type_demande") == "commercial",  "Team Sales")
        .when(col("type_demande") == "réclamation", "Team Customer Care")
        .when(col("type_demande") == "information", "Team Support N1")
        .otherwise("Team Triage")
    )

# ============================================================
# Main
# ============================================================
def main():
    print("=== Consumer PySpark démarré ===")
    print(f"Broker      : {KAFKA_BROKER}")
    print(f"Topic       : {TOPIC}")
    print(f"Output path : {OUTPUT_PATH}")

    spark = (
        SparkSession.builder
        .appName("IndutechTicketsConsumer")
        .config("spark.sql.shuffle.partitions", "3")
        .config("spark.sql.streaming.checkpointLocation", f"{OUTPUT_PATH}/_checkpoints")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # ----- Source : Redpanda (Kafka API) -----
    raw_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BROKER)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    # ----- Parsing JSON -----
    parsed_df = (
        raw_df
        .selectExpr("CAST(value AS STRING) as json_str", "timestamp as kafka_ts")
        .select(
            from_json(col("json_str"), ticket_schema).alias("ticket"),
            col("kafka_ts"),
        )
        .select("ticket.*", "kafka_ts")
        .withColumn("ingested_at", current_timestamp())
    )

    # ----- Transformation : enrichissement avec équipe support -----
    enriched_df = assigner_equipe(parsed_df)

    # ----- Sink 1 : tickets enrichis en Parquet -----
    query_tickets = (
        enriched_df.writeStream
        .format("parquet")
        .outputMode("append")
        .option("path", f"{OUTPUT_PATH}/tickets_enriched")
        .option("checkpointLocation", f"{OUTPUT_PATH}/_checkpoints/tickets_enriched")
        .trigger(processingTime="10 seconds")
        .start()
    )

    # ----- Sink 2 : agrégation par type + priorité (console pour debug) -----
    agg_df = (
        enriched_df
        .groupBy(
            window(col("ingested_at"), "1 minute"),
            col("type_demande"),
            col("priorite"),
        )
        .agg(count("*").alias("nb_tickets"))
    )

    query_agg = (
        agg_df.writeStream
        .format("console")
        .outputMode("complete")
        .option("truncate", "false")
        .trigger(processingTime="20 seconds")
        .start()
    )

    print("✅ Streams démarrés. En attente de tickets...")
    print(f"   Tickets enrichis -> {OUTPUT_PATH}/tickets_enriched")
    print(f"   Agrégations      -> console toutes les 20 secondes")

    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
