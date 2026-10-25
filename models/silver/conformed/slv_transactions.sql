-- Clean, deduplicated transactions: the only transaction source gold may use.
select
    transaction_id,
    session_id,
    account_id,
    terminal_id,
    channel,
    direction,
    amount,
    fee,
    currency,
    status,
    counterparty_bank_code,
    counterparty_account,
    narration,
    created_at,
    settled_at,
    source_system,
    kyc_tier,
    terminal_registered,
    dq_flags,
    ingested_at
from {{ ref('int_transactions_screened') }}
where quarantine_reasons = ''
