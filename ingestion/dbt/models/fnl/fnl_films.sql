WITH film_genres AS (
    SELECT
        film_id,
        STRING_AGG(DISTINCT genre_name, ', ' ORDER BY genre_name) AS genre
    FROM {{ ref('int_film_genres') }}
    GROUP BY film_id
),

max_allocation AS (
    SELECT
        film_id,
        country_name,
        budget_allocation,
        MAX(budget_allocation) OVER (PARTITION BY film_id) AS max_budget_allocation
    FROM {{ ref('fnl_film_country_budget_allocation') }}
),

french_financed AS (
    SELECT
        film_id,
        CASE
            WHEN budget_allocation = max_budget_allocation THEN TRUE
            ELSE FALSE
        END AS is_french_financed
    FROM max_allocation
    WHERE country_name = 'France'
)

SELECT
    films.film_id,
    films.cnc_visa,
    COALESCE(
        NULLIF(TRIM(matching.cnc_name), ''),
        NULLIF(TRIM(allocine.allocine_name), ''),
        films.cnc_name
    ) AS movie_name,
    films.cnc_agreement_year,
    allocine.release_date,
    allocine.duration_mn,
    films.budget,
    films.budget_category,
    film_genres.genre,
    films.broadcasters,
    french_financed.is_french_financed,
    films.has_parity_bonus,
    films.has_eof,
    films.has_sofica,
    films.has_tax_credit,
    films.has_regional_funding,
    films.filmography_rank,
    films.has_asr
FROM {{ ref('int_cnc_films') }} AS films
INNER JOIN {{ ref('int_id_matching') }} AS matching
    ON films.cnc_visa = matching.cnc_visa
LEFT JOIN {{ ref('int_allocine_films') }} AS allocine
    ON films.film_id = allocine.film_id
LEFT JOIN french_financed
    ON films.film_id = french_financed.film_id
LEFT JOIN film_genres
    ON films.film_id = film_genres.film_id
