# DQ scorecard

Batch as of **2026-10-25 14:00 WAT** · run `69f95764` · 47 scored rules (+2 source-conformity monitors) · method: [DQ framework](../docs/dq_framework.md#scoring)

| Overall DQ score | Rules breached | Critical breaches | Open P1 issues | Silver contract |
|---|---|---|---|---|
| **94.0%** 🔴 RED | 31 of 47 | 9 | 5 | ✅ 26 of 26 tests pass |

![DQ score by table and dimension](scorecard_heatmap.svg)

Scores measure the data **as received** (bronze and staging). The Silver contract figure measures what reaches gold after dedupe and quarantine: the raw feeds are red, the reporting layer is clean.

## By dimension

| Dimension | Score | RAG | Rules | Passed | Tolerated | Breached | Critical breaches | Failing rows |
|---|---|---|---|---|---|---|---|---|
| Completeness | 87.8% | 🔴 RED | 12 | 6 | 1 | 5 | 2 | 864 |
| Validity | 99.7% | 🔴 RED | 13 | 4 | 0 | 9 | 2 | 295 |
| Uniqueness | 98.8% | 🔴 RED | 8 | 2 | 0 | 6 | 3 | 1,366 |
| Ref. integrity | 99.5% | 🔴 RED | 5 | 0 | 0 | 5 | 2 | 176 |
| Consistency | 99.9% | 🟠 AMBER | 4 | 0 | 0 | 4 | 0 | 145 |
| Freshness | 77.5% | 🔴 RED | 5 | 3 | 0 | 2 | 0 | 2 |

## By table

| Table | Score | RAG | Rules | Breached | Critical breaches | Failing rows |
|---|---|---|---|---|---|---|
| Customers | 98.8% | 🟠 AMBER | 13 | 7 | 0 | 1,058 |
| Accounts | 99.0% | 🔴 RED | 7 | 4 | 3 | 160 |
| Terminals | 81.3% | 🔴 RED | 6 | 3 | 0 | 23 |
| Transactions | 93.0% | 🔴 RED | 21 | 17 | 6 | 1,607 |

## Table × dimension

| Table | Completeness | Validity | Uniqueness | Ref. integrity | Consistency | Freshness | Overall |
|---|---|---|---|---|---|---|---|
| Customers | 97.8% 🟠 | 99.4% 🟠 | 98.7% 🟠 | · | · | 100.0% 🟢 | 98.8% 🟠 |
| Accounts | 97.4% 🟠 | 99.6% 🔴 | 98.7% 🔴 | 99.6% 🔴 | · | 100.0% 🟢 | 99.0% 🔴 |
| Terminals | 100.0% 🟢 | 100.0% 🟢 | 98.2% 🟠 | 98.5% 🟠 | · | 0.0% 🔴 | 81.3% 🔴 |
| Transactions | 77.7% 🔴 | 99.9% 🔴 | 99.2% 🔴 | 99.8% 🔴 | 99.9% 🟠 | 91.4% 🔴 | 93.0% 🔴 |
| All tables | 87.8% 🔴 | 99.7% 🔴 | 98.8% 🔴 | 99.5% 🔴 | 99.9% 🟠 | 77.5% 🔴 | 94.0% 🔴 |

## Rule breaches

Sorted by severity, then pass rate. Feed-level rules (freshness, control totals) check one row per feed or channel, so a single stale feed scores 0% on its rule: by design, a missing feed is never averaged away.

| Rule | Table | Dimension | Severity | Failing / checked | Pass rate | Action | Value affected | Issue |
|---|---|---|---|---|---|---|---|---|
| **DQ-TXN-022** Transaction file row count matches control total | transactions | Completeness | critical | 1 / 1 | 0.00% | MONITOR | — | [ISS-004](issue_log.md#iss-004) |
| **DQ-ACC-001** Account ID unique | accounts | Uniqueness | critical | 80 / 6,630 | 98.79% | DEDUPE | — | [ISS-023](issue_log.md#iss-023) |
| **DQ-TXN-002** Transaction ID unique | transactions | Uniqueness | critical | 700 / 60,447 | 98.84% | DEDUPE | ₦8,757,199 | [ISS-005](issue_log.md#iss-005) |
| **DQ-ACC-003** Account number is a valid NUBAN (CBN check digit) | accounts | Validity | critical | 40 / 6,630 | 99.40% | FLAG | — | [ISS-024](issue_log.md#iss-024) |
| **DQ-ACC-002** Account owner exists in CIF | accounts | Ref. integrity | critical | 25 / 6,630 | 99.62% | FLAG | — | [ISS-026](issue_log.md#iss-026) |
| **DQ-TXN-012** One NIP session, one transaction | transactions | Uniqueness | critical | 50 / 18,149 | 99.72% | QUARANTINE | ₦992,519 | [ISS-001](issue_log.md#iss-001) |
| **DQ-TXN-008** Transaction account exists | transactions | Ref. integrity | critical | 60 / 60,447 | 99.90% | QUARANTINE | ₦875,263 | [ISS-006](issue_log.md#iss-006) |
| **DQ-TXN-003** Amount present | transactions | Completeness | critical | 40 / 60,447 | 99.93% | QUARANTINE | — | [ISS-008](issue_log.md#iss-008) |
| **DQ-TXN-004** Amount greater than zero | transactions | Validity | critical | 30 / 60,447 | 99.95% | QUARANTINE | ₦266,419 | [ISS-008](issue_log.md#iss-008) |
| **DQ-TRM-005** Terminal registry delivered within 24h | terminals | Freshness | high | 1 / 1 | 0.00% | MONITOR | — | [ISS-007](issue_log.md#iss-007) |
| **DQ-TXN-019** Every transaction channel delivered within its SLA | transactions | Freshness | high | 1 / 5 | 80.00% | MONITOR | — | [ISS-003](issue_log.md#iss-003) |
| **DQ-TRM-002** One device serial, one terminal ID | terminals | Uniqueness | high | 16 / 400 | 96.00% | FLAG | — | [ISS-027](issue_log.md#iss-027) |
| **DQ-CUS-003** BVN present for KYC tier 2 and 3 | customers | Completeness | high | 120 / 3,303 | 96.37% | FLAG | — | [ISS-016](issue_log.md#iss-016) |
| **DQ-CUS-005** One BVN, one customer profile | customers | Uniqueness | high | 120 / 4,079 | 97.06% | FLAG | — | [ISS-018](issue_log.md#iss-018) |
| **DQ-TRM-003** Settlement account exists | terminals | Ref. integrity | high | 6 / 400 | 98.50% | FLAG | — | [ISS-027](issue_log.md#iss-027) |
| **DQ-CUS-004** BVN is 11 digits | customers | Validity | high | 40 / 4,079 | 99.02% | FLAG | — | [ISS-017](issue_log.md#iss-017) |
| **DQ-CUS-009** Customer is 18 to 110 years old | customers | Validity | high | 25 / 5,060 | 99.51% | FLAG | — | [ISS-020](issue_log.md#iss-020) |
| **DQ-TXN-009** POS terminal exists in registry | transactions | Ref. integrity | high | 45 / 27,105 | 99.83% | FLAG | ₦524,500 | [ISS-007](issue_log.md#iss-007) |
| **DQ-TXN-016** Amount within the KYC tier single-transaction limit | transactions | Consistency | high | 80 / 60,447 | 99.87% | QUARANTINE | ₦63,144,702 | [ISS-002](issue_log.md#iss-002) |
| **DQ-TXN-010** POS transaction carries a terminal ID | transactions | Completeness | high | 35 / 27,140 | 99.87% | FLAG | ₦398,900 | [ISS-014](issue_log.md#iss-014) |
| **DQ-TXN-005** Status recognised (after standardisation) | transactions | Validity | high | 40 / 60,447 | 99.93% | QUARANTINE | ₦768,488 | [ISS-009](issue_log.md#iss-009) |
| **DQ-TXN-015** Fee not larger than the amount | transactions | Consistency | high | 20 / 60,377 | 99.97% | QUARANTINE | ₦12,114 | [ISS-011](issue_log.md#iss-011) |
| **DQ-TXN-011** Transaction time between 2020 and the batch cut-off | transactions | Validity | high | 20 / 60,447 | 99.97% | QUARANTINE | ₦319,400 | [ISS-013](issue_log.md#iss-013) |
| **DQ-TXN-017** No successful debits after account closure | transactions | Consistency | high | 15 / 60,447 | 99.98% | FLAG | ₦219,344 | [ISS-012](issue_log.md#iss-012) |
| **DQ-ACC-004** Closure date present on closed accounts | accounts | Completeness | medium | 15 / 235 | 93.62% | FLAG | — | [ISS-025](issue_log.md#iss-025) |
| **DQ-CUS-006** Phone is a valid Nigerian mobile (after standardisation) | customers | Validity | medium | 50 / 5,060 | 99.01% | FLAG | — | [ISS-019](issue_log.md#iss-019) |
| **DQ-TXN-021** No exact duplicate payloads (double ingestion) | transactions | Uniqueness | medium | 400 / 60,447 | 99.34% | DEDUPE | ₦5,041,736 | [ISS-005](issue_log.md#iss-005) |
| **DQ-CUS-008** State of residence is one of the 36 states or FCT | customers | Validity | medium | 30 / 5,060 | 99.41% | FLAG | — | [ISS-021](issue_log.md#iss-021) |
| **DQ-TXN-013** Transfer counterparty bank code is a known CBN code | transactions | Ref. integrity | medium | 40 / 18,149 | 99.78% | FLAG | ₦1,012,596 | [ISS-015](issue_log.md#iss-015) |
| **DQ-TXN-014** Settled at or after creation | transactions | Consistency | medium | 30 / 60,447 | 99.95% | FLAG | ₦525,743 | [ISS-010](issue_log.md#iss-010) |
| **DQ-CUS-011** Email well formed | customers | Validity | low | 20 / 4,407 | 99.55% | FLAG | — | [ISS-022](issue_log.md#iss-022) |

## Within tolerance

| Rule | Failing / checked | Pass rate | Threshold |
|---|---|---|---|
| **DQ-CUS-010** Email present (80% tolerance) | 653 / 5,060 | 87.09% | ≥ 80% |

## Source conformity (monitored, not scored)

How much each source deviates from the target format before silver standardises it. Not a defect in what gold sees; it is the evidence for a data-contract conversation with the source team.

| Rule | Non-conformant / checked | Conformant |
|---|---|---|
| **DQ-CUS-007** Phone captured in E.164 at source | 3,813 / 5,060 | 24.6% |
| **DQ-TXN-006** Status sent in the canonical vocabulary at source | 540 / 60,447 | 99.1% |

## What silver contained (transactions)

| Step | Rows | Detail |
|---|---|---|
| Declared in control file | 60,597 |  |
| Received | 60,447 | 150 missing (DQ-TXN-022) |
| Collapsed as duplicates | 350 | 200 re-deliveries + 150 superseded CDC versions |
| Quarantined | 315 | ₦65,882,646 held back. By rule: DQ-TXN-016 80; DQ-TXN-008 60; DQ-TXN-005 40; DQ-TXN-003 40; DQ-TXN-004 30; DQ-TXN-012 25; DQ-TXN-015 20; DQ-TXN-011 20 |
| Passed with flags | 165 | By rule: DQ-TXN-009 45; DQ-TXN-013 40; DQ-TXN-010 35; DQ-TXN-014 30; DQ-TXN-017 15 |
| Clean rows in silver | 59,782 | ₦850,813,327 successful value |

- **Kobo amounts kept out of reporting.** The quarantined USSD rows would have added ₦55,327,046 of successful value; their real value is about ₦553,270. Clean USSD value for the whole period is ₦36,231,501, so letting them through would have overstated USSD value 2.5x.
- **Double debits held for reversal.** 25 second legs of duplicated NIP sessions (₦496,260) are quarantined and routed to Settlement for refund.

## Detection coverage against planted defects

The synthetic data has 35 planted issues recorded in an answer key the rules never read. **35 of 35 were detected**, 35 with exactly the expected failing-row count. Of the 15 rules with nothing planted against them, 0 fired (false positives).

| Planted | Kind | What was planted | Catching rule | Rows planted | Rule expected | Rule detected | Result |
|---|---|---|---|---|---|---|---|
| PI-01 | defect | Duplicate customer profiles sharing one BVN | DQ-CUS-005 | 120 | 120 | 120 | ✅ exact |
| PI-02 | defect | Tier 2/3 customers with no BVN | DQ-CUS-003 | 120 | 120 | 120 | ✅ exact |
| PI-03 | defect | Malformed BVNs (truncated, Excel scientific notation, letter O) | DQ-CUS-004 | 40 | 40 | 40 | ✅ exact |
| PI-04 | standardisable | Phone numbers not in E.164 at source (fixed by standardisation) | DQ-CUS-007 | 3,813 | 3,813 | 3,813 | ✅ exact |
| PI-05 | defect | Phone numbers that cannot be standardised to +234 mobile | DQ-CUS-006 | 50 | 50 | 50 | ✅ exact |
| PI-06 | defect | State of residence not a Nigerian state (typos, cities, N/A) | DQ-CUS-008 | 30 | 30 | 30 | ✅ exact |
| PI-07 | defect | Implausible date of birth (1900-01-01 placeholder, future, under 18) | DQ-CUS-009 | 25 | 25 | 25 | ✅ exact |
| PI-08 | tolerated | Missing email (inside the 80% completeness tolerance) | DQ-CUS-010 | 653 | 653 | 653 | ✅ exact |
| PI-09 | defect | Malformed email addresses | DQ-CUS-011 | 20 | 20 | 20 | ✅ exact |
| PI-10 | defect | Accounts whose customer does not exist (orphans) | DQ-ACC-002 | 25 | 25 | 25 | ✅ exact |
| PI-11 | defect | Account numbers failing the NUBAN check digit | DQ-ACC-003 | 30 | 40 | 40 | ✅ exact |
| PI-12 | defect | Account numbers with the leading zero stripped (9 digits) | DQ-ACC-003 | 10 | 40 | 40 | ✅ exact |
| PI-13 | defect | Account rows ingested twice | DQ-ACC-001 | 80 | 80 | 80 | ✅ exact |
| PI-14 | defect | Closed accounts with no closure date | DQ-ACC-004 | 15 | 15 | 15 | ✅ exact |
| PI-15 | defect | Same device serial registered to two terminal IDs | DQ-TRM-002 | 16 | 16 | 16 | ✅ exact |
| PI-16 | defect | Terminals settling to an account that does not exist | DQ-TRM-003 | 6 | 6 | 6 | ✅ exact |
| PI-17 | defect | Terminal registry extract is 52 hours old | DQ-TRM-005 | 1 | 1 | 1 | ✅ exact |
| PI-18 | defect | Transactions ingested twice (identical payload) | DQ-TXN-021, DQ-TXN-002 | 400, 400 | 400, 700 | 400, 700 | ✅ exact |
| PI-19 | expected behaviour | Same transaction_id seen as PENDING then SUCCESSFUL | DQ-TXN-002 | 300 | 700 | 700 | ✅ exact |
| PI-20 | defect | Same NIP session posted twice under two transaction IDs | DQ-TXN-012 | 50 | 50 | 50 | ✅ exact |
| PI-21 | defect | Transactions with no amount | DQ-TXN-003 | 40 | 40 | 40 | ✅ exact |
| PI-22 | defect | Zero or negative amounts | DQ-TXN-004 | 30 | 30 | 30 | ✅ exact |
| PI-23 | defect | USSD amounts reported in kobo instead of naira (100x) | DQ-TXN-016 | 80 | 80 | 80 | ✅ exact |
| PI-24 | standardisable | Status values in non-canonical case/spelling (fixed by standardisation) | DQ-TXN-006 | 500 | 540 | 540 | ✅ exact |
| PI-25 | defect | Unrecognised status values ('UNKNOWN', raw response code '99') | DQ-TXN-005, DQ-TXN-006 | 40, 40 | 40, 540 | 40, 540 | ✅ exact |
| PI-26 | defect | Transactions on accounts that do not exist | DQ-TXN-008 | 60 | 60 | 60 | ✅ exact |
| PI-27 | defect | POS transactions from terminals missing in the registry | DQ-TXN-009 | 45 | 45 | 45 | ✅ exact |
| PI-28 | defect | POS transactions with no terminal ID | DQ-TXN-010 | 35 | 35 | 35 | ✅ exact |
| PI-29 | defect | POS timestamps from 1970 or the future | DQ-TXN-011 | 20 | 20 | 20 | ✅ exact |
| PI-30 | defect | Settled before it was created | DQ-TXN-014 | 30 | 30 | 30 | ✅ exact |
| PI-31 | defect | Fee larger than the transaction amount | DQ-TXN-015 | 20 | 20 | 20 | ✅ exact |
| PI-32 | defect | Transfers with an unknown counterparty bank code | DQ-TXN-013 | 40 | 40 | 40 | ✅ exact |
| PI-33 | defect | USSD feed silent for 30 hours | DQ-TXN-019 | 1 | 1 | 1 | ✅ exact |
| PI-34 | defect | Successful debits on accounts after they were closed | DQ-TXN-017 | 15 | 15 | 15 | ✅ exact |
| PI-35 | defect | Transactions file has fewer rows than its control total | DQ-TXN-022 | 1 | 1 | 1 | ✅ exact |

*Rows planted* is this issue's own contribution. *Rule expected* adds up every planted issue that feeds the same rule (PI-11 and PI-12 both fail DQ-ACC-003; PI-18 and PI-19 both fail DQ-TXN-002), and *exact* means the rule's failing-row count equals that total. 31 are defects; the rest are standardisable formats, a tolerated gap and expected CDC behaviour, planted to check the rules tell them apart from real defects.

## Run history

| Published (UTC) | Batch as of | Score | RAG | Breached | Critical |
|---|---|---|---|---|---|
| 2026-10-25 17:54 | 2026-10-25 14:00 | 94.0% | 🔴 RED | 31 | 9 |
| 2026-10-25 15:16 | 2026-10-25 14:00 | 94.0% | 🔴 RED | 31 | 9 |

## Silver contract

26 of 26 contract tests pass (uniqueness, not-null, accepted values and relationships on silver and gold, plus reference-data checks). These run at severity `error`: a failure stops the build before gold is refreshed.
