-- Classer toutes les tentatives AVANT de filtrer les anomalies : une réussite
-- plus récente retire le film de la file. Aucun rafraîchissement dbt requis.
WITH ranked_attempts AS (
    SELECT
        a.*,
        ROW_NUMBER() OVER (
            PARTITION BY
                CASE
                    WHEN NULLIF(BTRIM(source_record_id), '') IS NOT NULL THEN 'source'
                    WHEN NULLIF(BTRIM(visa_number), '') IS NOT NULL THEN 'visa'
                    ELSE 'unidentified'
                END,
                COALESCE(NULLIF(BTRIM(source_record_id), ''),
                         NULLIF(BTRIM(visa_number), ''),
                         record_hash, MD5(ROW(a.*)::TEXT))
            ORDER BY extracted_at DESC NULLS LAST,
                     run_id DESC NULLS LAST, record_hash DESC NULLS LAST,
                     MD5(ROW(a.*)::TEXT) DESC
        ) AS attempt_rank
    FROM raw.allocine_data AS a
), review_queue AS (
    SELECT *
    FROM ranked_attempts
    WHERE attempt_rank = 1
      AND scrape_status IN ('needs_review', 'visa_mismatch', 'not_found')
      [[AND BTRIM(visa_number) = BTRIM({{visa}})]]
      [[AND POSITION(LOWER({{titre}}) IN
          LOWER(COALESCE(original_name, '') || ' ' || COALESCE(allocine_title, ''))) > 0]]
)
