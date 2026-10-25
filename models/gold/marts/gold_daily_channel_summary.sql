-- Daily volume, value, success rate and fee income by channel, from clean silver only.
select
    cast(created_at as date)                                        as txn_date,
    channel,
    count(*)                                                        as txn_count,
    count(*) filter (where status = 'SUCCESSFUL')                   as successful_count,
    round(count(*) filter (where status = 'SUCCESSFUL') / count(*), 4) as success_rate,
    coalesce(sum(amount) filter (where status = 'SUCCESSFUL'), 0)   as successful_value_ngn,
    coalesce(sum(fee) filter (where status = 'SUCCESSFUL'), 0)      as fee_income_ngn,
    count(*) filter (where dq_flags <> '')                          as flagged_txn_count
from {{ ref('slv_transactions') }}
group by all
