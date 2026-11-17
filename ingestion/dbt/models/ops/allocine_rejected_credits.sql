{{ config(materialized='view', tags=['phase2']) }}

-- Une référence historique par visa, comme le staging avant invalidation.
-- Le détail de toutes les tentatives reste dans allocine_rejected_results.
WITH ranked AS (
    SELECT rejected.*, ROW_NUMBER() OVER (
        PARTITION BY COALESCE(NULLIF(visa_number::TEXT, ''), source_record_id::TEXT)
        ORDER BY extracted_at DESC NULLS LAST, run_id::TEXT DESC, record_hash DESC
    ) AS version_rank
    FROM {{ ref('allocine_rejected_results') }} AS rejected
    WHERE scrape_status = 'success'
), credits AS (
    SELECT
        r.visa_number::TEXT AS source_visa,
        r.allocine_id::TEXT AS allocine_id,
        r.run_id, r.record_hash,
        credit.*
    FROM ranked AS r
    CROSS JOIN LATERAL (
        SELECT 'Individual'::TEXT AS type, TRIM(value, '" ') AS full_name,
            NULL::TEXT AS legal_name, 'Réalisateur'::TEXT AS role
        FROM jsonb_array_elements_text(r.direction)
        UNION ALL
        SELECT 'Individual', TRIM(value, '" '), NULL, 'Acteur'
        FROM jsonb_array_elements_text(r.casting)
        UNION ALL
        SELECT 'Individual', TRIM(elem->>'name'), NULL,
            COALESCE(NULLIF(TRIM(elem->>'role'), ''), category.fallback_role)
        FROM (VALUES
            (r.screenwriters, 'screenwriter'), (r.production, 'production'),
            (r.technical_team, 'technical'), (r.distribution, 'distribution'),
            (r.soundtrack, 'soundtrack')
        ) AS category(payload, fallback_role)
        CROSS JOIN LATERAL jsonb_array_elements(category.payload) AS elem
        UNION ALL
        SELECT 'Company', NULL, TRIM(elem->>'name'), TRIM(elem->>'role')
        FROM jsonb_array_elements(r.companies) AS elem
    ) AS credit
    WHERE r.version_rank = 1
)
SELECT DISTINCT
    source_visa, allocine_id, run_id, record_hash, type,
    CASE WHEN type = 'Company' THEN MD5('company:' || NULLIF(TRIM(legal_name), ''))::UUID
        ELSE MD5(NULLIF(full_name, ''))::UUID END AS credit_holder_id,
    MD5(role)::UUID AS role_id,
    full_name, legal_name, role
FROM credits
