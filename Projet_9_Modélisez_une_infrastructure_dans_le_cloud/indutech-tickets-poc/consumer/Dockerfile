FROM apache/spark:3.5.3-python3

USER root
WORKDIR /app

# Créer les répertoires Ivy avec bonnes permissions
RUN mkdir -p /home/spark/.ivy2/cache /home/spark/.ivy2/jars /app/output && \
    chown -R spark:spark /home/spark /app && \
    chmod -R 777 /home/spark/.ivy2 /app/output

# Pré-télécharger le connecteur Kafka pour Spark 3.5.3 (Scala 2.12)
RUN cd /opt/spark/jars && \
    curl -sLO https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.3/spark-sql-kafka-0-10_2.12-3.5.3.jar && \
    curl -sLO https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.3/spark-token-provider-kafka-0-10_2.12-3.5.3.jar && \
    curl -sLO https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar && \
    curl -sLO https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar && \
    curl -sLO https://repo1.maven.org/maven2/org/lz4/lz4-java/1.8.0/lz4-java-1.8.0.jar && \
    curl -sLO https://repo1.maven.org/maven2/org/xerial/snappy/snappy-java/1.1.10.5/snappy-java-1.1.10.5.jar

COPY spark_consumer.py /app/spark_consumer.py

USER spark

CMD ["/opt/spark/bin/spark-submit", \
     "--master", "local[*]", \
     "--conf", "spark.driver.memory=1g", \
     "--conf", "spark.executor.memory=1g", \
     "--conf", "spark.sql.shuffle.partitions=4", \
     "/app/spark_consumer.py"]
