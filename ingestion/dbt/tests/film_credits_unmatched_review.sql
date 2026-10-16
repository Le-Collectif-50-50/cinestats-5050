{{ config(severity='warn', store_failures=true, schema='ops', tags=['phase2']) }}

-- Les crédits sont conservés pour revue, mais exclus de la table finale.
SELECT *
FROM {{ ref('film_credits_unmatched') }}
