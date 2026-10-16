#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS raw;
    CREATE SCHEMA IF NOT EXISTS staging;
    CREATE SCHEMA IF NOT EXISTS intermediate;
    CREATE SCHEMA IF NOT EXISTS marts;

    DO
    \$do\$
    BEGIN
       IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sds_app') THEN
          CREATE ROLE sds_app LOGIN PASSWORD '${SDS_APP_PASSWORD}';
       END IF;
    END
    \$do\$;

    GRANT USAGE, CREATE ON SCHEMA raw, staging, intermediate, marts TO sds_app;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw, staging, intermediate, marts TO sds_app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA raw, staging, intermediate, marts
      GRANT ALL PRIVILEGES ON TABLES TO sds_app;
EOSQL
