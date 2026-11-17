-- Issue 51 : contrôle des 25 décisions après synchronisation et publication.
-- Lecture seule. Exécuter dans cinestats-5050-db avec accès raw/staging/fnl/ops.
-- Le visa initial conserve le rapprochement legacy après correction de quatre visas source.
-- Le visa canonique et film_id suivent les valeurs corrigées de films et id_matching.
WITH expected(original_cnc_visa, cnc_visa, allocine_id, release_date, confirmed) AS (
    VALUES
        (107522, 107522, '53320', DATE '2004-06-09', TRUE),
        (108837, 108837, '54208', DATE '2004-09-29', TRUE),
        (109126, 109126, '56738', DATE '2004-12-15', TRUE),
        (109227, 109227, '54489', DATE '2004-09-29', TRUE),
        (109669, 109669, '55721', DATE '2005-04-20', TRUE),
        (109743, 109743, '55675', DATE '2007-07-25', TRUE),
        (111560, 111560, '139492', DATE '2008-12-10', TRUE),
        (112054, 112054, '44450', DATE '2006-03-29', TRUE),
        (112985, 112985, '110869', DATE '2007-09-26', TRUE),
        (113167, 113167, '110153', DATE '2007-09-12', TRUE),
        (115952, 115952, '110872', DATE '2007-06-20', TRUE),
        (122169, 136385, '138197', DATE '2014-09-03', TRUE),
        (122490, 122490, '146955', DATE '2010-02-17', TRUE),
        (124620, 124620, '204027', DATE '2015-02-18', TRUE),
        (126410, 126410, '188254', DATE '2011-02-09', TRUE),
        (127668, 127668, '189935', DATE '2011-09-14', TRUE),
        (128894, 128894, '191360', DATE '2012-11-28', TRUE),
        (130274, 130274, '193129', DATE '2013-06-05', TRUE),
        (146143, 146643, '255842', DATE '2019-05-01', TRUE),
        (148874, 148874, '292028', DATE '2021-11-24', TRUE),
        (149285, 149285, '298736', DATE '2022-09-07', TRUE),
        (150140, 150140, '270890', DATE '2021-11-24', TRUE),
        (152392, 152392, '283687', DATE '2020-09-30', TRUE),
        (154816, 154818, '279602', DATE '2023-03-29', TRUE),
        (155994, 154994, '291767', DATE '2023-01-25', TRUE)
)
SELECT
    e.original_cnc_visa,
    e.cnc_visa,
    e.confirmed,
    e.allocine_id AS expected_allocine_id,
    e.release_date AS expected_release_date,
    f.film_id,
    f.movie_name,
    f.release_date AS published_release_date,
    m."ID_ALLOCINE" AS raw_allocine_id,
    m."ID_MUBI" AS raw_mubi_id,
    m."ID_TMDB" AS raw_tmdb_id,
    m."VALIDATION_MANUELLE" AS raw_manual_validation,
    s.allocine_id AS staging_allocine_id,
    s.release_date AS staging_release_date,
    a.allocine_id AS latest_attempt_allocine_id,
    a.scrape_status AS latest_attempt_status,
    a.run_id AS latest_attempt_run_id,
    a.extracted_at AS latest_attempt_at,
    (SELECT COUNT(*) FROM raw.allocine_data x
     WHERE x.visa_number = e.cnc_visa::text
       AND x.extracted_at IS NOT DISTINCT FROM a.extracted_at) AS latest_timestamp_ties,
    (SELECT COUNT(*) FROM fnl.fnl_films x
     WHERE x.cnc_visa = e.cnc_visa) AS final_film_rows,
    (SELECT COUNT(*) FROM raw.id_matching x
     WHERE x."VISA" = e.cnc_visa::text) AS matching_rows,
    (SELECT COUNT(*) FROM raw.id_matching x
     WHERE x."ID_ALLOCINE" = e.allocine_id) AS allocine_id_matching_rows,
    (SELECT COUNT(*) FROM fnl.fnl_film_credits c
     WHERE c.film_id = f.film_id) AS published_credit_rows,
    (SELECT ARRAY_AGG(g.genre_name ORDER BY g.genre_name)
     FROM fnl.fnl_film_genre fg JOIN fnl.fnl_genre g USING (genre_id)
     WHERE fg.film_id = f.film_id) AS published_genres,
    (SELECT ARRAY_AGG(h.first_name || ' ' || h.last_name ORDER BY h.first_name, h.last_name)
     FROM fnl.fnl_film_credits c JOIN fnl.fnl_role r USING (role_id)
     JOIN fnl.fnl_credit_holders h USING (credit_holder_id)
     WHERE c.film_id = f.film_id AND r.role_name = 'Réalisateur') AS published_directors,
    l.release_date AS legacy_release_date
FROM expected e
LEFT JOIN fnl.fnl_films f ON f.cnc_visa = e.cnc_visa
LEFT JOIN raw.id_matching m ON m."VISA" = e.cnc_visa::text
LEFT JOIN staging.stg_allocine_films s ON s.cnc_visa = e.cnc_visa
LEFT JOIN ops.v_statistics_legacy_films l ON l.cnc_visa::text = e.original_cnc_visa::text
LEFT JOIN LATERAL (
    SELECT x.* FROM raw.allocine_data x
    WHERE x.visa_number = e.cnc_visa::text
    ORDER BY extracted_at DESC NULLS LAST, run_id DESC NULLS LAST,
             record_hash DESC NULLS LAST, MD5(ROW(x.*)::text) DESC
    LIMIT 1
) a ON TRUE
ORDER BY e.cnc_visa;
