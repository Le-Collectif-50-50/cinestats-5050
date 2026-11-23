{{ config(materialized='table') }}

-- Normaliser chaque valeur source distincte une seule fois ; garder sa provenance.
WITH source_values AS (
    SELECT DISTINCT 'paid'::text AS broadcaster_type, paid_broadcaster AS source_value
    FROM {{ ref('stg_cnc_films') }}
    WHERE NULLIF(TRIM(paid_broadcaster), '') IS NOT NULL
    UNION
    SELECT DISTINCT 'free'::text, free_broadcaster
    FROM {{ ref('stg_cnc_films') }}
    WHERE NULLIF(TRIM(free_broadcaster), '') IS NOT NULL
)
SELECT DISTINCT
    source_values.broadcaster_type,
    source_values.source_value,
    tokens.token,
    tokens.broadcaster_name,
    tokens.is_recognized,
    tokens.is_excluded
FROM source_values
CROSS JOIN LATERAL (
    {{ cnc_broadcaster_tokens('source_values.source_value') }}
) AS tokens
