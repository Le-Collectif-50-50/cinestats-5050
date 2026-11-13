SELECT cnc_visa
FROM {{ ref('stg_allocine_films') }}
GROUP BY cnc_visa
HAVING COUNT(*) > 1 OR cnc_visa IS NULL
