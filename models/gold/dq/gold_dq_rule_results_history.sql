with results as (
    select
        *,
        case when rows_checked = 0 then 1.0
             else 1 - rows_failed::double / rows_checked end as pass_rate
    from {{ source('dq_audit', 'rule_results') }}
)

select
    results.*,
    {{ dq_severity_weight('severity') }}                    as severity_weight,
    case
        when rows_failed = 0 then 'PASS'
        when pass_rate >= threshold then 'TOLERATED'
        else 'BREACH'
    end                                                     as rule_status
from results
