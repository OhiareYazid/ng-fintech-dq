-- Typed and standardised, every row kept. DQ rules assess this model.
select
    nullif(trim(src.customer_id), '')                       as customer_id,
    nullif(trim(src.first_name), '')                        as first_name,
    nullif(trim(src.last_name), '')                         as last_name,
    src.phone_number                                        as phone_raw,
    {{ standardize_ng_phone('src.phone_number') }}          as phone_e164,
    lower(nullif(trim(src.email), ''))                      as email,
    nullif(trim(src.bvn), '')                               as bvn,
    nullif(trim(src.nin), '')                               as nin,
    try_cast(src.date_of_birth as date)                     as date_of_birth,
    upper(nullif(trim(src.gender), ''))                     as gender,
    src.state_of_residence                                  as state_raw,
    coalesce(alias.state_name, nullif(trim(src.state_of_residence), '')) as state_of_residence,
    try_cast(src.kyc_tier as integer)                       as kyc_tier,
    upper(nullif(trim(src.onboarding_channel), ''))         as onboarding_channel,
    try_cast(src.created_at as timestamp)                   as created_at,
    try_cast(src.updated_at as timestamp)                   as updated_at,
    try_cast(src._ingested_at as timestamp)                 as ingested_at,
    src._row_hash,
    {{ dq_as_of() }}                                        as batch_as_of
from {{ ref('brz_customers') }} as src
left join {{ ref('ref_state_aliases') }} as alias
    on lower(regexp_replace(trim(src.state_of_residence), '\s+', ' ', 'g')) = alias.alias
