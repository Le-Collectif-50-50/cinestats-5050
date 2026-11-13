WITH named_holders AS (
    SELECT h.*, COALESCE(NULLIF(TRIM(CONCAT_WS(' ', first_name, last_name)), ''),
                         NULLIF(legal_name, ''), credit_holder_id::text) AS holder_name
    FROM fnl.fnl_credit_holders AS h
), selected_holders AS (
    SELECT h.*
    FROM named_holders AS h
    WHERE (FALSE
        [[OR NULLIF(TRIM({{identifiant}}), '') IS NOT NULL]]
        [[OR NULLIF(TRIM({{nom}}), '') IS NOT NULL]])
      [[AND LOWER(h.credit_holder_id::text) = LOWER(TRIM({{identifiant}}))]]
      [[AND STRPOS(LOWER(CONCAT_WS(' ', h.first_name, h.last_name, h.legal_name)),
                   LOWER(TRIM({{nom}}))) > 0]]
), credits AS (
    SELECT DISTINCT c.film_id, c.credit_holder_id, c.role_id
    FROM fnl.fnl_film_credits AS c
    JOIN selected_holders AS h USING (credit_holder_id)
), films AS (
    SELECT DISTINCT f.* FROM fnl.fnl_films AS f JOIN credits AS c USING (film_id)
)
