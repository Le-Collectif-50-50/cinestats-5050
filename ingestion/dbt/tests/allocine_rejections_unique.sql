SELECT source_record_id, visa_number, allocine_id
FROM {{ ref('allocine_association_rejections') }}
GROUP BY 1, 2, 3
HAVING COUNT(*) > 1
