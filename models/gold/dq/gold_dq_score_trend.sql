with per_run as (
    select
        run_id,
        max(published_at)                                               as published_at,
        max(batch_as_of)                                                as batch_as_of,
        count(*)                                                        as rules,
        count(*) filter (where rule_status = 'BREACH')                  as rules_breached,
        count(*) filter (where rule_status = 'BREACH' and severity = 'critical') as critical_breaches,
        count(*) filter (where rule_status = 'BREACH' and severity in ('high', 'medium')) as high_medium_breaches,
        round(sum(pass_rate * severity_weight) / sum(severity_weight), 4) as dq_score
    from {{ ref('gold_dq_rule_results_history') }}
    where scored
    group by run_id
)

select
    *,
    {{ dq_rag('dq_score', 'critical_breaches', 'high_medium_breaches') }} as rag
from per_run
order by published_at
