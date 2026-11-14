-- Deuxième action Allociné : visa CNC explicite et publication complète.
-- Même verrou que les lots : une seule demande Allociné active.
INSERT INTO ops.ingestion_run_requests (
    requested_by_metabase_user, requested_by_metabase_group, request_reason,
    request_source, request_type, max_films, visa_number, force_rescrape, dedupe_key
) VALUES (
    btrim({{email}}), 'C5050_Ops', btrim({{reason}}),
    'metabase', 'allocine', 1, btrim(CAST({{visa_number}} AS TEXT)),
    CASE lower(btrim({{force_rescrape}})) WHEN 'non' THEN false WHEN 'oui' THEN true END, 'metabase:allocine'
);
