select
    nullif(trim(terminal_id), '')               as terminal_id,
    nullif(trim(agent_id), '')                  as agent_id,
    nullif(trim(agent_name), '')                as agent_name,
    nullif(trim(account_id), '')                as account_id,
    upper(nullif(trim(serial_number), ''))      as serial_number,
    nullif(trim(terminal_model), '')            as terminal_model,
    nullif(trim(state), '')                     as state,
    upper(nullif(trim(status), ''))             as status,
    try_cast(activated_at as timestamp)         as activated_at,
    try_cast(_ingested_at as timestamp)         as ingested_at,
    _row_hash,
    {{ dq_as_of() }}                            as batch_as_of
from {{ ref('brz_terminals') }}
