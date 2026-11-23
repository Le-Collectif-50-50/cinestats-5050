{{ config(materialized='view', tags=['phase2']) }}

SELECT
    films.cnc_visa,
    films.cnc_name,
    b.broadcaster_type,
    b.source_value,
    b.token
FROM {{ ref('stg_cnc_films') }} AS films
JOIN {{ ref('int_cnc_broadcasters') }} AS b
    ON (b.broadcaster_type = 'paid' AND b.source_value = films.paid_broadcaster)
    OR (b.broadcaster_type = 'free' AND b.source_value = films.free_broadcaster)
WHERE NOT b.is_recognized
