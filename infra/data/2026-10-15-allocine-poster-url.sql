-- Migration additive ingestion, à exécuter avec le propriétaire des tables.
-- Appliquer avant le nouveau connecteur et dbt phase2 sur une base existante.
BEGIN;
ALTER TABLE raw.allocine_data ADD COLUMN IF NOT EXISTS poster_url TEXT;

-- Journal indépendant : les métadonnées de collecte initiales restent intactes.
CREATE TABLE IF NOT EXISTS raw.allocine_data_poster_backfill (
    attempt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id text NOT NULL,
    attempted_at timestamptz NOT NULL DEFAULT now(),
    source_record_id text NOT NULL,
    allocine_id integer NOT NULL,
    source_url text NOT NULL,
    poster_url text,
    status text NOT NULL CHECK (status IN ('updated', 'missing', 'error', 'unchanged')),
    error_message text,
    updated_rows integer NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_allocine_poster_backfill_source
    ON raw.allocine_data_poster_backfill (source_record_id, allocine_id, attempted_at);
COMMIT;
