-- Un token ne doit jamais correspondre à deux règles du mapping.
SELECT b.broadcaster_type, b.source_value, b.token, COUNT(*) AS matches
FROM {{ ref('int_cnc_broadcasters') }} AS b
JOIN {{ ref('cnc_broadcaster_aliases') }} AS mapping
    ON b.token ~* ('^(?:' || mapping.alias_pattern || ')$')
GROUP BY b.broadcaster_type, b.source_value, b.token
HAVING COUNT(*) > 1
