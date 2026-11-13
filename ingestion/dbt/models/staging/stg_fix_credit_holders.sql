{{
  config(materialized = 'table')
}}

SELECT
    CAST("CREDIT_HOLDER_ID" AS TEXT)::UUID AS id,
    NULLIF(TRIM("TYPE"), '') AS type,
    NULLIF(TRIM("FIRST_NAME"), '') AS first_name,
    NULLIF(TRIM("LAST_NAME"), '') AS last_name,
    NULLIF(TRIM("LEGAL_NAME"), '') AS legal_name,
    NULLIF(TRIM("GENDER"), '') AS gender,
    TO_DATE(NULLIF(TRIM("BIRTHDATE"), ''), 'DD/MM/YYYY') AS birthdate,
    -- METADATA
    {{ gsheet_updated_timestamp('"UPDATED_DATE"') }} AS updated_date,
    TRIM("UPDATED_BY") AS updated_by,
    TRIM(_airbyte_raw_id) AS airbyte_raw_id,
    CAST(_airbyte_generation_id AS INTEGER) AS airbyte_generation_id,
    CAST(_airbyte_extracted_at AS TIMESTAMP) AS airbyte_extraction_date,
    CAST(_airbyte_meta AS JSON) AS airbyte_meta
FROM {{ source('raw', 'credit_holders') }}
WHERE NULLIF(TRIM("UPDATED_BY"), '') IS NOT NULL
    AND NULLIF(TRIM("UPDATED_DATE"), '') IS NOT NULL
    -- Exclure la ligne de démonstration, pas les corrections de son auteur.
    AND NOT (
        "CREDIT_HOLDER_ID" = '000a676c-8ef7-5b14-8a67-9431ceeb933e'
        AND COALESCE("FIRST_NAME", '') = 'Example'
        AND COALESCE("LAST_NAME", '') = 'Example'
    )
