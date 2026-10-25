{#- Validity against a fixed domain. Nulls are completeness's job, so ignored here. -#}
{% test dq_accepted_values(model, column_name, values, quote=true) %}
select *
from {{ model }}
where {{ column_name }} is not null
  and {{ column_name }} not in (
      {%- for v in values %}{% if quote %}'{{ v }}'{% else %}{{ v }}{% endif %}{% if not loop.last %}, {% endif %}{% endfor -%}
  )
{% endtest %}
