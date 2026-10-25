-- One row per terminal; shared serials and unknown settlement accounts are flagged.
with deduped as (
    select *
    from {{ ref('stg_terminals') }}
    where terminal_id is not null
    qualify row_number() over (partition by terminal_id order by ingested_at desc, _row_hash) = 1
),

checked as (
    select
        deduped.* exclude (_row_hash, batch_as_of),
        count(*) over (partition by serial_number) > 1      as serial_is_shared,
        accounts.account_id is not null                     as settlement_account_found
    from deduped
    left join {{ ref('slv_accounts') }} as accounts on accounts.account_id = deduped.account_id
)

select
    *,
    concat_ws(',',
        case when serial_is_shared then 'DQ-TRM-002' end,
        case when not settlement_account_found then 'DQ-TRM-003' end
    ) as dq_flags
from checked
