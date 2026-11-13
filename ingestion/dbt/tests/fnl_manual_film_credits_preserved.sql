SELECT film_id, role_id, credit_holder_id
FROM {{ ref('int_fix_film_credits') }}
EXCEPT
SELECT film_id, role_id, credit_holder_id
FROM {{ ref('fnl_film_credits') }}
