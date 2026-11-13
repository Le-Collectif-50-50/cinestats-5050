WITH dedup AS (
    -- Si 2 corrections sont faites pour un même id, on ne garde que la plus récente
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_date DESC NULLS LAST, airbyte_extraction_date DESC NULLS LAST, airbyte_raw_id DESC) AS rn
    FROM {{ ref('stg_fix_credit_holders') }}
)
SELECT
    id,
    type,
    first_name,
    last_name,
    legal_name,
    gender,
    birthdate
FROM dedup
WHERE rn = 1