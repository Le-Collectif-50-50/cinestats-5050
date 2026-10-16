SELECT
    run_started_at AT TIME ZONE 'Europe/Paris' AS execution_paris,
    invocation_id AS execution_dbt,
    command AS commande,
    COUNT(*) FILTER (WHERE status IN ('pass', 'success')) AS reussites,
    COUNT(*) FILTER (WHERE status = 'warn') AS avertissements,
    COUNT(*) FILTER (WHERE status IN ('fail', 'error')) AS erreurs,
    COUNT(*) FILTER (WHERE status = 'skipped') AS ignores
FROM ops.dbt_run_results
GROUP BY run_started_at, invocation_id, command
ORDER BY run_started_at DESC
LIMIT 100
