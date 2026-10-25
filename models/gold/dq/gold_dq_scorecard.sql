-- Score = severity-weighted mean of rule pass rates. Only scored rules count;
-- source-conformity monitors (scored = false) are reported separately.
with rules as (
    select * from {{ ref('gold_dq_rule_results') }} where scored
),

rolled_up as (
    select
        coalesce(dataset, 'ALL')                                        as dataset,
        coalesce(dimension, 'ALL')                                      as dimension,
        count(*)                                                        as rules,
        count(*) filter (where rule_status = 'PASS')                    as rules_passed,
        count(*) filter (where rule_status = 'TOLERATED')               as rules_tolerated,
        count(*) filter (where rule_status = 'BREACH')                  as rules_breached,
        count(*) filter (where rule_status = 'BREACH' and severity = 'critical') as critical_breaches,
        count(*) filter (where rule_status = 'BREACH' and severity in ('high', 'medium')) as high_medium_breaches,
        sum(rows_failed)                                                as rows_failed,
        round(sum(pass_rate * severity_weight) / sum(severity_weight), 4) as dq_score,
        any_value(run_id)                                               as run_id,
        any_value(batch_as_of)                                          as batch_as_of
    from rules
    group by cube (dataset, dimension)
)

select
    *,
    {{ dq_rag('dq_score', 'critical_breaches', 'high_medium_breaches') }} as rag
from rolled_up
