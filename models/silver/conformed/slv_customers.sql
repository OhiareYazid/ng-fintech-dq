-- One row per customer. Customer records are never dropped (they are regulated
-- KYC records); defects are carried as flags for the owning team to remediate.
with deduped as (
    select *
    from {{ ref('stg_customers') }}
    where customer_id is not null
    qualify row_number() over (partition by customer_id order by ingested_at desc, _row_hash) = 1
),

checked as (
    select
        deduped.* exclude (_row_hash),
        case
            when bvn is null then 'MISSING'
            when not regexp_full_match(bvn, '[0-9]{11}') then 'INVALID_FORMAT'
            when count(*) over (partition by bvn) > 1 then 'SHARED_WITH_ANOTHER_CIF'
            else 'OK'
        end                                                                     as bvn_status,
        coalesce(regexp_full_match(phone_e164, '{{ ng_mobile_e164_pattern() }}'), false) as phone_is_valid,
        state_of_residence in (select state_name from {{ ref('ref_states') }})  as state_is_valid,
        coalesce(date_of_birth between (batch_as_of - interval 110 year)::date
                                   and (batch_as_of - interval 18 year)::date, false) as dob_is_plausible
    from deduped
)

select
    checked.* exclude (batch_as_of),
    concat_ws(',',
        case when kyc_tier >= 2 and bvn is null then 'DQ-CUS-003' end,
        case when bvn_status = 'INVALID_FORMAT' then 'DQ-CUS-004' end,
        case when bvn_status = 'SHARED_WITH_ANOTHER_CIF' then 'DQ-CUS-005' end,
        case when not phone_is_valid then 'DQ-CUS-006' end,
        case when not state_is_valid then 'DQ-CUS-008' end,
        case when not dob_is_plausible then 'DQ-CUS-009' end
    )                                                                           as dq_flags
from checked
