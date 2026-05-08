FROM python:3.12-slim

RUN pip install --no-cache-dir dbt-postgres==1.10.0

WORKDIR /dbt
COPY . /dbt/

RUN mkdir -p /root/.dbt
RUN echo 'greenandcoop:\n  target: prod\n  outputs:\n    prod:\n      type: postgres\n      host: "{{ env_var(\"DBT_HOST\") }}"\n      port: 5432\n      user: "{{ env_var(\"DBT_USER\") }}"\n      pass: "{{ env_var(\"DBT_PASSWORD\") }}"\n      dbname: "{{ env_var(\"DBT_DBNAME\") }}"\n      schema: public\n      threads: 1' > /root/.dbt/profiles.yml

CMD ["dbt", "build", "--target", "prod"]
