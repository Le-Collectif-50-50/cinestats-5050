-- Les identifiants signalés par dbt sont rapprochés de la source actuelle pour revue.
SELECT
    r.run_started_at AT TIME ZONE 'Europe/Paris' AS execution_paris,
    ids.source_column AS colonne_source,
    ids.external_id AS identifiant,
    raw."VISA" AS visa_cnc,
    raw."TITRE" AS titre_cnc,
    raw."UPDATED_DATE" AS modification_source,
    raw._airbyte_raw_id AS ligne_raw
FROM ops.v_dbt_latest_results AS r
JOIN ops.dbt_test_failures AS f
    ON f.invocation_id = r.invocation_id AND f.unique_id = r.unique_id
JOIN raw.id_matching AS raw ON TRUE
CROSS JOIN LATERAL (
    VALUES
        ('allocine_id', 'ID_ALLOCINE', raw."ID_ALLOCINE"::TEXT),
        ('mubi_id', 'ID_MUBI', raw."ID_MUBI"::TEXT),
        ('tmdb_id', 'ID_TMDB', raw."ID_TMDB"::TEXT)
) AS ids(column_name, source_column, external_id)
WHERE r.model_name = 'int_id_matching'
  AND r.status IN ('warn', 'fail')
  AND r.node_name LIKE 'unique_%'
  AND ids.column_name = r.column_name
  AND ids.external_id = f.row_data->>'unique_field'
ORDER BY ids.source_column, ids.external_id, raw."VISA"
