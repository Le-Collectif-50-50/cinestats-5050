{{
  config(materialized = 'table')
}}

SELECT
    CAST("VISA" AS INTEGER) AS cnc_visa,
    "TITRE" AS cnc_name,
    "GENRE" AS genre,
    CAST("ANNEE_D_AGREMENT" AS INTEGER) AS cnc_agreement_year,
    CASE
        -- Si l'année est >= 2013, on multiplie par 1 000 000 (peu importe le format)
        WHEN CAST("ANNEE_D_AGREMENT" AS INTEGER) >= 2013 THEN
            CAST(
                REPLACE(
                    TRANSLATE("DEVIS", ' ' || CHR(160) || CHR(8239), ''),
                    ',', '.'
                ) AS FLOAT
            ) * 1000000
        -- Sinon, on ne multiplie pas
        ELSE
            CAST(
                REPLACE(
                    TRANSLATE("DEVIS", ' ' || CHR(160) || CHR(8239), ''),
                    ',', '.'
                ) AS FLOAT
            )
    END AS budget,
    -- ARRAYS
    STRING_TO_ARRAY(REPLACE("REALISATEUR", ' ', ''), ' / ') AS director,
    CAST(REPLACE("RANG", ' ', '') AS TEXT) AS director_rank,
    STRING_TO_ARRAY(REPLACE("PRODUCTEURS", ' ', ''), ' / ') AS producer,
    CAST(REPLACE("PAYANT", ' ', '') AS TEXT) AS paid_broadcaster,
    CAST(REPLACE("CLAIR", ' ', '') AS TEXT) AS free_broadcaster,
    ARRAY(
        SELECT JSONB_BUILD_OBJECT(
            'country', INITCAP(UNACCENT(TRIM(REGEXP_REPLACE(elem, '[^a-zA-ZÀ-ÿ ]', '', 'g')))),
            'budget_allocation', NULLIF(REGEXP_REPLACE(elem, '[^0-9]', '', 'g'), '')::INTEGER
        )
        FROM UNNEST(
            STRING_TO_ARRAY(
                REGEXP_REPLACE(
                    REGEXP_REPLACE("NATIONALITE", '\s*/\s*', ' / ', 'g'),  -- normalise tous les '/' avec espaces
                    '\s+-', '-', 'g'),  -- supprime les espaces avant le '-'
                ' / ')
        ) AS elem
        WHERE "NATIONALITE" IS NOT NULL
            AND NULLIF(TRIM(elem), '') IS NOT NULL
    ) AS country_funder,
    -- BOOLEANS
    CASE
        WHEN "EOF" = 'OUI' THEN TRUE
        WHEN "EOF" = 'NON' THEN FALSE
        ELSE NULL
    END AS has_eof,
    CASE
        WHEN LOWER("BONUS_PARITE_") = 'x' THEN TRUE
        ELSE FALSE
    END AS has_parity_bonus,
    CASE
        WHEN LOWER("ASR") = 'x' THEN TRUE
        ELSE FALSE
    END AS has_asr,
    CASE
        WHEN LOWER("SOFICA") = 'x' THEN TRUE
        ELSE FALSE
    END AS has_sofica,
    CASE
        WHEN LOWER("CREDIT_D_IMPOT") = 'x' THEN TRUE
        ELSE FALSE
    END AS has_tax_credit,
    CASE
        WHEN LOWER("AIDE_REGIONALE") = 'x' THEN TRUE
        ELSE FALSE
    END AS has_regional_funding,
    -- METADATA
    TO_DATE("UPDATED_DATE", 'DD/MM/YYYY') AS updated_date,
    "UPDATED_BY" AS updated_by,
    _airbyte_raw_id AS airbyte_raw_id,
    CAST(_airbyte_generation_id AS INTEGER) AS airbyte_generation_id,
    CAST(_airbyte_extracted_at AS TIMESTAMP) AS airbyte_extraction_date,
    CAST(_airbyte_meta AS JSON) AS airbyte_meta
FROM {{ source('raw', 'films') }}
WHERE 1 = 1
    AND "UPDATED_DATE" IS NOT NULL
    AND "UPDATED_BY" IS NOT NULL