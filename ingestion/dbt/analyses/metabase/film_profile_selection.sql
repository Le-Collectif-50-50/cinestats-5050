WITH selected_films AS (
    SELECT f.*
    FROM fnl.fnl_films AS f
    WHERE (FALSE
        [[OR NULLIF(TRIM({{visa}}), '') IS NOT NULL]]
        [[OR NULLIF(TRIM({{titre}}), '') IS NOT NULL]])
      [[AND f.cnc_visa::text = TRIM({{visa}})]]
      [[AND STRPOS(LOWER(f.movie_name), LOWER(TRIM({{titre}}))) > 0]]
), credits AS (
    SELECT DISTINCT c.film_id, c.credit_holder_id, c.role_id
    FROM fnl.fnl_film_credits AS c
    JOIN selected_films AS f USING (film_id)
), people AS (
    SELECT DISTINCT h.*
    FROM fnl.fnl_credit_holders AS h
    JOIN credits AS c USING (credit_holder_id)
), named_holders AS (
    SELECT h.*, COALESCE(NULLIF(TRIM(CONCAT_WS(' ', first_name, last_name)), ''),
                         NULLIF(legal_name, ''), credit_holder_id::text) AS holder_name
    FROM fnl.fnl_credit_holders AS h
)
