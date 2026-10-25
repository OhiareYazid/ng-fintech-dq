with latest_run as (
    select run_id
    from {{ source('dq_audit', 'rule_results') }}
    order by published_at desc
    limit 1
)

select history.*
from {{ ref('gold_dq_rule_results_history') }} as history
join latest_run using (run_id)
