{#- Validity against a format. Nulls ignored. -#}
{% test dq_matches_regex(model, column_name, pattern) %}
select *
from {{ model }}
where {{ column_name }} is not null
  and not regexp_full_match(cast({{ column_name }} as varchar), '{{ pattern }}')
{% endtest %}
