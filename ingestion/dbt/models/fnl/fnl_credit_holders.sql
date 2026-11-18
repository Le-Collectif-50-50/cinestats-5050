SELECT
    DISTINCT
    COALESCE(casting.credit_holder_id, fix.id) AS credit_holder_id,
    COALESCE(fix.type, casting.type) AS type,
    CASE
        WHEN COALESCE(fix.type, casting.type) = 'Company' THEN NULL
        WHEN NULLIF(TRIM(fix.first_name), '') IS NOT NULL
            OR NULLIF(TRIM(fix.last_name), '') IS NOT NULL
        THEN NULLIF(CONCAT_WS(' ',
            COALESCE(NULLIF(TRIM(fix.first_name), ''), NULLIF(TRIM(casting.first_name), '')),
            COALESCE(NULLIF(TRIM(fix.last_name), ''), NULLIF(TRIM(casting.last_name), ''))
        ), '')
        ELSE COALESCE(
            NULLIF(TRIM(casting.full_name), ''),
            NULLIF(CONCAT_WS(' ',
                NULLIF(TRIM(casting.first_name), ''),
                NULLIF(TRIM(casting.last_name), '')
            ), '')
        )
    END AS full_name,
    COALESCE(fix.first_name, casting.first_name) AS first_name,
    COALESCE(fix.last_name, casting.last_name) AS last_name,
    COALESCE(fix.legal_name, casting.legal_name) AS legal_name,
    COALESCE(fix.gender, genre.gender) AS gender,
    COALESCE(fix.birthdate, NULL) AS birthdate
FROM {{ ref('int_credit_holders_role') }} AS casting
LEFT JOIN {{ ref('int_credit_holders_genre') }} AS genre
    ON LOWER(casting.full_name) = LOWER(genre.full_name)
FULL OUTER JOIN {{ ref('int_fix_credit_holders') }} AS fix
    ON casting.credit_holder_id = fix.id
ORDER BY credit_holder_id
