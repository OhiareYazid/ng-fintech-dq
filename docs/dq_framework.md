# DQ framework

How rules are defined, enforced, scored and turned into owned issues. The
[rule library](rule_library.md) is the catalogue, the [scorecard](../reports/dq_scorecard.md)
is the measurement and the [issue log](../reports/issue_log.md) is the follow-up.

## Principles

1. **Measure at the edge, enforce at the contract.** Rules assess the data as
   received and never stop the pipeline. Silver acts on what they find (dedupe,
   quarantine or flag) and a small set of contract tests on silver *does* stop
   the build, because gold must never be refreshed from data that breaks them.
2. **Never drop silently.** A blocked row goes to a quarantine table with the
   rule IDs that blocked it. A KYC or account record is never dropped at all: it
   carries flags, because it is a regulated record that someone must fix.
3. **A rule is code with an owner.** Every rule is a dbt test whose `config.meta`
   holds its ID, dimension, severity, action, threshold, owner and rationale. The
   catalogue is generated from the code, so it cannot drift.
4. **Averages hide expensive defects.** 25 double debits are 0.04% of
   transactions and a P1 incident. Scores are severity-weighted, and any critical
   breach turns the cell red whatever the average says.
5. **Not every failing row is a defect.** Formats silver can standardise,
   tolerated gaps and expected behaviour (change-data-capture updates) are
   measured separately so they don't create noise in the issue log.

## Where DQ happens in the medallion layout

| Layer | Models | What it holds | DQ role |
|---|---|---|---|
| Bronze | `brz_*` | The extract exactly as received: every column as text, plus row hash, source file and load time | Source-conformity monitors (not scored). Nothing can fail ingestion. |
| Silver staging | `stg_*` | Typed and standardised (phone to E.164, state aliases, status vocabulary). **Every row kept**, duplicates included | **Assessment point.** All scored rules run here, so results describe the feed, not our cleaning. Plus feed-level models: `stg_feed_heartbeat` (freshness) and `stg_batch_reconciliation` (control totals). |
| Silver conformed | `slv_*`, `int_*` | One row per business key, with rule actions applied | **Enforcement point.** Dedupe, quarantine to `slv_transactions_quarantine`, or carry `dq_flags`. Contract tests (severity `error`) guard the output. |
| Gold | `gold_*` | Business marts from clean silver only; DQ scorecard models from `dq_audit` | Reporting. Marts never read staging or quarantine. |

## Dimensions

| Dimension | Question it answers | Example rules |
|---|---|---|
| Completeness | Is the value, row or file there when it must be? | BVN present for tier 2/3 (conditional), amount present, file row count matches control total |
| Validity | Does the value conform to its format or domain? | BVN 11 digits, valid NUBAN check digit, state is one of 36 + FCT, plausible timestamp |
| Uniqueness | Is each real-world thing recorded once? | transaction ID, one NIP session per posting, one BVN per CIF, one device per terminal ID |
| Referential integrity | Does every reference resolve? | transaction account exists, POS terminal in registry, counterparty bank code is a CBN code |
| Consistency | Do related fields and tables agree? | settled after created, fee not above amount, amount within KYC tier limit, no debits after closure |
| Freshness | Did the data arrive within its SLA? | each feed within SLA, **each transaction channel** within SLA |

Accuracy (agreement with the real world) needs an external source of truth such
as a NIBSS settlement report; see [what's next](../README.md#what-id-build-next).

## Rule anatomy

```yaml
- dq_unique:                                   # generic test from tests/generic/
    name: dq_txn_012_session_id_unique_for_transfers
    config:
      where: "channel = 'TRANSFER'"            # scope; also scopes the denominator
      meta:
        rule_id: DQ-TXN-012                    # stable ID used everywhere
        rule_name: One NIP session, one transaction
        dimension: uniqueness
        dataset: transactions                  # the logical table it scores against
        severity: critical                     # critical | high | medium | low
        action: QUARANTINE                     # QUARANTINE | FLAG | DEDUPE | MONITOR
        threshold: 1.0                         # optional, default 1.0 (zero tolerance)
        scored: true                           # optional, false for conformity monitors
        owner: Settlement & Reconciliation     # accountable team
        key: transaction_id                    # optional, column for sample keys
        why: Two ledger postings for one NIP session is a double debit.
```

The generic tests (`dq_not_null`, `dq_unique`, `dq_accepted_values`,
`dq_matches_regex`, `dq_relationships`, `dq_expression_is_true`,
`dq_valid_nuban`) all return **every failing row**, unlike dbt's built-in
`unique` and `accepted_values` which return one row per bad value. That keeps
failing-row counts comparable across rules and puts both sides of a duplicate
into the stored failures used as evidence.

Predicates that silver also enforces (NUBAN check digit, phone standardisation,
plausible timestamps) live in `macros/dq_predicates.sql`, so the rule and the
quarantine logic cannot disagree.

## Severity

| Severity | Use when the defect... | Weight |
|---|---|---|
| critical | moves or misstates money, or breaks a regulatory obligation, now | 4 |
| high | misstates reporting or breaks a control | 3 |
| medium | degrades analysis or operations, with a workaround | 2 |
| low | is cosmetic, or is tolerated by design | 1 |

## Actions

| Action | Silver does | Use when |
|---|---|---|
| QUARANTINE | Withholds the row from `slv_transactions`, writes it to the quarantine table with reason codes | Letting it through would misstate money: no amount, unknown account, double posting, kobo amounts |
| FLAG | Passes the row through with the rule ID in `dq_flags` | The event is real and must be counted, but someone must fix an attribute: unregistered terminal, unknown bank code, debit after closure. Also every KYC/account defect |
| DEDUPE | Keeps the latest version per business key | Re-deliveries and CDC updates of the same record |
| MONITOR | Nothing; measured only | Feed-level checks (freshness, control totals) that are fixed upstream, tolerated gaps and source-conformity monitors |

Choosing between QUARANTINE and FLAG is the main judgement call. The test is:
*would gold be more wrong with this row in, or with it out?* Unregistered-terminal
cash-outs are real money, so they are flagged; leaving them out would understate
agent volume. Kobo amounts are 100x wrong, so they are quarantined.

## Scoring

- **Rule pass rate** = 1 - failing rows / rows in scope. Rows in scope honour the
  rule's `where`, and validity-style rules exclude nulls (completeness rules own
  nulls).
- **Rule status**: `PASS` (no failures), `TOLERATED` (failures but pass rate at
  or above `threshold`), `BREACH`.
- **Score** for any group of rules (a table, a dimension, a table × dimension
  cell, overall) = severity-weighted mean of the rule pass rates. Only scored
  rules count.
- **RAG**:
  - RED: any critical rule breached, or score < 95%
  - AMBER: any high or medium rule breached, or score < 99%
  - GREEN: otherwise (a low-severity breach alone does not change the colour)
- **Feed-level rules** check one row per feed or channel, so a stale feed scores
  0% on its rule. That is deliberate: a missing feed should never be averaged
  away by 60,000 healthy rows.

The policy lives in `macros/dq_scoring.sql` and is used by every scorecard model.

## Issue management

Every breached rule maps to an issue. Detection fields are written by the
pipeline; triage fields come from [`dq/issue_triage.yml`](../dq/issue_triage.yml).
A breach with no triage entry appears as **NEW**. An issue whose rules all pass
is marked **READY_TO_CLOSE** for the owner to confirm.

| Priority | Meaning | Target to fix |
|---|---|---|
| P1 | Money or regulatory exposure now | 1 business day; owner and DQ lead paged |
| P2 | Misstated reporting or a broken control | Current sprint |
| P3 | Degraded data with a workaround | Backlog, with a date |
| P4 | Cosmetic or tolerated | Monitor |

Lifecycle: `NEW → OPEN → IN_REMEDIATION → MONITORING → RESOLVED`, or
`RISK_ACCEPTED` with a named approver. An issue moves to RESOLVED only after its
rules pass for three consecutive batches, so a one-off clean batch does not
close a recurring problem.

Every triage entry answers four questions: **root cause** (not the symptom; the
stale terminal registry, not the 45 orphan transactions), **impact** (in naira,
customers or regulatory terms), **remediation** (fix the data) and
**prevention** (fix the process so it doesn't happen again).

| Role | Responsibility |
|---|---|
| Data owner (business team in `owner`) | Accountable for the data and for fixing it at source |
| Data steward / DQ analyst | Defines rules and thresholds, triages, tracks issues to closure, reports the scorecard |
| Data engineering | Implements rules and silver actions, keeps the pipeline idempotent |
| Data governance | Approves risk acceptance, owns standards and data contracts |

## Adding a rule

1. Pick the dimension, severity and action using the tables above. Write the `why`
   in business terms before writing SQL.
2. Add the test to the dataset's file in `models/dq_rules/` with a new `rule_id`.
3. If silver must act on it, add the rule ID to `quarantine_reasons` or
   `dq_flags` in the relevant silver model, reusing a macro from
   `macros/dq_predicates.sql` where one exists.
4. Run `python run_pipeline.py`. The rule library, scorecard and issue log update
   themselves; add a triage entry if it breaches.

## Known limitations

- Batch, not streaming: rules run per extract. Intraday alerting would move the
  freshness and uniqueness rules onto the stream.
- Results history is append-only in DuckDB. In production it would live in the
  warehouse with a retention policy and feed an alerting tool.
- KYC tier limits in `seeds/ref_kyc_tiers.csv` are illustrative, modelled on the
  CBN three-tier framework; real limits come from current CBN circulars and
  internal policy.
