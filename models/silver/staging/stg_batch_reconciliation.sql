-- Volume completeness: rows received per file vs the count declared in the control file.
with received as (
    select 'customers' as dataset, count(*) as received_count from {{ ref('brz_customers') }}
    union all
    select 'accounts', count(*) from {{ ref('brz_accounts') }}
    union all
    select 'terminals', count(*) from {{ ref('brz_terminals') }}
    union all
    select 'transactions', count(*) from {{ ref('brz_transactions') }}
)
select
    ctl.dataset,
    ctl.file_name,
    try_cast(ctl.record_count as bigint)                            as expected_count,
    coalesce(received.received_count, 0)                            as received_count,
    coalesce(received.received_count, 0) - try_cast(ctl.record_count as bigint) as variance,
    try_cast(ctl.extracted_at as timestamp)                         as extracted_at
from {{ ref('brz_batch_control') }} as ctl
left join received on received.dataset = ctl.dataset
