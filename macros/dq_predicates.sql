{#-
    Reusable predicates. Used by both the DQ rules (tests/generic) and the silver
    quarantine logic so a rule means the same thing wherever it is enforced.
-#}

{#- Batch timestamp from the control file. Rules compare against this, not now(),
    so re-running dbt on the same extract gives the same answer. -#}
{% macro dq_as_of() -%}
    (select max(try_cast(extracted_at as timestamp)) from {{ ref('brz_batch_control') }})
{%- endmacro %}


{#- Nigerian mobile number in E.164: +234 then 7/8/9, then 0/1, then 8 digits. -#}
{% macro ng_mobile_e164_pattern() -%}
    ^\+234[789][01][0-9]{8}$
{%- endmacro %}


{#- 08031234567 / 2348031234567 / +234 803 123 4567  ->  +2348031234567.
    Anything that cannot be mapped is returned digits-only so validity rules see it. -#}
{% macro standardize_ng_phone(column) -%}
    case
        when regexp_full_match(regexp_replace({{ column }}, '[^0-9]', '', 'g'), '0[0-9]{10}')
            then '+234' || substr(regexp_replace({{ column }}, '[^0-9]', '', 'g'), 2)
        when regexp_full_match(regexp_replace({{ column }}, '[^0-9]', '', 'g'), '234[0-9]{10}')
            then '+' || regexp_replace({{ column }}, '[^0-9]', '', 'g')
        else nullif(regexp_replace({{ column }}, '[^0-9+]', '', 'g'), '')
    end
{%- endmacro %}


{#- Processor status vocabularies mapped to the canonical set. Unknown values pass
    through unchanged so the validity rule can catch them. -#}
{% macro standardize_txn_status(column) -%}
    case upper(trim({{ column }}))
        when 'SUCCESS' then 'SUCCESSFUL'
        when 'SUCCESSFUL' then 'SUCCESSFUL'
        when 'APPROVED' then 'SUCCESSFUL'
        when 'FAIL' then 'FAILED'
        when 'FAILED' then 'FAILED'
        when 'DECLINED' then 'FAILED'
        else nullif(upper(trim({{ column }})), '')
    end
{%- endmacro %}


{#- CBN NUBAN check: 10 digits where digit 10 is the check digit computed over the
    3-digit bank code + 9-digit serial with weights 3,7,3,3,7,3,3,7,3,3,7,3. -#}
{% macro is_valid_nuban(column, bank_code) -%}
    {%- set weights = [3, 7, 3, 3, 7, 3, 3, 7, 3, 3, 7, 3] -%}
    case
        when regexp_full_match({{ column }}, '[0-9]{10}') then
            try_cast(substr({{ column }}, 10, 1) as integer) = (10 - ((
                {%- for w in weights %}
                try_cast(substr('{{ bank_code }}' || substr({{ column }}, 1, 9), {{ loop.index }}, 1) as integer) * {{ w }}
                {%- if not loop.last %} +{% endif %}
                {%- endfor %}
            ) % 10)) % 10
        else false
    end
{%- endmacro %}


{#- Event timestamps must fall between the platform launch and the batch cut-off
    (plus a few minutes of clock tolerance). -#}
{% macro is_plausible_event_ts(column, as_of_column) -%}
    ({{ column }} >= timestamp '2020-01-01' and {{ column }} <= {{ as_of_column }} + interval 10 minute)
{%- endmacro %}
