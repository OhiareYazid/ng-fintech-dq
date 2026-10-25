select
    nullif(trim(account_id), '')                as account_id,
    nullif(trim(customer_id), '')               as customer_id,
    nullif(trim(account_number), '')            as account_number,
    upper(nullif(trim(account_type), ''))       as account_type,
    upper(nullif(trim(currency), ''))           as currency,
    upper(nullif(trim(status), ''))             as status,
    try_cast(opened_at as timestamp)            as opened_at,
    try_cast(closed_at as timestamp)            as closed_at,
    try_cast(_ingested_at as timestamp)         as ingested_at,
    _row_hash,
    {{ dq_as_of() }}                            as batch_as_of
from {{ ref('brz_accounts') }}
