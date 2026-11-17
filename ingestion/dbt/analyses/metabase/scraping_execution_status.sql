-- Toutes les heures de la période sélectionnée, toutes exécutions confondues.
-- Une unité = une tentative stockée ; 14:37 est regroupé dans 14:00 (Paris).
WITH hourly_attempts AS (
    SELECT *, DATE_TRUNC('hour', extracted_at AT TIME ZONE 'Europe/Paris') AS heure_paris
    FROM raw.allocine_data
    WHERE extracted_at IS NOT NULL
      [[AND {{periode}}]]
)
SELECT
    TO_CHAR(a.heure_paris, 'YYYY-MM-DD HH24:MI') AS heure,
    COALESCE(NULLIF(a.scrape_status, ''), 'unknown') AS statut,
    COUNT(*) AS tentatives
FROM hourly_attempts a
WHERE TRUE
  [[AND BTRIM(a.visa_number) = BTRIM({{visa}})]]
  [[AND POSITION(LOWER({{titre}}) IN
      LOWER(COALESCE(a.original_name, '') || ' ' || COALESCE(a.allocine_title, ''))) > 0]]
GROUP BY a.heure_paris, COALESCE(NULLIF(a.scrape_status, ''), 'unknown')
ORDER BY a.heure_paris ASC, statut
