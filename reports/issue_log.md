# DQ issue log

Batch as of **2026-10-25 14:00 WAT** · run `69f95764` · 28 issues, open by priority: P1 **5**, P2 **12**, P3 **6**, P4 **2**

Detection fields (rules, failing rows, value, sample keys, first detected) are written by the pipeline. Triage fields (priority, owner, status, root cause, impact, remediation, prevention) come from [`dq/issue_triage.yml`](../dq/issue_triage.yml). Priority and status definitions are in [the DQ framework](../docs/dq_framework.md#issue-management).

| Issue | Priority | Status | Title | Owner | Failing rows | Value affected |
|---|---|---|---|---|---|---|
| [ISS-001](#iss-001) | P1 | IN_REMEDIATION | Customers debited twice for one NIP transfer | Settlement & Reconciliation | DQ-TXN-012: 50 of 18,149 | ₦992,519 |
| [ISS-002](#iss-002) | P1 | OPEN | USSD amounts arriving in kobo (100x overstated) | Partnerships (USSD) | DQ-TXN-016: 80 of 60,447 | ₦63,144,702 |
| [ISS-003](#iss-003) | P1 | OPEN | USSD feed silent for 30 hours | Partnerships (USSD) | DQ-TXN-019: 1 of 5 | — |
| [ISS-004](#iss-004) | P1 | OPEN | Transaction extract truncated (fewer rows than control total) | Payments Engineering | DQ-TXN-022: 1 of 1 | — |
| [ISS-016](#iss-016) | P1 | OPEN | Tier 2/3 customers with no BVN | Customer Onboarding & KYC | DQ-CUS-003: 120 of 3,303 | — |
| [ISS-005](#iss-005) | P2 | MONITORING | Transactions ingested twice | Payments Engineering | DQ-TXN-021: 400 of 60,447; DQ-TXN-002: 700 of 60,447 | ₦8,757,199 |
| [ISS-006](#iss-006) | P2 | OPEN | Transactions posted to accounts that do not exist | Payments Engineering | DQ-TXN-008: 60 of 60,447 | ₦875,263 |
| [ISS-007](#iss-007) | P2 | OPEN | Terminal registry 52 hours stale, so new terminals look unregistered | Agency Banking Operations | DQ-TRM-005: 1 of 1; DQ-TXN-009: 45 of 27,105 | ₦524,500 |
| [ISS-008](#iss-008) | P2 | OPEN | Reversal advices with missing or signed amounts | Payments Engineering | DQ-TXN-003: 40 of 60,447; DQ-TXN-004: 30 of 60,447 | ₦266,419 |
| [ISS-009](#iss-009) | P2 | OPEN | Unmapped processor status codes | Payments Engineering | DQ-TXN-005: 40 of 60,447 | ₦768,488 |
| [ISS-010](#iss-010) | P2 | OPEN | Settlement timestamps one hour behind (UTC vs WAT) | Settlement & Reconciliation | DQ-TXN-014: 30 of 60,447 | ₦525,743 |
| [ISS-011](#iss-011) | P2 | OPEN | Fees posted in kobo | Finance - Revenue Assurance | DQ-TXN-015: 20 of 60,377 | ₦12,114 |
| [ISS-012](#iss-012) | P2 | OPEN | Successful debits on closed accounts | Cards | DQ-TXN-017: 15 of 60,447 | ₦219,344 |
| [ISS-017](#iss-017) | P2 | OPEN | Malformed BVNs (truncated, scientific notation, letter O) | Customer Onboarding & KYC | DQ-CUS-004: 40 of 4,079 | — |
| [ISS-018](#iss-018) | P2 | OPEN | One BVN on two customer profiles | Customer Onboarding & KYC | DQ-CUS-005: 120 of 4,079 | — |
| [ISS-024](#iss-024) | P2 | OPEN | Account numbers that fail the NUBAN check digit | Core Banking Operations | DQ-ACC-003: 40 of 6,630 | — |
| [ISS-026](#iss-026) | P2 | OPEN | Accounts whose customer does not exist | Core Banking Operations | DQ-ACC-002: 25 of 6,630 | — |
| [ISS-027](#iss-027) | P2 | OPEN | Terminal hardware and settlement registry defects | Agency Banking Operations | DQ-TRM-002: 16 of 400; DQ-TRM-003: 6 of 400 | — |
| [ISS-013](#iss-013) | P3 | OPEN | POS terminals with wrong clocks (1970 and future dates) | Agency Banking Operations | DQ-TXN-011: 20 of 60,447 | ₦319,400 |
| [ISS-014](#iss-014) | P3 | OPEN | POS transactions with no terminal ID | Agency Banking Operations | DQ-TXN-010: 35 of 27,140 | ₦398,900 |
| [ISS-015](#iss-015) | P3 | OPEN | Transfers to unknown bank codes | Payments Engineering | DQ-TXN-013: 40 of 18,149 | ₦1,012,596 |
| [ISS-019](#iss-019) | P3 | OPEN | Phone numbers that cannot be standardised | Customer Onboarding & KYC | DQ-CUS-006: 50 of 5,060 | — |
| [ISS-020](#iss-020) | P3 | OPEN | Implausible dates of birth | Customer Onboarding & KYC | DQ-CUS-009: 25 of 5,060 | — |
| [ISS-023](#iss-023) | P3 | MONITORING | Account rows delivered twice | Core Banking Operations | DQ-ACC-001: 80 of 6,630 | — |
| [ISS-025](#iss-025) | P3 | OPEN | Closed accounts with no closure date | Core Banking Operations | DQ-ACC-004: 15 of 235 | — |
| [ISS-021](#iss-021) | P4 | OPEN | State of residence is a city, typo or placeholder | Customer Onboarding & KYC | DQ-CUS-008: 30 of 5,060 | — |
| [ISS-022](#iss-022) | P4 | OPEN | Malformed email addresses | Customer Onboarding & KYC | DQ-CUS-011: 20 of 4,407 | — |
| [ISS-028](#iss-028) | P4 | RISK_ACCEPTED | Sources send phone numbers and statuses in their own formats | Data Governance | DQ-CUS-007: 3,813 of 5,060; DQ-TXN-006: 540 of 60,447 | ₦8,671,229 |

Value affected is the absolute naira value of failing rows as received (for the kobo issue, the inflated value). Where an issue spans several overlapping rules, the largest single-rule value is shown.

## Detail

<a id="iss-001"></a>
### ISS-001 · Customers debited twice for one NIP transfer

**P1 · IN_REMEDIATION · Settlement & Reconciliation** · transactions · uniqueness  
Rules: DQ-TXN-012: 50 of 18,149 · Value affected: ₦992,519 · First detected: 2026-10-25  
Sample keys: `TRX02D9E49D3473, TRX02F1E321CD29, TRX050193526563, TRX097B9A2D29BF, TRX149A44EB5401`

- **Root cause:** The mobile app retries a transfer that timed out with a new transaction ID but the same NIP session ID. The ledger's idempotency key is the transaction ID, so both legs post.
- **Impact:** Each affected customer was debited twice; the failing-row value covers both legs, so half of it is money taken in error. Direct complaint, refund and CBN consumer-protection exposure.
- **Remediation:** Second legs are quarantined in silver. Reversal batch raised with Settlement for every session in the sample; customers to be refunded and notified.
- **Prevention:** Make the NIP session ID the ledger idempotency key. Keep DQ-TXN-012 at critical and page on any breach.
- **Related:** —

<a id="iss-002"></a>
### ISS-002 · USSD amounts arriving in kobo (100x overstated)

**P1 · OPEN · Partnerships (USSD)** · transactions · consistency  
Rules: DQ-TXN-016: 80 of 60,447 · Value affected: ₦63,144,702 · First detected: 2026-10-25  
Sample keys: `TRX06B71AA0DED2, TRX07F3A7E50459, TRX13007097D848, TRX14C6FA47F103, TRX151D62FF6A4C`

- **Root cause:** The USSD aggregator's v2 API reports amounts in minor units (kobo). The integration still treats the field as naira. Every failing row is a USSD debit from a tier 1/2 account, and divided by 100 every amount falls back inside the tier limit and the normal USSD ticket size.
- **Impact:** Reported value for the affected rows is 100x the real value. Had they reached gold, USSD value and total value for the period would be materially overstated, and the rows also look like KYC limit breaches.
- **Remediation:** Rows quarantined. Confirm units with the aggregator, divide by 100, replay through silver.
- **Prevention:** Data contract with the aggregator that names the currency unit, plus a per-channel amount distribution check to catch the next unit change.
- **Related:** [ISS-003](#iss-003)

<a id="iss-003"></a>
### ISS-003 · USSD feed silent for 30 hours

**P1 · OPEN · Partnerships (USSD)** · transactions · freshness  
Rules: DQ-TXN-019: 1 of 5 · Value affected: — · First detected: 2026-10-25  
Sample keys: `USSD`

- **Root cause:** The aggregator's SFTP credentials expired and no files have been pushed since. Table-level freshness (DQ-TXN-018) still passes because POS and transfers keep the latest timestamp fresh; only the per-channel check fires.
- **Impact:** USSD activity for more than a day is missing from dashboards, fraud monitoring and agent commission. Day-close totals are understated.
- **Remediation:** Rotate credentials, request a backfill from the last delivered file, reload.
- **Prevention:** Alert on per-channel freshness, not just table freshness. Track credential expiry dates for every external feed.
- **Related:** [ISS-002](#iss-002)

<a id="iss-004"></a>
### ISS-004 · Transaction extract truncated (fewer rows than control total)

**P1 · OPEN · Payments Engineering** · transactions · completeness  
Rules: DQ-TXN-022: 1 of 1 · Value affected: — · First detected: 2026-10-25  
Sample keys: `transactions`

- **Root cause:** The control file declares more rows than were received. The extract was cut off mid-transfer and the loader does not compare against the control file.
- **Impact:** Missing rows are missing money. Every downstream total for the batch is understated, with no error anywhere else in the pipeline.
- **Remediation:** Re-request the full extract and reload the batch.
- **Prevention:** Make the control-total check a gate: reject the batch before bronze when the counts do not reconcile.
- **Related:** —

<a id="iss-016"></a>
### ISS-016 · Tier 2/3 customers with no BVN

**P1 · OPEN · Customer Onboarding & KYC** · customers · completeness  
Rules: DQ-CUS-003: 120 of 3,303 · Value affected: — · First detected: 2026-10-25  
Sample keys: `CUS0000070, CUS0000099, CUS0000125, CUS0000181, CUS0000224`

- **Root cause:** Back-office tier upgrades by override, without BVN capture.
- **Impact:** Customers transacting at tier 2/3 limits without verified identity: a KYC compliance finding.
- **Remediation:** Downgrade to tier 1 until a BVN is verified; outreach campaign through agents.
- **Prevention:** Remove the override; tier upgrade requires a verified BVN.
- **Related:** [ISS-017](#iss-017)

<a id="iss-005"></a>
### ISS-005 · Transactions ingested twice

**P2 · MONITORING · Payments Engineering** · transactions · uniqueness  
Rules: DQ-TXN-021: 400 of 60,447; DQ-TXN-002: 700 of 60,447 · Value affected: ₦8,757,199 · First detected: 2026-10-25  
Sample keys: `TRX040C247ED475, TRX065536BB042C, TRX06E004AE9289, TRX07774ECCA91F, TRX08587BA9EB05`

- **Root cause:** The switch retries its webhook after a 504 and the consumer does not dedupe on transaction ID, so identical payloads land twice (DQ-TXN-021). DQ-TXN-002 fails on more rows than that because this feed is change data capture: a PENDING row followed by a SUCCESSFUL row for the same ID is expected.
- **Impact:** Contained: silver keeps the latest version of each transaction ID, so gold is not double counted. Raw-layer consumers (ad-hoc SQL on bronze) would be.
- **Remediation:** Dedupe in silver (live). Consumer idempotency fix raised with Payments Engineering.
- **Prevention:** Tune the rules: point DQ-TXN-002 at the latest-version view, or make it unique on (transaction_id, status), so it stops counting legitimate status updates. DQ-TXN-021 stays as the true double-ingestion signal.
- **Related:** —

<a id="iss-006"></a>
### ISS-006 · Transactions posted to accounts that do not exist

**P2 · OPEN · Payments Engineering** · transactions · ref. integrity  
Rules: DQ-TXN-008: 60 of 60,447 · Value affected: ₦875,263 · First detected: 2026-10-25  
Sample keys: `TRX008E14AA8B70, TRX0115669D34F7, TRX028BC0C794E9, TRX042FF33196F6, TRX059BD6221B76`

- **Root cause:** Every failing row comes from a non-transfer channel and carries an account ID outside the core banking range: wallet IDs from a decommissioned ledger that the bills hub still routes to.
- **Impact:** Money moved that cannot be attributed to a customer, limited by KYC tier or reconciled. Quarantined.
- **Remediation:** Map legacy wallet IDs to current accounts with Core Banking Ops, then replay.
- **Prevention:** Retire the legacy routing table in the bills hub.
- **Related:** —

<a id="iss-007"></a>
### ISS-007 · Terminal registry 52 hours stale, so new terminals look unregistered

**P2 · OPEN · Agency Banking Operations** · terminals, transactions · freshness, ref. integrity  
Rules: DQ-TRM-005: 1 of 1; DQ-TXN-009: 45 of 27,105 · Value affected: ₦524,500 · First detected: 2026-10-25  
Sample keys: `ALL`

- **Root cause:** The TMS export job has failed silently since the weekend. Terminals activated after the last good snapshot are transacting but are not in the registry, so their POS transactions fail the referential check. The integrity failure is a symptom of the freshness failure, not a separate defect.
- **Impact:** Cash-outs on these terminals cannot be attributed to an agent for commission or fraud monitoring until the registry refreshes. Transactions are kept (FLAG), so volume and value are not understated.
- **Remediation:** Fix and re-run the TMS export. The flagged transactions resolve on the next load.
- **Prevention:** Freshness alert on the registry. Fix the root cause first: chasing the "orphan" transactions one by one would have wasted a day.
- **Related:** —

<a id="iss-008"></a>
### ISS-008 · Reversal advices with missing or signed amounts

**P2 · OPEN · Payments Engineering** · transactions · completeness, validity  
Rules: DQ-TXN-003: 40 of 60,447; DQ-TXN-004: 30 of 60,447 · Value affected: ₦266,419 · First detected: 2026-10-25  
Sample keys: `TRX02CB1D52650D, TRX06760CE62667, TRX13A9CC0E41F9, TRX13C465F918A1, TRX147DA91278A3`

- **Root cause:** The processor sends some reversal advices with a null amount and others with a negative amount instead of direction = CR.
- **Impact:** Cannot post or settle null amounts. Negative amounts double-reverse when summed with direction. All quarantined.
- **Remediation:** Re-request the advices; map signed reversals to a positive amount with direction CR.
- **Prevention:** Schema contract with the processor (amount > 0, not null) and reject at ingestion.
- **Related:** —

<a id="iss-009"></a>
### ISS-009 · Unmapped processor status codes

**P2 · OPEN · Payments Engineering** · transactions · validity  
Rules: DQ-TXN-005: 40 of 60,447 · Value affected: ₦768,488 · First detected: 2026-10-25  
Sample keys: `TRX00B3A04C6D4D, TRX00FF0064570E, TRX01212B77D000, TRX02284AB1D1A6, TRX08CCFB5F05F9`

- **Root cause:** Raw processor response codes ('99') and 'UNKNOWN' pass through without mapping. Spelling variants (Success, successful) are already standardised in silver and tracked separately as source conformity (DQ-TXN-006).
- **Impact:** Cannot tell whether money moved; success rate and value exclude these until resolved.
- **Remediation:** Get final status from the processor and replay.
- **Prevention:** Status mapping table owned by each integration, with unknowns rejected at ingestion.
- **Related:** [ISS-028](#iss-028)

<a id="iss-010"></a>
### ISS-010 · Settlement timestamps one hour behind (UTC vs WAT)

**P2 · OPEN · Settlement & Reconciliation** · transactions · consistency  
Rules: DQ-TXN-014: 30 of 60,447 · Value affected: ₦525,743 · First detected: 2026-10-25  
Sample keys: `TRX0C8608CBA193, TRX18165201D926, TRX1944DAE4A7AD, TRX224F5AFEE9A0, TRX2722926A3037`

- **Root cause:** Every failing row is settled 56 to 60 minutes before it was created, which is a normal settlement lag minus one hour: the settlement service writes UTC while the switch writes West Africa Time (UTC+1).
- **Impact:** Transactions near midnight fall into the wrong settlement day, which breaks daily reconciliation with NIBSS and the card schemes.
- **Remediation:** Convert settlement timestamps to WAT in silver once the source is confirmed.
- **Prevention:** Store timestamps as timestamptz end to end; add the timezone to the data contract.
- **Related:** —

<a id="iss-011"></a>
### ISS-011 · Fees posted in kobo

**P2 · OPEN · Finance - Revenue Assurance** · transactions · consistency  
Rules: DQ-TXN-015: 20 of 60,377 · Value affected: ₦12,114 · First detected: 2026-10-25  
Sample keys: `TRX11B112D3BBF8, TRX1276E06CC974, TRX224F4ACC9C9B, TRX30E472316474, TRX365656B10320`

- **Root cause:** The pricing engine posted some fees in kobo, so the fee exceeds the transaction amount.
- **Impact:** Fee income overstated; customers may have been overcharged. Quarantined.
- **Remediation:** Recompute fees from the tariff table and refund any overcharge.
- **Prevention:** Fee-to-amount ratio check in the pricing engine before posting.
- **Related:** [ISS-002](#iss-002)

<a id="iss-012"></a>
### ISS-012 · Successful debits on closed accounts

**P2 · OPEN · Cards** · transactions · consistency  
Rules: DQ-TXN-017: 15 of 60,447 · Value affected: ₦219,344 · First detected: 2026-10-25  
Sample keys: `TRX01D649760A4A, TRX0E3F99DA35E6, TRX1A647D623390, TRX1F64343804D9, TRX232E9DF26D79`

- **Root cause:** Cards were not hot-listed when their account was closed, so card debits still authorise.
- **Impact:** Control failure and likely complaints. Transactions are kept (they happened) and flagged for Cards and Compliance.
- **Remediation:** Hot-list all cards on closed accounts; review each flagged debit.
- **Prevention:** Make card hot-listing a step in the account closure workflow.
- **Related:** [ISS-025](#iss-025)

<a id="iss-017"></a>
### ISS-017 · Malformed BVNs (truncated, scientific notation, letter O)

**P2 · OPEN · Customer Onboarding & KYC** · customers · validity  
Rules: DQ-CUS-004: 40 of 4,079 · Value affected: — · First detected: 2026-10-25  
Sample keys: `CUS0000264, CUS0000424, CUS0000437, CUS0001010, CUS0001236`

- **Root cause:** A bulk KYC remediation file was round-tripped through Excel.
- **Impact:** These BVNs fail NIBSS verification and defeat the duplicate-identity check.
- **Remediation:** Re-pull from the original remediation source; re-verify with NIBSS.
- **Prevention:** Never move identifiers through Excel; load bulk files as text.
- **Related:** [ISS-016](#iss-016)

<a id="iss-018"></a>
### ISS-018 · One BVN on two customer profiles

**P2 · OPEN · Customer Onboarding & KYC** · customers · uniqueness  
Rules: DQ-CUS-005: 120 of 4,079 · Value affected: — · First detected: 2026-10-25  
Sample keys: `CUS0000017, CUS0000130, CUS0000131, CUS0000277, CUS0000477`

- **Root cause:** Customers re-onboarded through a second agent. No BVN uniqueness check at onboarding. The second profile is upper-cased and created later, consistent with agent re-capture rather than fraud, but each pair needs review.
- **Impact:** Split customer view, double-counted customers, and potential KYC limit evasion across two profiles.
- **Remediation:** Review pairs, merge confirmed duplicates in CIF, escalate anything suspicious to Compliance.
- **Prevention:** BVN uniqueness check at onboarding.
- **Related:** —

<a id="iss-024"></a>
### ISS-024 · Account numbers that fail the NUBAN check digit

**P2 · OPEN · Core Banking Operations** · accounts · validity  
Rules: DQ-ACC-003: 40 of 6,630 · Value affected: — · First detected: 2026-10-25  
Sample keys: `ACC00000134, ACC00000234, ACC00000553, ACC00000612, ACC00000827`

- **Root cause:** Two causes: manual capture during the 2024 core banking migration (wrong check digit), and an extract re-saved in Excel, which stripped leading zeros (9-digit numbers).
- **Impact:** Inbound NIP transfers to these numbers are rejected or misrouted.
- **Remediation:** Correct from the core banking master; left-pad the 9-digit numbers and re-validate.
- **Prevention:** NUBAN check-digit validation at capture; identifiers loaded as text.
- **Related:** [ISS-015](#iss-015)

<a id="iss-026"></a>
### ISS-026 · Accounts whose customer does not exist

**P2 · OPEN · Core Banking Operations** · accounts · ref. integrity  
Rules: DQ-ACC-002: 25 of 6,630 · Value affected: — · First detected: 2026-10-25  
Sample keys: `ACC00006566, ACC00006567, ACC00006568, ACC00006569, ACC00006570`

- **Root cause:** CIF records purged during the migration while their accounts were kept.
- **Impact:** Accounts with no KYC tier or AML profile; cannot be included in regulatory returns correctly.
- **Remediation:** Restore CIF records from the migration archive.
- **Prevention:** Foreign-key constraint between account and CIF in the core banking schema.
- **Related:** —

<a id="iss-027"></a>
### ISS-027 · Terminal hardware and settlement registry defects

**P2 · OPEN · Agency Banking Operations** · terminals · ref. integrity, uniqueness  
Rules: DQ-TRM-002: 16 of 400; DQ-TRM-003: 6 of 400 · Value affected: — · First detected: 2026-10-25  
Sample keys: `2NR00015, 2NR00026, 2NR00060, 2NR00065, 2NR00114`

- **Root cause:** Devices swapped between agents without retiring the old terminal ID (shared serials), and settlement accounts typed by hand in the TMS (account not found).
- **Impact:** Cash-outs can settle to the wrong agent (shared serials) or fail to settle (unknown account). The unknown-account terminals had no transactions in this batch, so that half has not cost money yet.
- **Remediation:** Retire superseded terminal IDs; correct settlement accounts from agent onboarding records.
- **Prevention:** TMS validation of settlement account against core banking at terminal setup.
- **Related:** [ISS-007](#iss-007)

<a id="iss-013"></a>
### ISS-013 · POS terminals with wrong clocks (1970 and future dates)

**P3 · OPEN · Agency Banking Operations** · transactions · validity  
Rules: DQ-TXN-011: 20 of 60,447 · Value affected: ₦319,400 · First detected: 2026-10-25  
Sample keys: `TRX035B27C01280, TRX21F7FB10DC48, TRX32029C55AC76, TRX33483590B226, TRX3BD14335CA13`

- **Root cause:** Terminal real-time clocks reset to the epoch (flat RTC battery) or were set by hand.
- **Impact:** Transactions fall outside any reporting day. Quarantined until re-dated from switch receipt time.
- **Remediation:** Re-date from switch receipt time; list affected terminals for field service.
- **Prevention:** Use switch receipt time as the event time of record; sync terminal clocks over NTP.
- **Related:** —

<a id="iss-014"></a>
### ISS-014 · POS transactions with no terminal ID

**P3 · OPEN · Agency Banking Operations** · transactions · completeness  
Rules: DQ-TXN-010: 35 of 27,140 · Value affected: ₦398,900 · First detected: 2026-10-25  
Sample keys: `TRX0101E4571D0A, TRX0875B837156D, TRX088FA4FF480D, TRX1A9CE61A1446, TRX23A1CE438198`

- **Root cause:** Older terminal firmware drops ISO 8583 field 41 (terminal ID) on fallback transactions.
- **Impact:** Cannot attribute to an agent or device; flagged and excluded from the agent league table.
- **Remediation:** Recover the terminal ID from switch logs by STAN and RRN.
- **Prevention:** Firmware upgrade for the affected models.
- **Related:** —

<a id="iss-015"></a>
### ISS-015 · Transfers to unknown bank codes

**P3 · OPEN · Payments Engineering** · transactions · ref. integrity  
Rules: DQ-TXN-013: 40 of 18,149 · Value affected: ₦1,012,596 · First detected: 2026-10-25  
Sample keys: `TRX0051FA8FC557, TRX0D9C12521F7B, TRX120D0E74C53C, TRX15CAE9461927, TRX222FAC6F2795`

- **Root cause:** Leading zeros stripped ('58' for GTBank '058') and placeholder codes ('000') on manually keyed transfers.
- **Impact:** Breaks inter-bank settlement reporting and NIBSS reconciliation for these rows. Flagged.
- **Remediation:** Left-pad numeric codes to 3 digits; resolve placeholders from the NIP response.
- **Prevention:** Treat bank codes as strings everywhere (the ref_banks seed is typed varchar for the same reason).
- **Related:** [ISS-024](#iss-024)

<a id="iss-019"></a>
### ISS-019 · Phone numbers that cannot be standardised

**P3 · OPEN · Customer Onboarding & KYC** · customers · validity  
Rules: DQ-CUS-006: 50 of 5,060 · Value affected: — · First detected: 2026-10-25  
Sample keys: `CUS0000058, CUS0000065, CUS0000183, CUS0000241, CUS0000356`

- **Root cause:** Free-text phone field with no input mask on the agent onboarding form.
- **Impact:** OTPs and alerts do not reach these customers.
- **Remediation:** Collect correct numbers at next agent or app touchpoint.
- **Prevention:** Input mask and OTP verification at onboarding.
- **Related:** [ISS-028](#iss-028)

<a id="iss-020"></a>
### ISS-020 · Implausible dates of birth

**P3 · OPEN · Customer Onboarding & KYC** · customers · validity  
Rules: DQ-CUS-009: 25 of 5,060 · Value affected: — · First detected: 2026-10-25  
Sample keys: `CUS0000034, CUS0000159, CUS0000173, CUS0000788, CUS0000862`

- **Root cause:** The DOB widget fails on low-end Android devices and leaves the 1900-01-01 default.
- **Impact:** Age-based eligibility and KYC checks are wrong; possible under-age customers.
- **Remediation:** Verify DOB against the BVN record.
- **Prevention:** Fill DOB from the BVN record instead of manual entry.
- **Related:** —

<a id="iss-023"></a>
### ISS-023 · Account rows delivered twice

**P3 · MONITORING · Core Banking Operations** · accounts · uniqueness  
Rules: DQ-ACC-001: 80 of 6,630 · Value affected: — · First detected: 2026-10-25  
Sample keys: `ACC00000029, ACC00000287, ACC00000370, ACC00000542, ACC00000743`

- **Root cause:** A CDC batch was re-delivered after a connector timeout; the loader is not idempotent.
- **Impact:** Contained by the silver dedupe. Would fan out every join on account if read from bronze.
- **Remediation:** Dedupe in silver (live).
- **Prevention:** Idempotent loader (merge on account ID and change sequence).
- **Related:** [ISS-005](#iss-005)

<a id="iss-025"></a>
### ISS-025 · Closed accounts with no closure date

**P3 · OPEN · Core Banking Operations** · accounts · completeness  
Rules: DQ-ACC-004: 15 of 235 · Value affected: — · First detected: 2026-10-25  
Sample keys: `ACC00000756, ACC00001103, ACC00001590, ACC00002239, ACC00003271`

- **Root cause:** Closures done by status override instead of the closure workflow.
- **Impact:** The post-closure debit control (DQ-TXN-017) cannot run for these accounts, so ISS-012 may be undercounted.
- **Remediation:** Backfill closure dates from the audit trail.
- **Prevention:** Block status-only closures.
- **Related:** [ISS-012](#iss-012)

<a id="iss-021"></a>
### ISS-021 · State of residence is a city, typo or placeholder

**P4 · OPEN · Customer Onboarding & KYC** · customers · validity  
Rules: DQ-CUS-008: 30 of 5,060 · Value affected: — · First detected: 2026-10-25  
Sample keys: `CUS0000104, CUS0000220, CUS0000503, CUS0000516, CUS0000598`

- **Root cause:** Free-text state field; agents type the city (Ikeja, Port Harcourt) or a placeholder.
- **Impact:** Minor distortion of regional reporting and AML geography scoring.
- **Remediation:** Add city-to-state aliases where unambiguous; re-collect the rest.
- **Prevention:** Dropdown of states at onboarding.
- **Related:** —

<a id="iss-022"></a>
### ISS-022 · Malformed email addresses

**P4 · OPEN · Customer Onboarding & KYC** · customers · validity  
Rules: DQ-CUS-011: 20 of 4,407 · Value affected: — · First detected: 2026-10-25  
Sample keys: `CUS0000041, CUS0000329, CUS0000745, CUS0000838, CUS0001379`

- **Root cause:** No email validation on the USSD and agent onboarding paths.
- **Impact:** Statements and e-receipts bounce.
- **Remediation:** Re-collect at the next touchpoint.
- **Prevention:** Format validation at capture.
- **Related:** —

<a id="iss-028"></a>
### ISS-028 · Sources send phone numbers and statuses in their own formats

**P4 · RISK_ACCEPTED · Data Governance** · customers, transactions · validity  
Rules: DQ-CUS-007: 3,813 of 5,060; DQ-TXN-006: 540 of 60,447 · Value affected: ₦8,671,229 · First detected: 2026-10-25  
Sample keys: `CUS0000001, CUS0000002, CUS0000003, CUS0000005, CUS0000006`

- **Root cause:** No shared format standard across onboarding channels and processors.
- **Impact:** None downstream: silver standardises these. The cost is pipeline complexity and the risk that a new variant slips past the mapping (see ISS-009).
- **Remediation:** None needed for reporting. Kept as monitors (not scored).
- **Prevention:** Publish format standards as part of each source's data contract.
- **Related:** [ISS-009](#iss-009), [ISS-019](#iss-019)
