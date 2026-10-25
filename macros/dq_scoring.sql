{#- Scoring policy, kept in one place so every scorecard model agrees. See docs/dq_framework.md. -#}

{% macro dq_severity_weight(severity_column) -%}
    case {{ severity_column }}
        when 'critical' then 4
        when 'high' then 3
        when 'medium' then 2
        else 1
    end
{%- endmacro %}


{#- RED: a critical rule breached, or score below 95%.
    AMBER: any high/medium rule breached, or score below 99%.
    GREEN: otherwise (low-severity breaches alone do not change the colour).
    Averages hide small, expensive defects, so a single critical breach turns
    the cell red however good the weighted score looks. -#}
{% macro dq_rag(score, critical_breaches, high_medium_breaches) -%}
    case
        when {{ critical_breaches }} > 0 or {{ score }} < 0.95 then 'RED'
        when {{ high_medium_breaches }} > 0 or {{ score }} < 0.99 then 'AMBER'
        else 'GREEN'
    end
{%- endmacro %}
