{#- Completeness. Returns every row where the column is missing.
    Scope conditional rules ("BVN required for tier 2+") with config.where. -#}
{% test dq_not_null(model, column_name) %}
select *
from {{ model }}
where {{ column_name }} is null
{% endtest %}
