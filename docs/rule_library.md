# DQ rule library

49 rules (47 scored, 2 source-conformity monitors) across 4 tables and 6 dimensions.

Generated from the dbt project by `scripts/render_reports.py`. Each rule is a dbt test in [`models/dq_rules/`](../models/dq_rules/) and its catalogue entry (ID, dimension, severity, action, threshold, owner, rationale) is the test's `config.meta`, so this page cannot drift from what runs. Severity, action and threshold are defined in [the DQ framework](dq_framework.md).

## Coverage

| Table | Completeness | Validity | Uniqueness | Ref. integrity | Consistency | Freshness | Total |
|---|---|---|---|---|---|---|---|
| Customers | 4 | 7 | 2 | · | · | 1 | 14 |
| Accounts | 2 | 2 | 1 | 1 | · | 1 | 7 |
| Terminals | 1 | 1 | 2 | 1 | · | 1 | 6 |
| Transactions | 5 | 5 | 3 | 3 | 4 | 2 | 22 |

## Customers

| ID | Rule and why it matters | Dimension | Severity | Action | Check | Owner |
|---|---|---|---|---|---|---|
| **DQ-CUS-001** | **Customer ID present**<br>A profile with no CIF ID cannot be linked to accounts, KYC or AML screening. | Completeness | critical | QUARANTINE | `stg_customers`: `customer_id` is not null | Customer Onboarding & KYC |
| **DQ-CUS-002** | **Customer ID unique**<br>Two rows for one CIF ID double-count customers and break every join on customer. | Uniqueness | critical | DEDUPE | `stg_customers`: `customer_id` is unique | Customer Onboarding & KYC |
| **DQ-CUS-003** | **BVN present for KYC tier 2 and 3**<br>Tiered KYC requires identity verification above tier 1; a tier 2/3 customer with no BVN is a regulatory finding. | Completeness | high | FLAG | `stg_customers`: `bvn` is not null where `kyc_tier >= 2` | Customer Onboarding & KYC |
| **DQ-CUS-004** | **BVN is 11 digits**<br>A malformed BVN fails NIBSS verification and silently defeats duplicate-identity checks. | Validity | high | FLAG | `stg_customers`: `bvn` matches `^[0-9]{11}$` | Customer Onboarding & KYC |
| **DQ-CUS-005** | **One BVN, one customer profile**<br>A BVN on two CIFs is either a re-onboarded customer (split exposure, double counted) or identity misuse. | Uniqueness | high | FLAG | `stg_customers`: `bvn` is unique | Customer Onboarding & KYC |
| **DQ-CUS-006** | **Phone is a valid Nigerian mobile (after standardisation)**<br>OTPs, transaction alerts and collections all go to this number. | Validity | medium | FLAG | `stg_customers`: `phone_e164` matches `^\+234[789][01][0-9]{8}$` | Customer Onboarding & KYC |
| **DQ-CUS-007** | **Phone captured in E.164 at source**<br>Measures standardisation load; the fix is an input mask in the onboarding apps. | Validity | low | MONITOR · not scored | `brz_customers`: `phone_number` matches `^\+234[789][01][0-9]{8}$` | Customer Onboarding & KYC |
| **DQ-CUS-008** | **State of residence is one of the 36 states or FCT**<br>Drives regional reporting, agent coverage planning and AML geography risk scoring. | Validity | medium | FLAG | `stg_customers`: `state_of_residence` exists in `ref_states.state_name` | Customer Onboarding & KYC |
| **DQ-CUS-009** | **Customer is 18 to 110 years old**<br>Placeholder (1900-01-01), future and under-age birth dates break age-based KYC and product eligibility. | Validity | high | FLAG | `stg_customers`: `date_of_birth between (batch_as_of - interval 110 year)::date and (batch_as_of - interval 18 year)::date` | Customer Onboarding & KYC |
| **DQ-CUS-010** | **Email present (80% tolerance)**<br>Email is optional on USSD and agent onboarding, so it is tracked against a tolerance, not zero defects. | Completeness | low | MONITOR (pass ≥ 80%) | `stg_customers`: `email` is not null | Customer Onboarding & KYC |
| **DQ-CUS-011** | **Email well formed**<br>Statements and e-receipts bounce. | Validity | low | FLAG | `stg_customers`: `email` matches `^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$` | Customer Onboarding & KYC |
| **DQ-CUS-012** | **KYC tier is 1, 2 or 3**<br>Tier sets the transaction and balance limits enforced downstream. | Validity | high | FLAG | `stg_customers`: `kyc_tier` in (1, 2, 3) | Customer Onboarding & KYC |
| **DQ-CUS-013** | **Customer extract delivered within 24h**<br>Stale CIF data means new customers are missing from limits and AML screening. | Freshness | high | MONITOR | `stg_feed_heartbeat`: `coalesce(hours_since_last_load, 1e9) <= sla_hours` where `dataset = 'customers'` | Customer Onboarding & KYC |
| **DQ-CUS-014** | **Customer file row count matches control total**<br>A short file means customers are silently missing downstream. | Completeness | high | MONITOR | `stg_batch_reconciliation`: `received_count = expected_count` where `dataset = 'customers'` | Customer Onboarding & KYC |

## Accounts

| ID | Rule and why it matters | Dimension | Severity | Action | Check | Owner |
|---|---|---|---|---|---|---|
| **DQ-ACC-001** | **Account ID unique**<br>Duplicate account rows fan out every join from transactions and double balances. | Uniqueness | critical | DEDUPE | `stg_accounts`: `account_id` is unique | Core Banking Operations |
| **DQ-ACC-002** | **Account owner exists in CIF**<br>An account with no owner has no KYC tier, no AML profile and cannot be reported to regulators. | Ref. integrity | critical | FLAG | `stg_accounts`: `customer_id` exists in `stg_customers.customer_id` | Core Banking Operations |
| **DQ-ACC-003** | **Account number is a valid NUBAN (CBN check digit)**<br>An invalid NUBAN cannot receive NIP inflows; funds sent to it are rejected or misrouted. | Validity | critical | FLAG | `stg_accounts`: `account_number` is a 10-digit NUBAN with a valid CBN check digit | Core Banking Operations |
| **DQ-ACC-004** | **Closure date present on closed accounts**<br>Without a closure date, post-closure activity controls (DQ-TXN-017) cannot run. | Completeness | medium | FLAG | `stg_accounts`: `closed_at` is not null where `status = 'CLOSED'` | Core Banking Operations |
| **DQ-ACC-005** | **Account status recognised**<br>Status drives debit blocks, dormancy reporting and closure controls. | Validity | high | FLAG | `stg_accounts`: `status` in (ACTIVE, DORMANT, FROZEN, CLOSED) | Core Banking Operations |
| **DQ-ACC-006** | **Account extract delivered within 24h**<br>New accounts would appear as orphans in the transaction feed. | Freshness | high | MONITOR | `stg_feed_heartbeat`: `coalesce(hours_since_last_load, 1e9) <= sla_hours` where `dataset = 'accounts'` | Core Banking Operations |
| **DQ-ACC-007** | **Account file row count matches control total**<br>A short file means accounts are silently missing downstream. | Completeness | high | MONITOR | `stg_batch_reconciliation`: `received_count = expected_count` where `dataset = 'accounts'` | Core Banking Operations |

## Terminals

| ID | Rule and why it matters | Dimension | Severity | Action | Check | Owner |
|---|---|---|---|---|---|---|
| **DQ-TRM-001** | **Terminal ID unique**<br>Terminal ID is the join key from every POS transaction to its agent. | Uniqueness | critical | DEDUPE | `stg_terminals`: `terminal_id` is unique | Agency Banking Operations |
| **DQ-TRM-002** | **One device serial, one terminal ID**<br>A device on two terminal IDs means a swap that was never retired; settlement can go to the old agent. | Uniqueness | high | FLAG | `stg_terminals`: `serial_number` is unique | Agency Banking Operations |
| **DQ-TRM-003** | **Settlement account exists**<br>Cash-outs on this terminal cannot be settled to the agent. | Ref. integrity | high | FLAG | `stg_terminals`: `account_id` exists in `stg_accounts.account_id` | Agency Banking Operations |
| **DQ-TRM-004** | **Terminal state is one of the 36 states or FCT**<br>Agent network coverage and cash-logistics planning are done by state. | Validity | medium | FLAG | `stg_terminals`: `state` exists in `ref_states.state_name` | Agency Banking Operations |
| **DQ-TRM-005** | **Terminal registry delivered within 24h**<br>Newly activated terminals are missing, so their cash-outs fail the registry check. | Freshness | high | MONITOR | `stg_feed_heartbeat`: `coalesce(hours_since_last_load, 1e9) <= sla_hours` where `dataset = 'terminals'` | Agency Banking Operations |
| **DQ-TRM-006** | **Terminal file row count matches control total**<br>A short file means terminals are silently missing downstream. | Completeness | medium | MONITOR | `stg_batch_reconciliation`: `received_count = expected_count` where `dataset = 'terminals'` | Agency Banking Operations |

## Transactions

| ID | Rule and why it matters | Dimension | Severity | Action | Check | Owner |
|---|---|---|---|---|---|---|
| **DQ-TXN-001** | **Transaction ID present**<br>Without an ID a transaction cannot be deduplicated, disputed or reconciled. | Completeness | critical | QUARANTINE | `stg_transactions`: `transaction_id` is not null | Payments Engineering |
| **DQ-TXN-002** | **Transaction ID unique**<br>Repeated IDs inflate volume and value; silver keeps the latest version of each ID. | Uniqueness | critical | DEDUPE | `stg_transactions`: `transaction_id` is unique | Payments Engineering |
| **DQ-TXN-003** | **Amount present**<br>A transaction with no amount cannot be posted, settled or reported. | Completeness | critical | QUARANTINE | `stg_transactions`: `amount` is not null | Payments Engineering |
| **DQ-TXN-004** | **Amount greater than zero**<br>Direction carries the sign; zero or negative amounts double-reverse when summed. | Validity | critical | QUARANTINE | `stg_transactions`: `amount > 0` | Payments Engineering |
| **DQ-TXN-005** | **Status recognised (after standardisation)**<br>Unknown status means we cannot tell whether money moved, so success rate and value are unreliable. | Validity | high | QUARANTINE | `stg_transactions`: `status` in (SUCCESSFUL, FAILED, PENDING, REVERSED) | Payments Engineering |
| **DQ-TXN-006** | **Status sent in the canonical vocabulary at source**<br>Measures standardisation load; the fix is a status mapping owned by each integration. | Validity | low | MONITOR · not scored | `brz_transactions`: `status` in (SUCCESSFUL, FAILED, PENDING, REVERSED) | Payments Engineering |
| **DQ-TXN-007** | **Channel recognised**<br>Channel drives fee rules, limits and every channel-level KPI. | Validity | high | QUARANTINE | `stg_transactions`: `channel` in (POS, TRANSFER, USSD, CARD, BILLS) | Payments Engineering |
| **DQ-TXN-008** | **Transaction account exists**<br>Money moved against an account we do not hold; it cannot be attributed, limited or reconciled. | Ref. integrity | critical | QUARANTINE | `stg_transactions`: `account_id` exists in `stg_accounts.account_id` | Payments Engineering |
| **DQ-TXN-009** | **POS terminal exists in registry**<br>Cash-outs on unregistered terminals cannot be attributed to an agent for commission or fraud monitoring. | Ref. integrity | high | FLAG | `stg_transactions`: `terminal_id` exists in `stg_terminals.terminal_id` | Agency Banking Operations |
| **DQ-TXN-010** | **POS transaction carries a terminal ID**<br>A POS transaction with no terminal cannot be traced to an agent or a device. | Completeness | high | FLAG | `stg_transactions`: `terminal_id` is not null where `channel = 'POS'` | Agency Banking Operations |
| **DQ-TXN-011** | **Transaction time between 2020 and the batch cut-off**<br>1970 and future-dated transactions land in the wrong reporting day, or no day at all. | Validity | high | QUARANTINE | `stg_transactions`: `created_at >= timestamp '2020-01-01' and created_at <= batch_as_of + interval 10 minute` | Agency Banking Operations |
| **DQ-TXN-012** | **One NIP session, one transaction**<br>Two ledger postings for one NIP session is a double debit; the customer has been charged twice. | Uniqueness | critical | QUARANTINE | `stg_transactions`: `session_id` is unique where `channel = 'TRANSFER'` | Settlement & Reconciliation |
| **DQ-TXN-013** | **Transfer counterparty bank code is a known CBN code**<br>Unknown bank codes break inter-bank settlement reporting and NIBSS reconciliation. | Ref. integrity | medium | FLAG | `stg_transactions`: `counterparty_bank_code` exists in `ref_banks.bank_code` where `channel = 'TRANSFER'` | Payments Engineering |
| **DQ-TXN-014** | **Settled at or after creation**<br>Negative settlement lag points at a timezone mismatch, which shifts transactions across settlement days. | Consistency | medium | FLAG | `stg_transactions`: `settled_at >= created_at` | Settlement & Reconciliation |
| **DQ-TXN-015** | **Fee not larger than the amount**<br>Fee income is overstated and the customer may have been overcharged. | Consistency | high | QUARANTINE | `stg_transactions`: `fee <= amount` where `amount > 0` | Finance - Revenue Assurance |
| **DQ-TXN-016** | **Amount within the KYC tier single-transaction limit**<br>Either a limit breach (compliance) or an amount in the wrong unit; both misstate value. | Consistency | high | QUARANTINE | `int_transactions_enriched`: `amount <= single_txn_limit_ngn` | Partnerships (USSD) |
| **DQ-TXN-017** | **No successful debits after account closure**<br>A debit on a closed account is a control failure (card not hot-listed) and a likely customer complaint. | Consistency | high | FLAG | `int_transactions_enriched`: `not (account_status = 'CLOSED' and direction = 'DR' and status = 'SUCCESSFUL' and created_at > account_closed_at)` | Cards |
| **DQ-TXN-018** | **Transaction feed delivered within 2h (table level)**<br>Intraday liquidity, fraud and agent dashboards read this feed. | Freshness | critical | MONITOR | `stg_feed_heartbeat`: `coalesce(hours_since_last_load, 1e9) <= sla_hours` where `dataset = 'transactions' and partition_key = 'ALL'` | Payments Engineering |
| **DQ-TXN-019** | **Every transaction channel delivered within its SLA**<br>A dead channel is invisible to a table-level check while the other channels keep the max timestamp fresh. | Freshness | high | MONITOR | `stg_feed_heartbeat`: `coalesce(hours_since_last_load, 1e9) <= sla_hours` where `dataset = 'transactions' and partition_key <> 'ALL'` | Payments Engineering |
| **DQ-TXN-020** | **NIP transfer carries a session ID**<br>The NIP session ID is the reference used for NIBSS reconciliation and customer disputes. | Completeness | high | FLAG | `stg_transactions`: `session_id` is not null where `channel = 'TRANSFER'` | Payments Engineering |
| **DQ-TXN-021** | **No exact duplicate payloads (double ingestion)**<br>Separates true re-deliveries from legitimate status updates that share a transaction ID (DQ-TXN-002). | Uniqueness | medium | DEDUPE | `stg_transactions`: `_row_hash` is unique | Payments Engineering |
| **DQ-TXN-022** | **Transaction file row count matches control total**<br>Missing rows are missing money; every downstream total is understated with no visible error. | Completeness | critical | MONITOR | `stg_batch_reconciliation`: `received_count = expected_count` where `dataset = 'transactions'` | Payments Engineering |
