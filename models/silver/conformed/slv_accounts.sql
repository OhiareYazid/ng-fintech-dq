-- One row per account. Re-delivered CDC rows are collapsed; defects are flagged,
-- not dropped, because an account holding money cannot disappear from reporting.
with deduped as (
    select *
    from {{ ref('stg_accounts') }}
    where account_id is not null
    qualify row_number() over (partition by account_id order by ingested_at desc, _row_hash) = 1
),

customers as (
    select distinct customer_id from {{ ref('stg_customers') }}
),

checked as (
    select
        deduped.* exclude (_row_hash, batch_as_of),
        {{ is_valid_nuban('deduped.account_number', var('home_bank_code')) }}  as nuban_is_valid,
        customers.customer_id is not null                                       as customer_found
    from deduped
    left join customers on customers.customer_id = deduped.customer_id
)

select
    *,
    concat_ws(',',
        case when not customer_found then 'DQ-ACC-002' end,
        case when not nuban_is_valid then 'DQ-ACC-003' end,
        case when status = 'CLOSED' and closed_at is null then 'DQ-ACC-004' end
    ) as dq_flags
from checked
