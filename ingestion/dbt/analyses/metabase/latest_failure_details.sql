-- Détails du même run que le dernier résultat : aucune jointure avec un run antérieur.
SELECT
    r.run_started_at AT TIME ZONE 'Europe/Paris' AS execution_paris,
    r.model_name AS modele,
    r.column_name AS colonne,
    r.node_name AS controle,
    COALESCE(f.row_data->>'unique_field', f.row_data->>'cnc_visa',
             f.row_data->>'allocine_id') AS identifiant,
    f.row_data->>'cnc_name' AS titre_cnc,
    f.row_data->>'n_records' AS occurrences,
    f.row_data AS details
FROM ops.v_dbt_latest_results AS r
JOIN ops.dbt_test_failures AS f
    ON f.invocation_id = r.invocation_id AND f.unique_id = r.unique_id
WHERE r.status IN ('warn', 'fail')
ORDER BY r.model_name, r.node_name, f.row_number
