SELECT film_id, genre_id
FROM {{ ref('int_fix_film_genres') }}
EXCEPT
SELECT film_id, genre_id
FROM {{ ref('fnl_film_genre') }}
