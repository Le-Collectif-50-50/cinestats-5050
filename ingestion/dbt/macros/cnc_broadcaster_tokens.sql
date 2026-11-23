{% macro cnc_broadcaster_tokens(value) %}
-- Les expressions de noms composés précèdent le repli sur un mot inconnu.
SELECT
    pieces.token,
    COALESCE(mapping.broadcaster_name, pieces.token) AS broadcaster_name,
    mapping.priority IS NOT NULL AS is_recognized,
    COALESCE(mapping.is_excluded, FALSE) AS is_excluded
FROM (
    SELECT matched[1] AS token
    FROM (
        SELECT STRING_AGG('(?:' || alias_pattern || ')', '|' ORDER BY priority) AS pattern
        FROM {{ ref('cnc_broadcaster_aliases') }}
    ) AS patterns
    CROSS JOIN LATERAL REGEXP_MATCHES(
        TRANSLATE(COALESCE({{ value }}, ''), CHR(160) || CHR(8239), '  '),
        '((?:' || patterns.pattern || ')(?![[:alnum:]+])|[^[:space:],;/]+)',
        'gi'
    ) AS matched
) AS pieces
LEFT JOIN {{ ref('cnc_broadcaster_aliases') }} AS mapping
    ON pieces.token ~* ('^(?:' || mapping.alias_pattern || ')$')
{% endmacro %}
