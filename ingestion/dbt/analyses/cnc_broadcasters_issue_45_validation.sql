-- Validation read-only de #45 : comparaison d'ensembles, puis filtres identiques.
-- Cohorte commune : visas rapprochés dont les DEUX dates tombent en 2004–2024.
-- Le périmètre historique « au moins une des deux dates » est compté séparément.
WITH matched AS (
    SELECT f.cnc_visa, f.movie_name, f.broadcasters AS current_names,
           l.broadcasters AS legacy_names,
           f.release_date AS dbt_release_date, l.release_date AS legacy_release_date,
           f.is_french_financed AS current_french, l.is_french_financed AS legacy_french,
           ARRAY(SELECT DISTINCT btrim(x) FROM unnest(string_to_array(COALESCE(f.broadcasters,''), ',')) x
                 WHERE btrim(x)<>'' ORDER BY 1) AS current_set,
           ARRAY(SELECT DISTINCT btrim(x) FROM unnest(string_to_array(COALESCE(l.broadcasters,''), ',')) x
                 WHERE btrim(x)<>'' ORDER BY 1) AS legacy_set
    FROM fnl.fnl_films f
    JOIN ops.v_statistics_legacy_films l ON l.cnc_visa=f.cnc_visa::text
), historical AS (
    SELECT * FROM matched
    WHERE dbt_release_date BETWEEN DATE '2004-01-01' AND DATE '2024-12-31'
       OR legacy_release_date BETWEEN DATE '2004-01-01' AND DATE '2024-12-31'
), common AS (
    SELECT * FROM matched
    WHERE dbt_release_date BETWEEN DATE '2004-01-01' AND DATE '2024-12-31'
      AND legacy_release_date BETWEEN DATE '2004-01-01' AND DATE '2024-12-31'
), funders AS (
    SELECT unnest(ARRAY['Canal+','Ciné+','France2','M6','W9']) AS name
)
SELECT json_build_object(
    'historical_scope', (SELECT json_build_object('rows',count(*),'visas',count(DISTINCT cnc_visa),
        'different_strings',count(*) FILTER(WHERE current_names IS DISTINCT FROM legacy_names),
        'different_sets',count(*) FILTER(WHERE current_set<>legacy_set)) FROM historical),
    'common_scope', (SELECT json_build_object('visas',count(DISTINCT cnc_visa),
        'different_sets',count(*) FILTER(WHERE current_set<>legacy_set)) FROM common),
    'filters_common_scope',(SELECT json_agg(t) FROM (
        SELECT name, count(DISTINCT cnc_visa) FILTER(WHERE name=ANY(legacy_set)) AS legacy,
            count(DISTINCT cnc_visa) FILTER(WHERE name=ANY(current_set)) AS current,
            count(DISTINCT cnc_visa) FILTER(WHERE (name=ANY(legacy_set))<>(name=ANY(current_set))) AS different_members
        FROM common CROSS JOIN funders GROUP BY name ORDER BY name) t),
    'residual_pairs',(SELECT json_agg(t) FROM (
        SELECT legacy_set,current_set,count(*) AS films
        FROM historical WHERE current_set<>legacy_set GROUP BY 1,2 ORDER BY count(*) DESC,1,2) t),
    'residual_films',(SELECT json_agg(t) FROM (
        SELECT cnc_visa,movie_name,legacy_set,current_set,dbt_release_date,legacy_release_date
        FROM historical WHERE current_set<>legacy_set ORDER BY cnc_visa) t)
);
