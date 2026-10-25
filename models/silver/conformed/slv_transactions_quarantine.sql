-- Transactions withheld from silver, with the rule(s) that blocked them. Worked
-- by the owning team and replayed once fixed; never silently dropped.
select
    transaction_id,
    session_id,
    account_id,
    terminal_id,
    channel,
    direction,
    amount,
    fee,
    status,
    status_raw,
    created_at,
    settled_at,
    source_system,
    kyc_tier,
    single_txn_limit_ngn,
    quarantine_reasons,
    dq_flags,
    ingested_at,
    batch_as_of                     as quarantined_for_batch
from {{ ref('int_transactions_screened') }}
where quarantine_reasons <> ''
