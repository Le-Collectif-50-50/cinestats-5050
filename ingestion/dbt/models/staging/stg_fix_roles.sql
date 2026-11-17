{{
  config(materialized = 'table')
}}

SELECT
    CAST("ROLE_ID" AS TEXT)::UUID AS id,
    TRIM("ROLE_NAME") AS name,
    TRIM("ROLE_INCLUSIVE_NAME") AS inclusive_name,
    CAST("IS_KEY_ROLE" AS BOOLEAN) AS is_key_role,
    -- METADATA
    {{ gsheet_updated_timestamp('"UPDATED_DATE"') }} AS updated_date,
    TRIM("UPDATED_BY") AS updated_by,
    TRIM(_airbyte_raw_id) AS airbyte_raw_id,
    CAST(_airbyte_generation_id AS INTEGER) AS airbyte_generation_id,
    CAST(_airbyte_extracted_at AS TIMESTAMP) AS airbyte_extraction_date,
    CAST(_airbyte_meta AS JSON) AS airbyte_meta
FROM {{ source('raw', 'roles') }}
WHERE "UPDATED_BY" IS NOT NULL
    AND "UPDATED_DATE" IS NOT NULL
    AND "UPDATED_BY" <> 'Hugo Laurens'