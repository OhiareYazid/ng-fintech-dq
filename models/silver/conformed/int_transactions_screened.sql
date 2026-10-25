-- Dedupe, then apply the silver action policy for each rule:
--   quarantine_reasons -> row is withheld from slv_transactions (it would misstate money)
--   dq_flags           -> row passes through, flagged for the owning team
with latest_version as (
    -- Exact re-deliveries and CDC status updates share a transaction_id: keep the latest.
    select *
    from {{ ref('int_transactions_enriched') }}
    qualify row_number() over (partition by transaction_id order by ingested_at desc, _row_hash) = 1
),

legs as (
    -- A second transaction on the same NIP session is a double posting, not a dedupe case:
    -- the first leg stays, the second is held for reconciliation.
    select
        *,
        case when channel = 'TRANSFER' and session_id is not null
             then row_number() over (partition by session_id order by created_at, transaction_id)
        end as session_leg
    from latest_version
)

select
    legs.*,
    concat_ws(',',
        case when amount is null then 'DQ-TXN-003' end,
        case when amount <= 0 then 'DQ-TXN-004' end,
        case when status is null
              or status not in ('SUCCESSFUL', 'FAILED', 'PENDING', 'REVERSED') then 'DQ-TXN-005' end,
        case when channel is null
              or channel not in ('POS', 'TRANSFER', 'USSD', 'CARD', 'BILLS') then 'DQ-TXN-007' end,
        case when not account_found then 'DQ-TXN-008' end,
        case when not coalesce({{ is_plausible_event_ts('created_at', 'batch_as_of') }}, false) then 'DQ-TXN-011' end,
        case when session_leg > 1 then 'DQ-TXN-012' end,
        case when amount > 0 and fee > amount then 'DQ-TXN-015' end,
        case when amount > single_txn_limit_ngn then 'DQ-TXN-016' end
    ) as quarantine_reasons,
    concat_ws(',',
        case when terminal_registered = false then 'DQ-TXN-009' end,
        case when channel = 'POS' and terminal_id is null then 'DQ-TXN-010' end,
        case when counterparty_bank_known = false then 'DQ-TXN-013' end,
        case when settled_at < created_at then 'DQ-TXN-014' end,
        case when channel = 'TRANSFER' and session_id is null then 'DQ-TXN-020' end,
        case when account_status = 'CLOSED' and direction = 'DR' and status = 'SUCCESSFUL'
              and created_at > account_closed_at then 'DQ-TXN-017' end
    ) as dq_flags
from legs
