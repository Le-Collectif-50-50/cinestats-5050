-- Action SQL Metabase sur cinestats-ops-db.
-- Variables texte obligatoires : email (nom ou adresse e-mail), reason (texte long).
-- L'identité est déclarée par l'utilisateur, sans vérification automatique.
INSERT INTO ops.ingestion_run_requests (
  requested_by_metabase_user,
  requested_by_metabase_group,
  request_reason,
  request_source,
  dedupe_key
)
SELECT
  btrim({{email}}),
  'C5050_Ops',
  btrim({{reason}}),
  'metabase',
  CONCAT('metabase:', CURRENT_DATE::TEXT)
WHERE NOT EXISTS (
  SELECT 1
  FROM ops.ingestion_run_requests
  WHERE dedupe_key = CONCAT('metabase:', CURRENT_DATE::TEXT)
    AND request_status IN ('pending', 'processing', 'triggered')
);
