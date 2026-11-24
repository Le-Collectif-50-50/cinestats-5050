{{ config(materialized='view', tags=['phase2', 'mubi']) }}

-- Une ligne par visa du référentiel, sans multiplier les événements par visa.
-- Les compteurs globaux du dashboard dédupliquent séparément les ID Mubi.
WITH latest AS (
    SELECT DISTINCT ON (mubi_id) mubi_id, run_id, extracted_at, scrape_status,
           error_message, film_link
    FROM {{ source('raw', 'mubi_film_awards') }}
    WHERE mubi_id IS NOT NULL
    ORDER BY mubi_id, extracted_at DESC NULLS LAST, run_id DESC
), completed AS (
    SELECT mubi_id, max(extracted_at) AS last_success_at
    FROM {{ source('raw', 'mubi_film_awards') }}
    WHERE scrape_status IN ('success', 'no_awards')
    GROUP BY mubi_id
)
SELECT CAST(m.cnc_visa AS TEXT) AS cnc_visa, m.cnc_name AS title, m.mubi_id AS source_mubi_id,
       NULLIF(ltrim(btrim(m.mubi_id), '0'), '') AS mubi_id,
       l.run_id, l.extracted_at, l.scrape_status, l.error_message, l.film_link,
       c.last_success_at,
       CASE WHEN m.mubi_id IS NULL OR btrim(m.mubi_id) = '' THEN 'missing_id'
            WHEN btrim(m.mubi_id) !~ '^[0-9]+$'
              OR length(ltrim(btrim(m.mubi_id), '0')) = 0
              OR length(ltrim(btrim(m.mubi_id), '0')) > 10
              OR (length(ltrim(btrim(m.mubi_id), '0')) = 10
                  AND ltrim(btrim(m.mubi_id), '0') > '2147483647') THEN 'invalid_id'
            WHEN c.last_success_at IS NOT NULL THEN 'completed'
            ELSE 'pending' END AS eligibility
FROM {{ ref('int_id_matching') }} m
LEFT JOIN latest l ON ltrim(btrim(m.mubi_id), '0') = CAST(l.mubi_id AS TEXT)
LEFT JOIN completed c ON ltrim(btrim(m.mubi_id), '0') = CAST(c.mubi_id AS TEXT)
