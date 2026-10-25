{#- Validity: 10-digit NUBAN with a correct CBN check digit. Nulls ignored. -#}
{% test dq_valid_nuban(model, column_name, bank_code) %}
select *
from {{ model }}
where {{ column_name }} is not null
  and not ({{ is_valid_nuban(column_name, bank_code) }})
{% endtest %}
