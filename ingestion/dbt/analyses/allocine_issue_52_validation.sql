-- Revue #52 du 14 novembre 2026 : 144 lignes de quarantaine, 16 ID Allociné.
-- Lecture seule dans cinestats-5050-db ; la vue legacy exige un rôle autorisé.
-- Les nombres attendus décrivent ce lot daté, pas une règle permanente du catalogue.
WITH decisions(cnc_visa, allocine_id, initial_rows, publish, decision) AS (
    VALUES
        (111864, '59833', 1, TRUE, 'confirmed'),
        (117557, '120326', 12, TRUE, 'confirmed'),
        (120846, '109311', 18, FALSE, 'wrong_work'),
        (126103, '186800', 1, TRUE, 'confirmed'),
        (139058, '226218', 1, TRUE, 'confirmed'),
        (141408, '233453', 2, TRUE, 'confirmed'),
        (142040, '231782', 16, TRUE, 'confirmed'),
        (146222, '287331', 9, TRUE, 'confirmed'),
        (152119, '309459', 1, FALSE, 'confirmed_identity_tv_date_deferred'),
        (155365, '260988', 16, FALSE, 'obsolete_wrong_work'),
        (160111, '319142', 5, FALSE, 'wrong_work'),
        (161050, '5459', 21, FALSE, 'wrong_work'),
        (162402, '236434', 15, FALSE, 'wrong_work'),
        (164127, '323303', 11, FALSE, 'wrong_work'),
        (165043, '112135', 8, FALSE, 'wrong_work'),
        (166339, '170268', 7, FALSE, 'wrong_work')
)
SELECT
    d.*,
    f.film_id,
    f.film_id = MD5(d.cnc_visa::text)::uuid AS film_id_preserved,
    f.movie_name,
    m."ID_ALLOCINE" AS raw_matching_id,
    m."VALIDATION_MANUELLE" AS raw_manual_validation,
    m."UPDATED_BY" AS matching_updated_by,
    m."UPDATED_DATE" AS matching_updated_date,
    s.allocine_id AS staging_id,
    s.extracted_ts AS existing_success_at,
    s.run_id AS existing_success_run_id,
    a.scrape_status AS latest_attempt_status,
    a.allocine_id AS latest_attempt_id,
    f.release_date AS final_release_date,
    l.release_date AS legacy_release_date,
    (SELECT COUNT(*) FROM raw.id_matching x
     WHERE x."VISA" = d.cnc_visa::text) AS matching_visa_rows,
    (SELECT COUNT(*) FROM raw.id_matching x
     WHERE x."ID_ALLOCINE" = d.allocine_id) AS matching_old_id_rows,
    (SELECT COUNT(*) FROM fnl.fnl_films x
     WHERE x.cnc_visa = d.cnc_visa) AS final_film_rows,
    (SELECT COUNT(*) FROM ops.film_credits_unmatched q
     WHERE q.allocine_id = d.allocine_id) AS remaining_quarantine_rows,
    (SELECT COUNT(*) FROM intermediate.int_credit_holders_role c
     WHERE c.allocine_id = d.allocine_id
       AND c.film_id = f.film_id) AS attached_scraped_rows,
    (SELECT COUNT(*) FROM intermediate.int_credit_holders_role c
     WHERE c.allocine_id = d.allocine_id
       AND c.film_id = f.film_id
       AND NOT EXISTS (
           SELECT 1 FROM fnl.fnl_film_credits fc
           WHERE fc.film_id = c.film_id
             AND fc.role_id = c.role_id
             AND fc.credit_holder_id = c.credit_holder_id
       )) AS attached_rows_missing_final,
    (SELECT COUNT(*) FROM fnl.fnl_film_credits fc
     WHERE fc.film_id = f.film_id) AS final_credit_rows,
    (SELECT ARRAY_AGG(h.first_name || ' ' || h.last_name
                     ORDER BY h.first_name, h.last_name)
     FROM fnl.fnl_film_credits fc
     JOIN fnl.fnl_role r USING (role_id)
     JOIN fnl.fnl_credit_holders h USING (credit_holder_id)
     WHERE fc.film_id = f.film_id
       AND r.role_name = 'Réalisateur') AS final_directors
FROM decisions d
LEFT JOIN raw.id_matching m ON m."VISA" = d.cnc_visa::text
LEFT JOIN fnl.fnl_films f ON f.cnc_visa = d.cnc_visa
LEFT JOIN staging.stg_allocine_films s ON s.cnc_visa = d.cnc_visa
LEFT JOIN ops.v_statistics_legacy_films l ON l.cnc_visa::text = d.cnc_visa::text
LEFT JOIN LATERAL (
    SELECT x.scrape_status, x.allocine_id FROM raw.allocine_data x
    WHERE x.source_record_id = d.cnc_visa::text
    ORDER BY x.extracted_at DESC NULLS LAST, x.run_id::text DESC,
             x.record_hash DESC
    LIMIT 1
) a ON TRUE
ORDER BY d.cnc_visa;

-- Compteurs globaux et intégrité des associations publiées.
SELECT
    (SELECT COUNT(*) FROM fnl.fnl_films) AS final_films,
    (SELECT COUNT(*) FROM fnl.fnl_film_credits) AS final_credits,
    (SELECT COUNT(*) FROM ops.film_credits_unmatched) AS quarantined_rows,
    (SELECT COUNT(DISTINCT allocine_id)
     FROM ops.film_credits_unmatched) AS quarantined_ids,
    (SELECT COUNT(*) FROM raw.id_matching
     WHERE NULLIF(BTRIM("ID_ALLOCINE"::text), '') IS NULL) AS missing_allocine_ids,
    (SELECT COUNT(*) FROM (
        SELECT film_id, role_id, credit_holder_id
        FROM fnl.fnl_film_credits GROUP BY 1, 2, 3 HAVING COUNT(*) > 1
    ) d) AS duplicate_credit_keys,
    (SELECT COUNT(*) FROM fnl.fnl_film_credits c
     WHERE NOT EXISTS (SELECT 1 FROM fnl.fnl_films f WHERE f.film_id = c.film_id)
        OR NOT EXISTS (SELECT 1 FROM fnl.fnl_credit_holders h
                       WHERE h.credit_holder_id = c.credit_holder_id)
        OR NOT EXISTS (SELECT 1 FROM fnl.fnl_role r WHERE r.role_id = c.role_id)
    ) AS orphan_credits;

-- Périmètre temporel des sept rattachements publiables, sans autre filtre métier.
-- Une date absente n'établit pas que le film est hors période.
SELECT
    COUNT(*) AS reviewed_films,
    COUNT(*) FILTER (WHERE f.release_date BETWEEN DATE '2004-01-01'
                    AND DATE '2024-12-31') AS selected_by_final_date,
    COUNT(*) FILTER (WHERE l.release_date BETWEEN DATE '2004-01-01'
                    AND DATE '2024-12-31') AS selected_by_legacy_date,
    COUNT(*) FILTER (WHERE f.release_date IS NULL) AS missing_final_date,
    (SELECT COUNT(*) FROM fnl.fnl_film_credits c
     JOIN fnl.fnl_films x USING (film_id)
     WHERE x.cnc_visa IN (111864,117557,126103,139058,141408,142040,146222)
    ) AS reviewed_final_credit_associations
FROM fnl.fnl_films f
LEFT JOIN ops.v_statistics_legacy_films l ON l.cnc_visa::text = f.cnc_visa::text
WHERE f.cnc_visa IN (111864,117557,126103,139058,141408,142040,146222);

-- Déduplication sémantique ciblée : une réalisation, identifiant existant, genre conservé.
SELECT f.cnc_visa, c.credit_holder_id, h.first_name, h.last_name, h.gender
FROM fnl.fnl_films f
JOIN fnl.fnl_film_credits c USING (film_id)
JOIN fnl.fnl_credit_holders h USING (credit_holder_id)
JOIN fnl.fnl_role r USING (role_id)
WHERE f.cnc_visa = 126103 AND r.role_name = 'Réalisateur';
