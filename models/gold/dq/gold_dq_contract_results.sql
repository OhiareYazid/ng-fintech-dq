with latest_run as (
    select run_id
    from {{ source('dq_audit', 'contract_results') }}
    order by published_at desc
    limit 1
)

select contracts.*
from {{ source('dq_audit', 'contract_results') }} as contracts
join latest_run using (run_id)
