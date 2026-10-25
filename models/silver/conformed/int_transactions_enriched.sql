-- Every staged transaction (duplicates included) with the account, KYC tier,
-- terminal and bank context that the cross-table consistency rules need.
select
    txn.*,
    accounts.account_id is not null                 as account_found,
    accounts.status                                 as account_status,
    accounts.closed_at                              as account_closed_at,
    customers.kyc_tier,
    tiers.single_txn_limit_ngn,
    case when txn.terminal_id is not null
         then terminals.terminal_id is not null end as terminal_registered,
    case when txn.channel = 'TRANSFER'
         then banks.bank_code is not null end       as counterparty_bank_known
from {{ ref('stg_transactions') }} as txn
left join {{ ref('slv_accounts') }} as accounts on accounts.account_id = txn.account_id
left join {{ ref('slv_customers') }} as customers on customers.customer_id = accounts.customer_id
left join {{ ref('ref_kyc_tiers') }} as tiers on tiers.kyc_tier = customers.kyc_tier
left join {{ ref('slv_terminals') }} as terminals on terminals.terminal_id = txn.terminal_id
left join {{ ref('ref_banks') }} as banks on banks.bank_code = txn.counterparty_bank_code
