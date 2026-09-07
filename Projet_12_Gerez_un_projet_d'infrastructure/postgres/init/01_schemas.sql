-- Création des schémas du pattern medallion
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS marts;

-- Utilisateur applicatif à droits limités (bonne pratique sécurité)
-- Il ne pourra qu'agir sur les données, pas administrer la base.
DO

$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sds_app') THEN
      CREATE ROLE sds_app LOGIN PASSWORD 'Kx7pR2mVq9Lz4Wt6';
   END IF;
END

$$;

GRANT USAGE, CREATE ON SCHEMA raw, staging, intermediate, marts TO sds_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw, staging, intermediate, marts TO sds_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw, staging, intermediate, marts
  GRANT ALL PRIVILEGES ON TABLES TO sds_app;
