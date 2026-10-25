{#- Referential integrity: the key must exist in the parent. Null keys ignored. -#}
{% test dq_relationships(model, column_name, to, field) %}
with child as (
    select * from {{ model }}
)
select child.*
from child
where child.{{ column_name }} is not null
  and not exists (
      select 1 from {{ to }} as parent
      where parent.{{ field }} = child.{{ column_name }}
  )
{% endtest %}
