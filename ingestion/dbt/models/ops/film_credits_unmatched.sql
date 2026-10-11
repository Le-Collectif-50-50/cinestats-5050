{{ config(materialized='table', tags=['phase2']) }}

WITH source_films AS (
    SELECT
        allocine_id,
        ARRAY_AGG(DISTINCT cnc_visa) AS source_visas,
        ARRAY_AGG(DISTINCT cnc_name) AS source_titles
    FROM {{ ref('stg_allocine_films') }}
    GROUP BY allocine_id
)
SELECT
    credits.allocine_id,
    credits.credit_holder_id,
    credits.role_id,
    credits.type,
    credits.full_name,
    credits.legal_name,
    credits.role,
    films.source_visas,
    films.source_titles
FROM {{ ref('int_credit_holders_role') }} AS credits
LEFT JOIN source_films AS films
    ON credits.allocine_id = films.allocine_id
WHERE credits.film_id IS NULL
