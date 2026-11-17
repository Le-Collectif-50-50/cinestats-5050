SELECT film_id, role_id, credit_holder_id
FROM {{ ref('fnl_film_credits') }}
GROUP BY film_id, role_id, credit_holder_id
HAVING COUNT(*) > 1
