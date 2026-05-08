import psycopg2
import csv
import os

LOCAL = {"host": "localhost", "port": 5432, "dbname": "greenandcoop", "user": "postgres", "password": "postgres"}
RDS = {"host": "greenandcoop-db.c3myioi8qr9d.eu-west-3.rds.amazonaws.com", "port": 5432, "dbname": "greenandcoop", "user": "postgres", "password": "GreenCoop2026!"}

tables = ["infoclimat_raw", "wu_ichtegem_raw", "wu_la_madeleine_raw"]

local_conn = psycopg2.connect(**LOCAL)
rds_conn = psycopg2.connect(**RDS)
rds_conn.autocommit = True

for table in tables:
    print(f"\n--- Migration de {table} ---")
    
    # Récupérer la structure
    local_cur = local_conn.cursor()
    local_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}' ORDER BY ordinal_position")
    columns = local_cur.fetchall()
    
    # Créer la table sur RDS
    rds_cur = rds_conn.cursor()
    col_defs = ", ".join([f'"{c[0]}" {c[1]}' for c in columns])
    rds_cur.execute(f'DROP TABLE IF EXISTS "{table}"')
    rds_cur.execute(f'CREATE TABLE "{table}" ({col_defs})')
    
    # Copier les données
    import json
    from psycopg2.extras import Json
    
    local_cur.execute(f'SELECT * FROM "{table}"')
    rows = local_cur.fetchall()
    if rows:
        cleaned_rows = []
        for row in rows:
            cleaned_row = []
            for val in row:
                if isinstance(val, dict):
                    cleaned_row.append(Json(val))
                else:
                    cleaned_row.append(val)
            cleaned_rows.append(tuple(cleaned_row))
        placeholders = ",".join(["%s"] * len(columns))
        rds_cur.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', cleaned_rows)

