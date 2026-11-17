-- Action SQL Metabase sur cinestats-ops-db ; identité déclarative.
-- Une seule demande Allociné active, indépendamment du jour et du demandeur.
-- La contrainte unique signale un doublon ; aucun faux succès silencieux.
-- Le cast texte -> entier rejette les décimales au lieu de les arrondir.
INSERT INTO ops.ingestion_run_requests (
    requested_by_metabase_user, requested_by_metabase_group, request_reason,
    request_source, request_type, max_films, dedupe_key
) VALUES (
    btrim({{email}}), 'C5050_Ops', btrim({{reason}}),
    'metabase', 'allocine', CAST(CAST({{max_films}} AS TEXT) AS INTEGER),
    'metabase:allocine'
);
