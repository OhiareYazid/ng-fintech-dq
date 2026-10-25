{#-
    Bronze = the extract exactly as received: every column kept as text, plus
    lineage columns. Nothing is cast, trimmed or dropped here, so a bad value can
    never fail ingestion and every DQ finding can be traced back to the source row.
-#}
{% macro bronze_select(source_table, payload_columns) %}
select
    {%- for col in payload_columns %}
    {{ col }},
    {%- endfor %}
    _ingested_at,
    md5(concat_ws('|',
        {%- for col in payload_columns %}
        coalesce({{ col }}, '<null>'){% if not loop.last %},{% endif %}
        {%- endfor %}
    ))                               as _row_hash,
    '{{ source_table }}.csv'         as _source_file,
    now()::timestamp                 as _bronze_loaded_at
from {{ source('raw', source_table) }}
{% endmacro %}
