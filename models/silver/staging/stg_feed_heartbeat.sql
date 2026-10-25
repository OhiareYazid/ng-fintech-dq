-- Timeliness per feed. Transactions are also measured per channel, because a
-- table-level max(ingested_at) stays fresh while one upstream feed is dead.
-- Driven from the SLA seed so a feed that sent nothing at all still shows up.
with loads as (
    select 'customers' as dataset, 'ALL' as partition_key, max(ingested_at) as last_loaded_at
    from {{ ref('stg_customers') }}
    union all
    select 'accounts', 'ALL', max(ingested_at) from {{ ref('stg_accounts') }}
    union all
    select 'terminals', 'ALL', max(ingested_at) from {{ ref('stg_terminals') }}
    union all
    select 'transactions', 'ALL', max(ingested_at) from {{ ref('stg_transactions') }}
    union all
    select 'transactions', channel, max(ingested_at)
    from {{ ref('stg_transactions') }}
    group by channel
),
as_of as (
    select {{ dq_as_of() }} as batch_as_of
)
select
    sla.dataset,
    sla.partition_key,
    sla.source_system,
    sla.data_owner,
    loads.last_loaded_at,
    as_of.batch_as_of,
    round(date_diff('second', loads.last_loaded_at, as_of.batch_as_of) / 3600.0, 2) as hours_since_last_load,
    sla.sla_hours
from {{ ref('ref_feed_sla') }} as sla
cross join as_of
left join loads
    on loads.dataset = sla.dataset
   and loads.partition_key = sla.partition_key
