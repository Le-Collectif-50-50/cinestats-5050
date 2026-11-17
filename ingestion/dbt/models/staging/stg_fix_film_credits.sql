{{
  config(materialized = 'table')
}}

SELECT
    CAST("FILM_ID" AS TEXT)::UUID AS film_id,
    CAST("ROLE_ID" AS TEXT)::UUID AS role_id,
    CAST("CREDIT_HOLDER_ID" AS TEXT)::UUID AS credit_holder_id,
    -- METADATA
    {{ gsheet_updated_timestamp('"UPDATED_DATE"') }} AS updated_date,
    TRIM("UPDATED_BY") AS updated_by,
    _airbyte_raw_id AS airbyte_raw_id,
    CAST(_airbyte_generation_id AS INTEGER) AS airbyte_generation_id,
    CAST(_airbyte_extracted_at AS TIMESTAMP) AS airbyte_extraction_date,
    CAST(_airbyte_meta AS JSON) AS airbyte_meta
FROM {{ source('raw', 'film_credits') }}
WHERE NULLIF(TRIM("UPDATED_BY"), '') IS NOT NULL
    AND NULLIF(TRIM("UPDATED_DATE"), '') IS NOT NULL
    -- Signature exacte de la ligne exemple ; les autres lignes de Hugo sont acceptées.
    AND NOT (
        COALESCE("FILM_ID", '') = '0016b072-7ad8-f224-cfd7-053b56ff2720'
        AND COALESCE("ROLE_ID", '') = 'd894803c-210d-2b5b-6e7e-50f2d418bfcf'
        AND COALESCE("CREDIT_HOLDER_ID", '') = 'd8f8d53c-51b8-f89b-1a8d-da48da142694'
        AND {{ gsheet_updated_timestamp('"UPDATED_DATE"') }} = TIMESTAMP '2026-04-25 00:00:00'
        AND "UPDATED_BY" = 'Hugo Laurens'
    )
