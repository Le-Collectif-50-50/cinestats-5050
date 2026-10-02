-- Droits Postgres au moindre privilège pour cinestats-5050.
-- Appliqué par infra/vps/30-postgres.sh, idempotent (peut être rejoué à volonté).
-- Les rôles eux-mêmes (LOGIN + mot de passe) sont créés par le script.
-- Variable psql attendue : db_name.
--
-- Rappel : un GRANT ... ON ALL TABLES ne vaut que pour les tables existantes.
-- dbt et Airbyte recréent leurs tables à chaque run, d'où les ALTER DEFAULT
-- PRIVILEGES, qui s'appliquent aux tables créées ensuite par le rôle indiqué.

\set ON_ERROR_STOP on
SET client_min_messages = warning;

-- Personne n'a de droit implicite sur la base.
REVOKE ALL ON DATABASE :"db_name" FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- ===== Application : schéma public, tables ric_* =====
-- app_migrator possède la base, donc le schéma public : Alembic y crée les tables
-- et les extensions de confiance (unaccent, pg_trgm). Il ne sert qu'aux migrations.
GRANT CONNECT ON DATABASE :"db_name" TO app_migrator, app_ro;

-- app_ro : rôle d'exécution du backend, qui n'expose que des routes GET.
GRANT USAGE ON SCHEMA public TO app_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE app_migrator IN SCHEMA public GRANT SELECT ON TABLES TO app_ro;
ALTER ROLE app_ro SET default_transaction_read_only = on;
ALTER ROLE app_ro SET statement_timeout = '10s';
ALTER ROLE app_ro SET idle_in_transaction_session_timeout = '60s';
-- Pool SQLAlchemy par défaut : 5 + 10 de débordement par worker uvicorn.
ALTER ROLE app_ro CONNECTION LIMIT 20;

-- ===== Stack data (branche analytics : Airbyte, dbt, scrapers, Prefect, Metabase) =====
GRANT CONNECT ON DATABASE :"db_name" TO airbyte_user, dbt_user, prefect_user, metabase_user, metabase_ops_user;

-- Airbyte lance « CREATE SCHEMA IF NOT EXISTS » à chaque synchro, ce qui exige
-- CREATE sur la base même quand le schéma existe (vérifié sur Postgres 16).
GRANT CREATE, TEMPORARY ON DATABASE :"db_name" TO airbyte_user;

-- pgcrypto : gen_random_uuid() de ops.ingestion_run_requests.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS fnl;
CREATE SCHEMA IF NOT EXISTS ops;
ALTER SCHEMA raw OWNER TO airbyte_user;
ALTER SCHEMA staging OWNER TO dbt_user;
ALTER SCHEMA intermediate OWNER TO dbt_user;
ALTER SCHEMA fnl OWNER TO dbt_user;
REVOKE ALL ON SCHEMA ops FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA ops FROM PUBLIC;

-- dbt (et les scrapers, qui se connectent aussi en dbt_user) : écrit dans raw et ops,
-- lit ce qu'Airbyte charge dans raw.
GRANT USAGE, CREATE ON SCHEMA raw TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA ops TO dbt_user;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO dbt_user;
ALTER DEFAULT PRIVILEGES FOR ROLE airbyte_user IN SCHEMA raw GRANT SELECT ON TABLES TO dbt_user;

-- metabase_user : lecture seule de la couche finale.
GRANT USAGE ON SCHEMA fnl TO metabase_user;
GRANT SELECT ON ALL TABLES IN SCHEMA fnl TO metabase_user;
ALTER DEFAULT PRIVILEGES FOR ROLE dbt_user IN SCHEMA fnl GRANT SELECT ON TABLES TO metabase_user;
ALTER ROLE metabase_user SET default_transaction_read_only = on;

-- metabase_ops_user : lecture de toutes les couches, écriture dans ops (boutons d'action).
GRANT USAGE ON SCHEMA raw, staging, intermediate, fnl, ops TO metabase_ops_user;
GRANT SELECT ON ALL TABLES IN SCHEMA raw, staging, intermediate, fnl TO metabase_ops_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ops TO metabase_ops_user;
ALTER DEFAULT PRIVILEGES FOR ROLE airbyte_user IN SCHEMA raw GRANT SELECT ON TABLES TO metabase_ops_user;
ALTER DEFAULT PRIVILEGES FOR ROLE dbt_user IN SCHEMA raw, staging, intermediate, fnl GRANT SELECT ON TABLES TO metabase_ops_user;
ALTER DEFAULT PRIVILEGES FOR ROLE dbt_user IN SCHEMA ops GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO metabase_ops_user;

-- prefect_user : uniquement le cycle de vie des demandes d'ingestion. Sa propre
-- base de métadonnées vit sur le VPS data, pas ici.
GRANT USAGE ON SCHEMA ops TO prefect_user;
SELECT to_regclass('ops.ingestion_run_requests') IS NOT NULL AS has_ingestion_table \gset
\if :has_ingestion_table
  GRANT SELECT, UPDATE ON ops.ingestion_run_requests TO prefect_user;
\else
  \echo 'ops.ingestion_run_requests absente : relancer ce script après sa création (runbook analytics §4.3).'
\endif
