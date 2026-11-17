WITH dedup AS (
    -- Si 2 corrections sont faites pour un même id, on ne garde que la plus récente
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY film_country_budget_allocation_id ORDER BY updated_date DESC NULLS LAST, airbyte_extraction_date DESC NULLS LAST, airbyte_raw_id DESC) AS rn
    FROM {{ ref('stg_fix_film_country_budget_allocation') }}
)
SELECT
    film_country_budget_allocation_id,
    country_id,
    film_id,
    budget_allocation
FROM dedup
WHERE rn = 1