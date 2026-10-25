-- POS agent league table. Terminals missing from the registry are kept (their
-- cash-outs are real) and labelled, rather than dropped by an inner join.
select
    txn.terminal_id,
    coalesce(terminals.agent_id, 'UNREGISTERED')                    as agent_id,
    terminals.agent_name,
    terminals.state,
    terminals.terminal_model,
    coalesce(txn.terminal_registered, false)                        as terminal_registered,
    count(*)                                                        as txn_count,
    round(count(*) filter (where txn.status = 'SUCCESSFUL') / count(*), 4) as success_rate,
    coalesce(sum(txn.amount) filter (where txn.status = 'SUCCESSFUL'), 0) as successful_value_ngn,
    coalesce(sum(txn.fee) filter (where txn.status = 'SUCCESSFUL'), 0)    as fee_income_ngn,
    count(distinct cast(txn.created_at as date))                    as active_days,
    max(txn.created_at)                                             as last_txn_at
from {{ ref('slv_transactions') }} as txn
left join {{ ref('slv_terminals') }} as terminals on terminals.terminal_id = txn.terminal_id
where txn.channel = 'POS'
  and txn.terminal_id is not null
group by all
