{{ config(materialized='view', tags=['phase2']) }}

-- Toutes les tentatives des associations rejetées, sans suppression du brut.
-- Les clés run/hash proviennent de chaque résultat, les preuves de la décision.
SELECT
    raw_result.*,
    rejection.reason AS rejection_reason,
    rejection.source_url AS rejection_source_url,
    rejection.reviewed_at,
    rejection.reviewed_by,
    rejection.evidence_run_id,
    rejection.evidence_record_hash
FROM {{ source('raw', 'allocine_data') }} AS raw_result
INNER JOIN {{ ref('allocine_association_rejections') }} AS rejection
    ON rejection.source_record_id::TEXT = raw_result.source_record_id::TEXT
    AND rejection.visa_number::TEXT = raw_result.visa_number::TEXT
    AND rejection.allocine_id::TEXT = raw_result.allocine_id::TEXT
