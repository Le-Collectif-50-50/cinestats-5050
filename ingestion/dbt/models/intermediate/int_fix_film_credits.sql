WITH dedup AS (
    -- Une correction par association métier, en conservant la plus récente.
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY film_id, role_id, credit_holder_id ORDER BY updated_date DESC NULLS LAST, airbyte_extraction_date DESC NULLS LAST, airbyte_raw_id DESC) AS rn
    FROM {{ ref('stg_fix_film_credits') }}
)
SELECT
    film_id,
    role_id,
    credit_holder_id
FROM dedup
WHERE rn = 1