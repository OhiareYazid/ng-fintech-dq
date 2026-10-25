select
    dataset,
    file_name,
    record_count,
    extracted_at,
    'batch_control.csv'  as _source_file,
    now()::timestamp     as _bronze_loaded_at
from {{ source('raw', 'batch_control') }}
