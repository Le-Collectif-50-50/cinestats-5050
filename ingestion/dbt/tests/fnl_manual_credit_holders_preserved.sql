SELECT fix.id
FROM {{ ref('int_fix_credit_holders') }} AS fix
LEFT JOIN {{ ref('fnl_credit_holders') }} AS final ON final.credit_holder_id = fix.id
WHERE final.credit_holder_id IS NULL
{% for field in ['type', 'first_name', 'last_name', 'legal_name', 'gender', 'birthdate'] %}
    OR (fix.{{ field }} IS NOT NULL AND fix.{{ field }} IS DISTINCT FROM final.{{ field }})
{% endfor %}
