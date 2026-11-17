{% macro gsheet_updated_timestamp(expression) -%}
    {%- set value = "NULLIF(TRIM(CAST(" ~ expression ~ " AS TEXT)), '')" -%}
    {%- set time_suffix = "( [0-9]{2}:[0-9]{2}(:[0-9]{2})?)?$" -%}
    CASE
        WHEN {{ value }} IS NULL THEN NULL::TIMESTAMP
        WHEN {{ value }} ~ '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}{{ time_suffix }}' THEN
            -- Réordonner la date avant conversion pour ignorer DateStyle et TimeZone.
            CAST(REGEXP_REPLACE(
                {{ value }},
                '^([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})(.*)$',
                '\3-\2-\1\4'
            ) AS TIMESTAMP)
        WHEN {{ value }} ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}{{ time_suffix }}' THEN
            CAST({{ value }} AS TIMESTAMP)
        -- Ne pas tronquer silencieusement une heure ou accepter une date ambiguë.
        ELSE CAST('Invalid UPDATED_DATE: ' || {{ value }} AS TIMESTAMP)
    END
{%- endmacro %}
