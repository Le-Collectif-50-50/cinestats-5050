-- Dernier résultat observé pour chaque test ou modèle, même après un run partiel.
SELECT
    run_started_at AT TIME ZONE 'Europe/Paris' AS execution_paris,
    model_name AS modele,
    column_name AS colonne,
    node_name AS controle,
    status AS statut,
    failures AS lignes_ou_valeurs_concernees,
    message AS detail
FROM ops.v_dbt_latest_results
WHERE status IN ('warn', 'fail', 'error', 'skipped')
ORDER BY CASE status WHEN 'error' THEN 0 WHEN 'fail' THEN 1 WHEN 'warn' THEN 2 ELSE 3 END,
         model_name, node_name
