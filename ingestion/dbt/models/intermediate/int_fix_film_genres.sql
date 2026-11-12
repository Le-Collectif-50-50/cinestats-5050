WITH dedup AS (
    -- Une correction par association métier, en conservant la plus récente.
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY film_id, genre_id ORDER BY updated_date DESC) AS rn
    FROM {{ ref('stg_fix_film_genres') }}
)
SELECT
    film_id,
    genre_id
FROM dedup
WHERE rn = 1