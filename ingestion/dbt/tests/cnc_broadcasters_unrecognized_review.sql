{{ config(severity='warn', tags=['phase2']) }}

-- Inconnus conservés dans le champ final, avec provenance pour revue.
SELECT * FROM {{ ref('cnc_broadcasters_unrecognized') }}
