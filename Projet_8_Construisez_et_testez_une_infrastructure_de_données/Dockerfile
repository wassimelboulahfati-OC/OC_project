FROM python:3.11-slim

RUN pip install dbt-postgres==1.10.0

WORKDIR /dbt

COPY greenandcoop/ /dbt/
COPY profiles_prod.yml /root/.dbt/profiles.yml

CMD ["dbt", "run", "--target", "prod"]
