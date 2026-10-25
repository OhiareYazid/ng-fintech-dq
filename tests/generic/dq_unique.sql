{#- Uniqueness. Unlike dbt's built-in unique test this returns every row that
    shares a key (not one row per key), so failing-row counts are comparable
    with the other rules and the stored failures show both sides of a duplicate. -#}
{% test dq_unique(model, column_name) %}
with scoped as (
    select * from {{ model }} where {{ column_name }} is not null
),
duplicated_keys as (
    select {{ column_name }} as dup_key
    from scoped
    group by 1
    having count(*) > 1
)
select scoped.*
from scoped
join duplicated_keys on scoped.{{ column_name }} = duplicated_keys.dup_key
{% endtest %}
