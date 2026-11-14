-- Les corrections ajoutent des associations sans remplacer les genres scrapés.
SELECT
    film_id,
    genre_id
FROM {{ ref('int_film_genres') }}

UNION

SELECT
    film_id,
    genre_id
FROM {{ ref('int_fix_film_genres') }}
