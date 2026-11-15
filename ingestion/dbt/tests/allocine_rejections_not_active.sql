SELECT active.cnc_visa, active.allocine_id
FROM {{ ref('stg_allocine_films') }} AS active
INNER JOIN {{ ref('allocine_association_rejections') }} AS rejection
    ON active.source_record_id::TEXT = rejection.source_record_id::TEXT
    AND active.cnc_visa::TEXT = rejection.visa_number::TEXT
    AND active.allocine_id::TEXT = rejection.allocine_id::TEXT
