{{ config(materialized='view') }}

-- Ne publier que l'affiche du dernier succès correspondant au mapping courant.
SELECT
    film.film_id,
    film.cnc_visa,
    NULLIF(TRIM(allocine.poster_url), '') AS poster_url
FROM {{ ref('fnl_films') }} AS film
INNER JOIN {{ ref('int_id_matching') }} AS matching
    ON film.film_id = matching.film_id
    AND film.cnc_visa = matching.cnc_visa
INNER JOIN {{ ref('stg_allocine_films') }} AS allocine
    ON matching.cnc_visa = allocine.cnc_visa
    AND matching.allocine_id = allocine.allocine_id
WHERE NULLIF(TRIM(allocine.poster_url), '') IS NOT NULL
