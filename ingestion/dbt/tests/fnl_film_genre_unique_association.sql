SELECT film_id, genre_id
FROM {{ ref('fnl_film_genre') }}
GROUP BY film_id, genre_id
HAVING COUNT(*) > 1
