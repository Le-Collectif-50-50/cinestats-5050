-- Table de file des demandes d'ingestion (runbook analytics §4.3).
-- Créée en dbt_user : les droits par défaut de roles.sql (ALTER DEFAULT PRIVILEGES
-- FOR ROLE dbt_user IN SCHEMA ops) s'appliquent alors aux rôles Metabase.
-- Les droits de prefect_user sont posés ensuite en relançant roles.sql.
SET ROLE dbt_user;

CREATE TABLE IF NOT EXISTS ops.ingestion_run_requests (
  request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requested_at TIMESTAMP NOT NULL DEFAULT now(),
  requested_by_metabase_user TEXT NOT NULL,
  requested_by_metabase_group TEXT,
  request_reason TEXT,
  request_source TEXT NOT NULL DEFAULT 'metabase',
  request_status TEXT NOT NULL DEFAULT 'pending',
  claimed_at TIMESTAMP,
  claimed_by TEXT,
  processed_at TIMESTAMP,
  triggered_flow_run_id TEXT,
  trigger_error TEXT,
  dedupe_key TEXT NOT NULL
);

-- Migration additive pour les files déjà en service ; historique conservé.
ALTER TABLE ops.ingestion_run_requests
  ADD COLUMN IF NOT EXISTS request_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_ingestion_run_requests_status_requested_at
  ON ops.ingestion_run_requests (request_status, requested_at ASC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ingestion_run_requests_dedupe_key_active
  ON ops.ingestion_run_requests (dedupe_key)
  WHERE request_status IN ('pending', 'processing');

RESET ROLE;
