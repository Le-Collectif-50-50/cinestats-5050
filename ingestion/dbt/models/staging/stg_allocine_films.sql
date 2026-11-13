{{
  config(materialized = 'table')
}}

-- Conserver le dernier succès par visa source, même si une tentative ultérieure échoue.
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY COALESCE(NULLIF(visa_number::TEXT, ''), source_record_id::TEXT)
        ORDER BY extracted_at DESC NULLS LAST, run_id::TEXT DESC, record_hash DESC
    ) AS version_rank
    FROM {{ source('raw', 'allocine_data') }}
    WHERE scrape_status = 'success'
)
SELECT
    CAST(visa_number AS INTEGER) AS cnc_visa,
    CAST(NULLIF(REGEXP_REPLACE(allocine_visa_number, '[^0-9]', '', 'g'), '') AS INTEGER) AS allocine_visa,
    CAST(allocine_id AS TEXT) AS allocine_id,
    original_name AS cnc_name,
    allocine_title AS allocine_name,
    CAST(cnc_agrement_year AS INTEGER) AS cnc_agreement_year,
    release_date_raw,
    CAST(release_date AS DATE) AS release_date,
    duration_raw,
    CAST(duration_minutes AS INTEGER) AS duration_mn,
    search_url AS search_url,
    source_url AS source_url,
    allocine_url AS allocine_url,
    poster_url AS poster_url,
    trailer_url AS trailer_url,
    ARRAY(
        SELECT jsonb_array_elements_text("genres")
    ) AS genres,
    ARRAY(
        SELECT jsonb_array_elements_text("direction")
    ) AS direction,
    ARRAY(
        SELECT jsonb_array_elements_text("casting")
    ) AS casting,
    screenwriters,
    production,
    technical_team,
    soundtrack,
    distribution,
    companies,
    -- METADATA
    run_id AS run_id,
    CAST(extracted_at AS TIMESTAMP) AS extracted_ts,
    CAST(source_record_id AS INTEGER) AS source_record_id,
    match_strategy AS match_strategy,
    scrape_status AS scrapping_status,
    error_message AS error_message,
    record_hash AS record_hash
FROM ranked
WHERE version_rank = 1
