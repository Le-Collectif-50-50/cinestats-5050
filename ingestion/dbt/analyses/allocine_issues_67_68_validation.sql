-- Issues #67/#68 : contrôles de publication, lecture seule.
-- Comparer avant/après à sources, clés et filtres constants, sans exporter les données.
BEGIN READ ONLY;

SELECT visa_number, allocine_id, COUNT(*) AS rejected_attempts,
       ARRAY_AGG(DISTINCT run_id) AS rejected_runs
FROM ops.allocine_rejected_results GROUP BY 1, 2 ORDER BY 1;

SELECT source_visa, allocine_id, COUNT(*) AS historical_credits
FROM ops.allocine_rejected_credits GROUP BY 1, 2 ORDER BY 1;

SELECT COUNT(*) AS rejected_associations_still_active
FROM staging.stg_allocine_films s
JOIN ops.allocine_association_rejections r
  ON s.source_record_id::text=r.source_record_id
 AND s.cnc_visa::text=r.visa_number AND s.allocine_id=r.allocine_id;

SELECT f.cnc_visa, f.film_id, f.movie_name, f.release_date,
       m."ID_ALLOCINE", m."VALIDATION_MANUELLE", COUNT(c.*) AS final_credits
FROM fnl.fnl_films f
LEFT JOIN raw.id_matching m ON m."VISA"=f.cnc_visa::text
LEFT JOIN fnl.fnl_film_credits c USING(film_id)
WHERE f.cnc_visa IN (120846,155365,160111,161050,162402,164127,165043,166339,
                    112488,151848,152119,160360)
GROUP BY 1,2,3,4,5,6 ORDER BY 1;

-- Cohorte intégrale : ces empreintes détectent aussi une modification hors des douze visas.
SELECT 'films' AS population, COUNT(*) AS n,
       MD5(STRING_AGG(TO_JSONB(f)::text,'|' ORDER BY film_id)) AS fingerprint
FROM fnl.fnl_films f;
SELECT 'credits' AS population, COUNT(*) AS n,
       MD5(STRING_AGG(TO_JSONB(c)::text,'|' ORDER BY film_id,credit_holder_id,role_id)) AS fingerprint
FROM fnl.fnl_film_credits c;

-- Jointure complète des lignes contribuant aux statistiques, avant tout filtre métier.
-- Si identique, ses sous-populations à filtres inchangés le sont aussi.
SELECT 'credits_2004_2024_with_film_holder_role' AS population, COUNT(*) AS n,
       MD5(STRING_AGG(JSONB_BUILD_ARRAY(f,c,h,r)::text,'|'
           ORDER BY c.film_id,c.credit_holder_id,c.role_id)) AS fingerprint
FROM fnl.fnl_film_credits c JOIN fnl.fnl_films f USING(film_id)
JOIN fnl.fnl_credit_holders h USING(credit_holder_id)
JOIN fnl.fnl_role r USING(role_id)
WHERE f.release_date >= DATE '2004-01-01' AND f.release_date < DATE '2025-01-01';

SELECT COUNT(*) AS duplicate_credit_keys FROM (
    SELECT film_id,credit_holder_id,role_id FROM fnl.fnl_film_credits
    GROUP BY 1,2,3 HAVING COUNT(*)>1
) d;
SELECT COUNT(*) AS orphan_credits FROM fnl.fnl_film_credits c
LEFT JOIN fnl.fnl_films f USING(film_id)
LEFT JOIN fnl.fnl_credit_holders h USING(credit_holder_id)
LEFT JOIN fnl.fnl_role r USING(role_id)
WHERE f.film_id IS NULL OR h.credit_holder_id IS NULL OR r.role_id IS NULL;

COMMIT;
