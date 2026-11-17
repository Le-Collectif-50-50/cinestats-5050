-- Suivi technique des demandes Metabase, y compris celles sans résultat film.
SELECT requested_at AS demande_le, requested_by_metabase_user AS demandeur,
       request_reason AS motif, max_films AS films_maximum,
       visa_number AS visa_cnc, force_rescrape AS retraitement_force,
       CASE request_status
           WHEN 'pending' THEN 'En attente'
           WHEN 'processing' THEN 'Transmise / en cours'
           WHEN 'success' THEN 'Terminée'
           WHEN 'failed' THEN 'Échec'
           ELSE request_status
       END AS etat_demande,
       processed_at AS terminee_le, triggered_flow_run_id AS execution_prefect,
       trigger_error AS erreur, request_id AS demande_id
FROM ops.ingestion_run_requests
WHERE request_type = 'allocine'
ORDER BY requested_at DESC, request_id DESC
LIMIT 50
