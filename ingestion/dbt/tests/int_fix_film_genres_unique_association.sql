SELECT
    film_id,
    genre_id
FROM {{ ref('int_fix_film_genres') }}
GROUP BY film_id, genre_id
HAVING COUNT(*) > 1
