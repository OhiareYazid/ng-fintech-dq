{#- Row-level business rule. A row fails when the expression is false; when it
    evaluates to null (an input is missing) the row is left to the completeness rules. -#}
{% test dq_expression_is_true(model, expression) %}
select *
from {{ model }}
where not ({{ expression }})
{% endtest %}
