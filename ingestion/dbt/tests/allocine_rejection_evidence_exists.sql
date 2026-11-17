-- Chaque rejet doit désigner un succès brut existant de la même association.
SELECT rejection.*
FROM {{ ref('allocine_association_rejections') }} AS rejection
WHERE NOT EXISTS (
    SELECT 1 FROM {{ source('raw', 'allocine_data') }} AS result
    WHERE result.source_record_id::TEXT = rejection.source_record_id::TEXT
        AND result.visa_number::TEXT = rejection.visa_number::TEXT
        AND result.allocine_id::TEXT = rejection.allocine_id::TEXT
        AND result.run_id::TEXT = rejection.evidence_run_id::TEXT
        AND result.record_hash = rejection.evidence_record_hash
        AND result.scrape_status = 'success'
)
