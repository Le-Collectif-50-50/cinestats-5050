-- Les corrections ajoutent des associations ; elles ne suppriment pas les crédits scrapés.
SELECT DISTINCT
    film_id,
    role_id,
    credit_holder_id
FROM {{ ref('int_credit_holders_role') }}
WHERE film_id IS NOT NULL

UNION

SELECT
    film_id,
    role_id,
    credit_holder_id
FROM {{ ref('int_fix_film_credits') }}
