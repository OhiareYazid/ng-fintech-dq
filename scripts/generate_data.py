#!/usr/bin/env python
"""Generate a synthetic Nigerian fintech dataset with planted data quality defects.

The fictional company is NairaRails MFB: agency banking (POS terminals run by
agents), NIP transfers, USSD, card and bill payments. Four source feeds land as
raw CSV extracts in data/raw/, together with a batch control file that declares
the expected record count of each extract.

Every defect is planted on purpose and recorded in
data/answer_key/planted_issues.json with the rule expected to catch it and the
number of failing rows it should produce. The DQ rules never read the answer
key; it exists so the pipeline can prove what it catches.

The run is seeded: the same --seed always produces the same rows, and --as-of
only shifts the timestamps.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WAT = timezone(timedelta(hours=1))  # West Africa Time: UTC+1, no DST

HOME_BANK_CODE = "990"  # fictional; must match var home_bank_code in dbt_project.yml
NIP_INSTITUTION_CODE = "090990"  # fictional; prefixes NIP session IDs
NUBAN_WEIGHTS = (3, 7, 3, 3, 7, 3, 3, 7, 3, 3, 7, 3)

# Single-transaction limit per KYC tier in NGN. Mirrors seeds/ref_kyc_tiers.csv.
TIER_LIMIT = {1: 50_000, 2: 100_000, 3: 5_000_000}

# CBN bank codes used as transfer counterparties. Mirrors seeds/ref_banks.csv.
COUNTERPARTY_BANKS = [
    "044", "023", "050", "070", "011", "214", "058", "030", "301", "082", "076",
    "101", "221", "068", "232", "100", "032", "033", "215", "035", "057", "103",
]

STATE_WEIGHTS = {
    "Lagos": 30, "FCT": 10, "Kano": 7, "Rivers": 6, "Oyo": 6, "Ogun": 5, "Kaduna": 4,
    "Anambra": 4, "Enugu": 3, "Delta": 3, "Edo": 3, "Imo": 2, "Abia": 2, "Kwara": 2,
    "Plateau": 2, "Osun": 2, "Ondo": 2, "Akwa Ibom": 2, "Cross River": 1, "Benue": 1,
    "Niger": 1, "Bauchi": 1, "Borno": 1, "Katsina": 1, "Sokoto": 1, "Ekiti": 1, "Kogi": 1,
    "Nasarawa": 1, "Gombe": 1, "Adamawa": 1, "Bayelsa": 1, "Ebonyi": 1, "Jigawa": 1,
    "Kebbi": 1, "Taraba": 1, "Yobe": 1, "Zamfara": 1,
}

NAMES = {
    "yoruba": (
        ["Adebayo", "Oluwaseun", "Funmilayo", "Temitope", "Olumide", "Abiodun", "Kehinde",
         "Taiwo", "Bukola", "Yetunde", "Tunde", "Folake", "Ayodele", "Damilola", "Opeyemi"],
        ["Adeyemi", "Ogunleye", "Balogun", "Adewale", "Oladipo", "Bakare", "Afolabi",
         "Oyelaran", "Adebisi", "Olatunji"],
    ),
    "igbo": (
        ["Chinedu", "Ngozi", "Chiamaka", "Emeka", "Obinna", "Ifeoma", "Uchenna", "Nnamdi",
         "Adaeze", "Chukwuemeka", "Ebuka", "Amarachi", "Kelechi", "Nkechi"],
        ["Okonkwo", "Eze", "Nwosu", "Okafor", "Obi", "Nwachukwu", "Okeke", "Uzoma",
         "Chukwu", "Onyeka"],
    ),
    "hausa": (
        ["Abubakar", "Aisha", "Musa", "Fatima", "Ibrahim", "Zainab", "Usman", "Hauwa",
         "Sani", "Maryam", "Bello", "Hadiza", "Yusuf", "Halima"],
        ["Abdullahi", "Mohammed", "Garba", "Suleiman", "Danjuma", "Lawal", "Aminu",
         "Yakubu", "Idris", "Shehu"],
    ),
    "south_south": (
        ["Ese", "Efe", "Osas", "Tamuno", "Ini", "Ekaette", "Tari", "Ovie", "Nengi", "Imade"],
        ["Etim", "Bassey", "Okon", "Edet", "Omoregie", "Igbinedion", "Briggs", "Ikpeba",
         "Amadi", "Ekanem"],
    ),
}

MOBILE_PREFIXES = [
    "0803", "0806", "0703", "0706", "0813", "0816", "0810", "0814", "0903", "0906",
    "0805", "0807", "0705", "0815", "0811", "0905", "0802", "0808", "0708", "0812",
    "0701", "0902", "0901", "0904", "0907", "0809", "0818", "0817", "0909", "0908",
]
EMAIL_DOMAINS = ["gmail.com"] * 6 + ["yahoo.com"] * 3 + ["outlook.com", "icloud.com"]
BUSINESS_SUFFIXES = ["Ventures", "Enterprises", "Global Concepts", "POS Hub", "Stores",
                     "Integrated Services", "& Sons", "Nig. Ltd"]
TERMINAL_MODELS = {"PAX A920": "PXA9", "PAX S90": "PXS9", "Topwise T1": "TPT1",
                   "Horizon K11": "HZK1", "Nexgo N5": "NXN5"}

CHANNEL_WEIGHTS = {"POS": 45, "TRANSFER": 30, "USSD": 10, "CARD": 5, "BILLS": 10}
SOURCE_SYSTEM = {"POS": "POS_SWITCH", "TRANSFER": "NIP_GATEWAY", "USSD": "USSD_AGGREGATOR",
                 "CARD": "CARD_PROCESSOR", "BILLS": "BILLS_HUB"}
# Relative transaction volume by hour of day (WAT).
HOURLY_WEIGHT = [1, 1, 1, 1, 1, 2, 4, 6, 8, 9, 10, 10, 10, 10, 10, 10, 9, 9, 8, 7, 5, 4, 3, 2]

CUSTOMER_FIELDS = ["customer_id", "first_name", "last_name", "phone_number", "email", "bvn",
                   "nin", "date_of_birth", "gender", "state_of_residence", "kyc_tier",
                   "onboarding_channel", "created_at", "updated_at", "_ingested_at"]
ACCOUNT_FIELDS = ["account_id", "customer_id", "account_number", "account_type", "currency",
                  "status", "opened_at", "closed_at", "_ingested_at"]
TERMINAL_FIELDS = ["terminal_id", "agent_id", "agent_name", "account_id", "serial_number",
                   "terminal_model", "state", "status", "activated_at", "_ingested_at"]
TXN_FIELDS = ["transaction_id", "session_id", "account_id", "terminal_id", "channel",
              "direction", "amount", "fee", "currency", "status", "counterparty_bank_code",
              "counterparty_account", "narration", "created_at", "settled_at",
              "source_system", "_ingested_at"]

E164_NG_MOBILE = re.compile(r"^\+234[789][01][0-9]{8}$")


# --------------------------------------------------------------------------- helpers

def nuban(bank_code: str, serial: str) -> str:
    """CBN NUBAN: 9-digit serial + check digit weighted over bank code and serial."""
    total = sum(int(d) * w for d, w in zip(bank_code + serial, NUBAN_WEIGHTS))
    return serial + str((10 - total % 10) % 10)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


class Picker:
    """Draws disjoint row indices so planted defects never overlap."""

    def __init__(self, rng: random.Random, n: int):
        self.available = list(range(n))
        rng.shuffle(self.available)

    def take(self, k: int, where=lambda i: True) -> list[int]:
        chosen, rest = [], []
        for i in self.available:
            (chosen if len(chosen) < k and where(i) else rest).append(i)
        if len(chosen) < k:
            raise RuntimeError(f"only {len(chosen)} eligible rows, wanted {k}")
        self.available = rest
        return chosen


class AnswerKey:
    def __init__(self):
        self.issues: list[dict] = []

    def plant(self, issue_id, dataset, title, root_cause, expected: dict[str, int],
              kind="defect"):
        self.issues.append({"issue_id": issue_id, "dataset": dataset, "title": title,
                            "simulated_root_cause": root_cause, "kind": kind,
                            "expected_failing_rows": expected})


# --------------------------------------------------------------------------- generator

class Generator:
    def __init__(self, seed: int, as_of: datetime, n_customers: int, n_transactions: int):
        self.rng = random.Random(seed)
        self.seed = seed
        self.as_of = as_of
        self.n_customers = n_customers
        self.n_transactions = n_transactions
        self.key = AnswerKey()
        self.used_ids: set[str] = set()

    # ---- small value generators

    def unique(self, make) -> str:
        while True:
            value = make()
            if value not in self.used_ids:
                self.used_ids.add(value)
                return value

    def diurnal_ts(self, start: datetime, end: datetime) -> datetime:
        span = int((end - start).total_seconds())
        while True:
            ts = start + timedelta(seconds=self.rng.randrange(span))
            if self.rng.random() * 10 < HOURLY_WEIGHT[ts.hour]:
                return ts

    def messy_state(self, state: str) -> str:
        """How onboarding apps actually spell states. Standardisable, so not a defect."""
        rng = self.rng
        if state == "FCT":
            return rng.choice(["FCT", "FCT", "Abuja", "F.C.T", "Federal Capital Territory"])
        r = rng.random()
        if r < 0.70:
            return state
        if r < 0.80:
            return state.upper()
        if r < 0.90:
            return f"{state} State"
        return state.lower()

    def messy_phone(self, local: str) -> str:
        r = self.rng.random()
        if r < 0.60:
            return local
        if r < 0.85:
            return "+234" + local[1:]
        if r < 0.95:
            return "234" + local[1:]
        return f"{local[:4]} {local[4:7]} {local[7:]}"

    # ---- customers

    def customers(self):
        rng, as_of = self.rng, self.as_of
        rows, meta = [], []
        bvns: set[str] = set()
        for i in range(1, self.n_customers + 1):
            group = rng.choices(list(NAMES), weights=[35, 30, 25, 10])[0]
            first, last = rng.choice(NAMES[group][0]), rng.choice(NAMES[group][1])
            tier = rng.choices([1, 2, 3], weights=[35, 40, 25])[0]
            state = rng.choices(list(STATE_WEIGHTS), weights=list(STATE_WEIGHTS.values()))[0]
            local = rng.choice(MOBILE_PREFIXES) + f"{rng.randrange(10**7):07d}"
            bvn = None
            if tier >= 2 or rng.random() < 0.5:
                while True:
                    bvn = "22" + f"{rng.randrange(10**9):09d}"
                    if bvn not in bvns:
                        bvns.add(bvn)
                        break
            created = as_of - timedelta(days=rng.randint(30, 1100), seconds=rng.randrange(86400))
            email = None
            if rng.random() > 0.12:
                email = f"{first}.{last}{rng.randrange(1, 999)}@{rng.choice(EMAIL_DOMAINS)}".lower()
            rows.append({
                "customer_id": f"CUS{i:07d}",
                "first_name": first,
                "last_name": last,
                "phone_number": self.messy_phone(local),
                "email": email,
                "bvn": bvn,
                "nin": f"{rng.randrange(10**11):011d}" if rng.random() < 0.7 else None,
                "date_of_birth": as_of.date() - timedelta(days=rng.randint(18 * 366, 70 * 365)),
                "gender": rng.choice(["M", "F"]),
                "state_of_residence": self.messy_state(state),
                "kyc_tier": tier,
                "onboarding_channel": rng.choices(["AGENT", "APP", "USSD", "WEB"], weights=[45, 35, 15, 5])[0],
                "created_at": created,
                "updated_at": created + timedelta(seconds=rng.randrange(int((as_of - created).total_seconds()))),
                "_ingested_at": as_of - timedelta(minutes=55),
            })
            meta.append({"state": state, "local_phone": local, "tier": tier})
        self.customer_rows, self.customer_meta = rows, meta

    def plant_customer_defects(self):
        rng, rows, key = self.rng, self.customer_rows, self.key
        pick = Picker(rng, len(rows))

        # Agents are tier-3 customers; keep them clean so terminal checks stay isolated.
        self.agent_idx = pick.take(320, lambda i: rows[i]["kyc_tier"] == 3)

        # Re-onboarding by a different agent creates a second CIF with the same BVN.
        dupes = []
        for n, i in enumerate(pick.take(60, lambda i: rows[i]["bvn"] is not None)):
            dupe = dict(rows[i])
            dupe["customer_id"] = f"CUS{len(rows) + n + 1:07d}"
            dupe["first_name"], dupe["last_name"] = dupe["first_name"].upper(), dupe["last_name"].upper()
            dupe["phone_number"] = self.messy_phone(self.customer_meta[i]["local_phone"])
            dupe["onboarding_channel"] = "AGENT"
            dupe["created_at"] = rows[i]["created_at"] + timedelta(days=rng.randint(20, 300))
            dupe["created_at"] = min(dupe["created_at"], self.as_of - timedelta(days=1))
            dupe["updated_at"] = dupe["created_at"]
            dupes.append(dupe)
        rows.extend(dupes)
        key.plant("PI-01", "customers", "Duplicate customer profiles sharing one BVN",
                  "Customer re-onboarded through a second agent; no BVN dedupe at onboarding",
                  {"DQ-CUS-005": 120})

        for i in pick.take(120, lambda i: rows[i]["kyc_tier"] >= 2):
            rows[i]["bvn"] = None
        key.plant("PI-02", "customers", "Tier 2/3 customers with no BVN",
                  "Tier upgraded by back-office override without BVN capture",
                  {"DQ-CUS-003": 120})

        for n, i in enumerate(pick.take(40, lambda i: rows[i]["bvn"] is not None)):
            bvn = rows[i]["bvn"]
            rows[i]["bvn"] = [bvn[:-1], f"{int(bvn):.8E}", bvn[:2] + "O" + bvn[3:]][n % 3]
        key.plant("PI-03", "customers", "Malformed BVNs (truncated, Excel scientific notation, letter O)",
                  "Bulk KYC remediation file round-tripped through Excel",
                  {"DQ-CUS-004": 40})

        for n, i in enumerate(pick.take(50)):
            local = self.customer_meta[i]["local_phone"]
            rows[i]["phone_number"] = [
                local[:-1],
                local + str(rng.randrange(10)),
                "01" + f"{rng.randrange(10**7):07d}",
                "+44 7" + f"{rng.randrange(10**9):09d}",
            ][n % 4]
        key.plant("PI-05", "customers", "Phone numbers that cannot be standardised to +234 mobile",
                  "Free-text phone field on agent onboarding form; no input mask",
                  {"DQ-CUS-006": 50})

        for i in pick.take(30):
            rows[i]["state_of_residence"] = rng.choice(["Lagoss", "N/A", "Ikeja", "Port Harcourt", "Unknown"])
        key.plant("PI-06", "customers", "State of residence not a Nigerian state (typos, cities, N/A)",
                  "Free-text state field; agents type the city or leave a placeholder",
                  {"DQ-CUS-008": 30})

        for n, i in enumerate(pick.take(25)):
            if n < 10:
                rows[i]["date_of_birth"] = date(1900, 1, 1)
            elif n < 18:
                rows[i]["date_of_birth"] = self.as_of.date() + timedelta(days=rng.randint(30, 2000))
            else:
                rows[i]["date_of_birth"] = self.as_of.date() - timedelta(days=rng.randint(5 * 365, 17 * 365))
        key.plant("PI-07", "customers", "Implausible date of birth (1900-01-01 placeholder, future, under 18)",
                  "Default date left in place when the DOB widget fails on low-end Android",
                  {"DQ-CUS-009": 25})

        for i in pick.take(20, lambda i: rows[i]["email"] is not None):
            first, last = rows[i]["first_name"].lower(), rows[i]["last_name"].lower()
            rows[i]["email"] = rng.choice([f"{first}.{last}@gmail", f"{first}{last}.gmail.com",
                                           f"{first}.{last}@@yahoo.com"])
        key.plant("PI-09", "customers", "Malformed email addresses",
                  "No email validation on the USSD/agent onboarding path",
                  {"DQ-CUS-011": 20})

        # Measured after all edits so the answer key matches the file exactly.
        missing_email = sum(r["email"] is None for r in rows)
        key.plant("PI-08", "customers", "Missing email (inside the 80% completeness tolerance)",
                  "Email is optional for USSD and agent onboarding",
                  {"DQ-CUS-010": missing_email}, kind="tolerated")
        raw_phone_nonconformant = sum(not E164_NG_MOBILE.match(r["phone_number"]) for r in rows)
        key.plant("PI-04", "customers", "Phone numbers not in E.164 at source (fixed by standardisation)",
                  "Each channel captures phone numbers in its own format",
                  {"DQ-CUS-007": raw_phone_nonconformant}, kind="standardisable")

    # ---- accounts

    def accounts(self):
        rng, as_of = self.rng, self.as_of
        serials: set[str] = set()

        def new_number(leading_zero=False):
            while True:
                serial = ("0" + f"{rng.randrange(10**8):08d}") if leading_zero else f"{rng.randrange(10**9):09d}"
                if serial not in serials:
                    serials.add(serial)
                    return nuban(HOME_BANK_CODE, serial)

        self.new_account_number = new_number
        rows, owner_tier = [], {}
        agent_ids = {self.customer_rows[i]["customer_id"] for i in self.agent_idx}
        seq = 0
        for c in self.customer_rows[: self.n_customers]:  # duplicate CIFs hold no accounts
            n_accounts = 1 if rng.random() < 0.75 else 2
            for _ in range(n_accounts):
                seq += 1
                opened = c["created_at"] + timedelta(days=rng.randint(0, 30))
                opened = min(opened, as_of - timedelta(days=2))
                status = rng.choices(["ACTIVE", "DORMANT", "FROZEN", "CLOSED"], weights=[88, 6, 2, 4])[0]
                closed = None
                if status == "CLOSED":
                    span = max(int((as_of - timedelta(days=3) - opened).total_seconds()), 3600)
                    closed = opened + timedelta(seconds=rng.randrange(span))
                acct_type = "SAVINGS" if c["kyc_tier"] == 1 else rng.choice(["SAVINGS", "CURRENT"])
                rows.append({
                    "account_id": f"ACC{seq:08d}", "customer_id": c["customer_id"],
                    "account_number": new_number(), "account_type": acct_type, "currency": "NGN",
                    "status": status, "opened_at": opened, "closed_at": closed,
                    "_ingested_at": as_of - timedelta(minutes=50),
                })
                owner_tier[f"ACC{seq:08d}"] = c["kyc_tier"]
        self.agent_account = {}
        for cid in sorted(agent_ids):
            seq += 1
            c = next(r for r in self.customer_rows if r["customer_id"] == cid)
            opened = min(c["created_at"] + timedelta(days=rng.randint(0, 30)), as_of - timedelta(days=90))
            rows.append({
                "account_id": f"ACC{seq:08d}", "customer_id": cid, "account_number": new_number(),
                "account_type": "BUSINESS", "currency": "NGN", "status": "ACTIVE",
                "opened_at": opened, "closed_at": None, "_ingested_at": as_of - timedelta(minutes=50),
            })
            owner_tier[f"ACC{seq:08d}"] = 3
            self.agent_account[cid] = f"ACC{seq:08d}"
        self.account_rows, self.account_tier = rows, owner_tier

    def plant_account_defects(self):
        rng, rows, key = self.rng, self.account_rows, self.key
        agent_accounts = set(self.agent_account.values())
        pick = Picker(rng, len(rows))
        not_agent = lambda i: rows[i]["account_id"] not in agent_accounts  # noqa: E731
        self.tainted_accounts: set[str] = set()

        for i in pick.take(30, not_agent):
            number = rows[i]["account_number"]
            rows[i]["account_number"] = number[:9] + str((int(number[9]) + rng.randint(1, 9)) % 10)
            self.tainted_accounts.add(rows[i]["account_id"])
        key.plant("PI-11", "accounts", "Account numbers failing the NUBAN check digit",
                  "Manual account capture during the 2024 core banking migration",
                  {"DQ-ACC-003": 30})

        for i in pick.take(10, not_agent):
            rows[i]["account_number"] = self.new_account_number(leading_zero=True)[1:]
            self.tainted_accounts.add(rows[i]["account_id"])
        key.plant("PI-12", "accounts", "Account numbers with the leading zero stripped (9 digits)",
                  "Extract opened and re-saved in Excel, which treats NUBANs as numbers",
                  {"DQ-ACC-003": 10})

        for i in pick.take(15, lambda i: rows[i]["status"] == "CLOSED"):
            rows[i]["closed_at"] = None
            self.tainted_accounts.add(rows[i]["account_id"])
        key.plant("PI-14", "accounts", "Closed accounts with no closure date",
                  "Closure performed by status override instead of the closure workflow",
                  {"DQ-ACC-004": 15})

        dupes = []
        for i in pick.take(40, not_agent):
            dupe = dict(rows[i])
            dupe["_ingested_at"] = rows[i]["_ingested_at"] + timedelta(minutes=5)
            dupes.append(dupe)
        key.plant("PI-13", "accounts", "Account rows ingested twice",
                  "CDC batch re-delivered after a connector timeout; loader is not idempotent",
                  {"DQ-ACC-001": 80})

        orphans = []
        for n in range(25):
            orphan = dict(rows[rng.randrange(len(rows))])
            orphan["account_id"] = f"ACC{len(rows) + n + 1:08d}"
            orphan["customer_id"] = f"CUS8{rng.randrange(10**6):06d}"
            orphan["account_number"] = self.new_account_number()
            orphan["account_type"], orphan["status"], orphan["closed_at"] = "SAVINGS", "ACTIVE", None
            orphans.append(orphan)
            self.tainted_accounts.add(orphan["account_id"])
        key.plant("PI-10", "accounts", "Accounts whose customer does not exist (orphans)",
                  "CIF records purged during migration while their accounts were kept",
                  {"DQ-ACC-002": 25})

        rows.extend(dupes)
        rows.extend(orphans)

    # ---- terminals

    def terminals(self):
        rng, as_of = self.rng, self.as_of
        snapshot_at = as_of - timedelta(hours=52)
        serials: set[str] = set()
        rows, agents = [], []
        for n, i in enumerate(self.agent_idx):
            c = self.customer_rows[i]
            name = rng.choice([c["first_name"], c["last_name"]])
            agents.append({
                "agent_id": f"AGT{n + 1:05d}", "agent_name": f"{name} {rng.choice(BUSINESS_SUFFIXES)}",
                "account_id": self.agent_account[c["customer_id"]],
                "state": self.customer_meta[i]["state"],
            })
        owners = agents + rng.sample(agents, 80)  # 80 agents run a second terminal
        for n, agent in enumerate(owners):
            model = rng.choice(list(TERMINAL_MODELS))
            while True:
                serial = TERMINAL_MODELS[model] + f"{rng.randrange(10**8):08d}"
                if serial not in serials:
                    serials.add(serial)
                    break
            rows.append({
                "terminal_id": f"2NR{n + 1:05d}", "agent_id": agent["agent_id"],
                "agent_name": agent["agent_name"], "account_id": agent["account_id"],
                "serial_number": serial, "terminal_model": model, "state": agent["state"],
                "status": "ACTIVE" if rng.random() < 0.95 else "INACTIVE",
                "activated_at": snapshot_at - timedelta(days=rng.randint(10, 700), seconds=rng.randrange(86400)),
                "_ingested_at": snapshot_at,
            })
        self.terminal_rows = rows
        # Activated after the registry snapshot, so they transact but are not in the extract.
        self.unregistered_terminals = [
            {"terminal_id": f"2NR{len(rows) + k + 1:05d}", "account_id": rng.choice(agents)["account_id"]}
            for k in range(5)
        ]

    def plant_terminal_defects(self):
        rng, rows, key = self.rng, self.terminal_rows, self.key
        pick = Picker(rng, len(rows))
        self.tainted_terminals: set[str] = set()
        for a, b in zip(*[iter(pick.take(16))] * 2):
            rows[b]["serial_number"] = rows[a]["serial_number"]
        key.plant("PI-15", "terminals", "Same device serial registered to two terminal IDs",
                  "Device swapped between agents without retiring the old terminal ID",
                  {"DQ-TRM-002": 16})

        for i in pick.take(6):
            rows[i]["account_id"] = f"ACC9{rng.randrange(10**7):07d}"
            self.tainted_terminals.add(rows[i]["terminal_id"])
        key.plant("PI-16", "terminals", "Terminals settling to an account that does not exist",
                  "Settlement account typed by hand in the terminal management system",
                  {"DQ-TRM-003": 6})
        key.plant("PI-17", "terminals", "Terminal registry extract is 52 hours old",
                  "TMS export job failing silently since the weekend",
                  {"DQ-TRM-005": 1})

    # ---- transactions

    def draw_amount(self, channel: str) -> tuple[float, str | None]:
        rng = self.rng
        if channel == "POS":
            return round(clamp(rng.lognormvariate(9.2, 0.8), 500, 200_000), -2), "POS cash withdrawal"
        if channel == "TRANSFER":
            return round(clamp(rng.lognormvariate(9.5, 1.3), 100, 2_000_000), 2), None
        if channel == "USSD":
            return round(clamp(rng.lognormvariate(8.3, 1.0), 100, 100_000), 2), "USSD *990# transfer"
        if channel == "CARD":
            return round(clamp(rng.lognormvariate(9.0, 1.0), 200, 500_000), 2), "Card purchase - online"
        bill = rng.choice(["airtime", "power", "tv", "data"])
        if bill == "airtime":
            return float(rng.choice([100, 200, 500, 1000, 2000, 5000])), "Airtime top-up"
        if bill == "power":
            return float(rng.randrange(20, 500) * 100), "Electricity token (prepaid)"
        if bill == "tv":
            return float(rng.choice([4200, 7900, 12500, 18400, 29500])), "Cable TV subscription"
        return float(rng.choice([350, 1000, 2500, 5000, 10000])), "Data bundle"

    @staticmethod
    def fee_for(channel, direction, amount, status):
        if status == "FAILED":
            return 0.0
        if channel == "POS":
            return min(round(amount * 0.005, 2), 100.0)
        if channel == "TRANSFER" and direction == "DR":
            return 10.0 if amount <= 5_000 else 25.0 if amount <= 50_000 else 50.0
        if channel == "USSD":
            return 6.98
        return 0.0

    def new_txn_id(self):
        return self.unique(lambda: f"TRX{self.rng.getrandbits(48):012X}")

    def new_session_id(self, created: datetime):
        return self.unique(lambda: NIP_INSTITUTION_CODE + created.strftime("%y%m%d%H%M%S")
                           + f"{self.rng.randrange(10**12):012d}")

    def make_txn(self, channel, created, account_id, tier, terminal_id=None, status=None,
                 direction=None):
        rng = self.rng
        amount, narration = self.draw_amount(channel)
        limit = TIER_LIMIT[tier]
        if amount > limit:
            amount = round(limit * rng.uniform(0.3, 0.95), -2 if channel == "POS" else 2)
        direction = direction or ("CR" if channel == "POS" else
                                  "DR" if channel != "TRANSFER" or rng.random() < 0.7 else "CR")
        status = status or rng.choices(["SUCCESSFUL", "FAILED", "PENDING", "REVERSED"],
                                       weights=[92, 6, 1, 1])[0]
        session_id = counterparty_bank = counterparty_account = None
        if channel == "TRANSFER":
            session_id = self.new_session_id(created)
            counterparty_bank = rng.choice(COUNTERPARTY_BANKS)
            counterparty_account = nuban(counterparty_bank, f"{rng.randrange(10**9):09d}")
            first = rng.choice(rng.choice(list(NAMES.values()))[0])
            narration = f"Transfer {'to' if direction == 'DR' else 'from'} {first}"
        settle_lag = {"POS": (5, 120), "TRANSFER": (1, 30)}.get(channel, (5, 600))
        settled = (created + timedelta(seconds=rng.randint(*settle_lag))
                   if status in ("SUCCESSFUL", "REVERSED") else None)
        return {
            "transaction_id": self.new_txn_id(), "session_id": session_id,
            "account_id": account_id, "terminal_id": terminal_id, "channel": channel,
            "direction": direction, "amount": amount,
            "fee": self.fee_for(channel, direction, amount, status), "currency": "NGN",
            "status": status, "counterparty_bank_code": counterparty_bank,
            "counterparty_account": counterparty_account, "narration": narration,
            "created_at": created, "settled_at": settled, "source_system": SOURCE_SYSTEM[channel],
            "_ingested_at": min(created + timedelta(seconds=rng.randint(20, 300)), self.as_of),
        }

    def transactions(self):
        rng, as_of = self.rng, self.as_of
        start = as_of - timedelta(days=30)
        ussd_cutoff = as_of - timedelta(hours=30)  # the USSD aggregator feed died here
        live_terminals = [t for t in self.terminal_rows
                          if t["status"] == "ACTIVE" and t["terminal_id"] not in self.tainted_terminals]
        customer_accounts = [
            (a["account_id"], self.account_tier[a["account_id"]])
            for a in self.account_rows
            if a["status"] == "ACTIVE" and a["account_type"] != "BUSINESS"
            and a["account_id"] not in self.tainted_accounts
        ]
        customer_accounts = list(dict.fromkeys(customer_accounts))  # drop double-ingested copies

        def one(channel, created):
            if channel == "POS":
                t = rng.choice(live_terminals)
                return self.make_txn("POS", created, t["account_id"], 3, terminal_id=t["terminal_id"])
            account_id, tier = rng.choice(customer_accounts)
            return self.make_txn(channel, created, account_id, tier)

        rows = []
        for _ in range(self.n_transactions):
            channel = rng.choices(list(CHANNEL_WEIGHTS), weights=list(CHANNEL_WEIGHTS.values()))[0]
            end = ussd_cutoff if channel == "USSD" else as_of - timedelta(minutes=1)
            rows.append(one(channel, self.diurnal_ts(start, end)))
        for channel in ("POS", "TRANSFER", "CARD", "BILLS"):  # every live feed has recent traffic
            for _ in range(3):
                rows.append(one(channel, as_of - timedelta(minutes=rng.randint(2, 55))))
        self.txn_rows = rows
        self.closed_accounts = [a for a in self.account_rows
                                if a["status"] == "CLOSED" and a["closed_at"] is not None
                                and a["account_id"] not in self.tainted_accounts]

    def plant_transaction_defects(self):
        rng, rows, key, as_of = self.rng, self.txn_rows, self.key, self.as_of
        pick = Picker(rng, len(rows))
        not_transfer = lambda i: rows[i]["channel"] != "TRANSFER"  # noqa: E731
        appended = []

        for i in pick.take(200, not_transfer):
            dupe = dict(rows[i])
            dupe["_ingested_at"] = min(rows[i]["_ingested_at"] + timedelta(minutes=rng.randint(2, 15)), as_of)
            appended.append(dupe)
        key.plant("PI-18", "transactions", "Transactions ingested twice (identical payload)",
                  "Switch webhook retried after a 504; the consumer does not dedupe on transaction_id",
                  {"DQ-TXN-021": 400, "DQ-TXN-002": 400})

        for i in pick.take(150, lambda i: not_transfer(i) and rows[i]["status"] == "SUCCESSFUL"):
            pending = dict(rows[i])
            pending["status"], pending["settled_at"] = "PENDING", None
            pending["_ingested_at"] = rows[i]["created_at"] + timedelta(seconds=3)
            appended.append(pending)
        key.plant("PI-19", "transactions", "Same transaction_id seen as PENDING then SUCCESSFUL",
                  "Feed is change-data-capture, not a snapshot: status updates arrive as new rows",
                  {"DQ-TXN-002": 300}, kind="expected_behaviour")

        for i in pick.take(25, lambda i: rows[i]["channel"] == "TRANSFER" and rows[i]["direction"] == "DR"
                           and rows[i]["status"] == "SUCCESSFUL"):
            leg = dict(rows[i])
            leg["transaction_id"] = self.new_txn_id()
            leg["created_at"] = rows[i]["created_at"] + timedelta(seconds=rng.randint(2, 20))
            leg["settled_at"] = leg["created_at"] + timedelta(seconds=rng.randint(1, 30))
            leg["_ingested_at"] = min(leg["created_at"] + timedelta(seconds=rng.randint(20, 300)), as_of)
            appended.append(leg)
        key.plant("PI-20", "transactions", "Same NIP session posted twice under two transaction IDs",
                  "Mobile app retried a timed-out transfer; the ledger accepted both legs (customer debited twice)",
                  {"DQ-TXN-012": 50})

        for i in pick.take(40):
            rows[i]["amount"] = None
        key.plant("PI-21", "transactions", "Transactions with no amount",
                  "Processor sends amount as null on some reversal advices",
                  {"DQ-TXN-003": 40})

        for n, i in enumerate(pick.take(30)):
            rows[i]["amount"] = 0.0 if n < 15 else -rows[i]["amount"]
        key.plant("PI-22", "transactions", "Zero or negative amounts",
                  "Reversals sent as signed amounts instead of direction = CR",
                  {"DQ-TXN-004": 30})

        def kobo_candidate(i):
            r = rows[i]
            return (r["channel"] == "USSD" and self.account_tier.get(r["account_id"]) in (1, 2)
                    and r["amount"] >= 1500)
        for i in pick.take(80, kobo_candidate):
            rows[i]["amount"] = round(rows[i]["amount"] * 100, 2)
        key.plant("PI-23", "transactions", "USSD amounts reported in kobo instead of naira (100x)",
                  "USSD aggregator changed its API to minor units without notice",
                  {"DQ-TXN-016": 80})

        for i in pick.take(500, lambda i: rows[i]["status"] == "SUCCESSFUL"):
            rows[i]["status"] = rng.choice(["successful", "Success", "SUCCESS"])
        for n, i in enumerate(pick.take(40)):
            rows[i]["status"] = "UNKNOWN" if n % 2 else "99"
        key.plant("PI-24", "transactions", "Status values in non-canonical case/spelling (fixed by standardisation)",
                  "Each processor has its own status vocabulary",
                  {"DQ-TXN-006": 500}, kind="standardisable")
        key.plant("PI-25", "transactions", "Unrecognised status values ('UNKNOWN', raw response code '99')",
                  "Processor response codes passed through without mapping",
                  {"DQ-TXN-005": 40, "DQ-TXN-006": 40})

        for i in pick.take(60, not_transfer):
            rows[i]["account_id"] = f"ACC9{rng.randrange(10**7):07d}"
        key.plant("PI-26", "transactions", "Transactions on accounts that do not exist",
                  "Wallet IDs from a decommissioned ledger still routed by the bills hub",
                  {"DQ-TXN-008": 60})

        for _ in range(45):
            t = rng.choice(self.unregistered_terminals)
            created = self.diurnal_ts(as_of - timedelta(hours=40), as_of - timedelta(minutes=5))
            appended.append(self.make_txn("POS", created, t["account_id"], 3,
                                          terminal_id=t["terminal_id"], status="SUCCESSFUL"))
        key.plant("PI-27", "transactions", "POS transactions from terminals missing in the registry",
                  "Symptom of PI-17: terminals activated after the stale registry snapshot",
                  {"DQ-TXN-009": 45})

        for i in pick.take(35, lambda i: rows[i]["channel"] == "POS"):
            rows[i]["terminal_id"] = None
        key.plant("PI-28", "transactions", "POS transactions with no terminal ID",
                  "Older terminal firmware omits field 41 (terminal ID) on fallback transactions",
                  {"DQ-TXN-010": 35})

        for n, i in enumerate(pick.take(20, lambda i: rows[i]["channel"] == "POS")):
            r = rows[i]
            r["created_at"] = (datetime(1970, 1, 1, 0, rng.randrange(60), rng.randrange(60)) if n < 10
                               else as_of + timedelta(days=rng.randint(30, 400), seconds=rng.randrange(86400)))
            if r["settled_at"] is not None:
                r["settled_at"] = r["created_at"] + timedelta(seconds=60)
        key.plant("PI-29", "transactions", "POS timestamps from 1970 or the future",
                  "Terminal real-time clock reset (flat RTC battery) or set by hand",
                  {"DQ-TXN-011": 20})

        for i in pick.take(30, lambda i: rows[i]["settled_at"] is not None):
            rows[i]["settled_at"] -= timedelta(hours=1)
        key.plant("PI-30", "transactions", "Settled before it was created",
                  "Settlement service writes UTC while the switch writes WAT (UTC+1)",
                  {"DQ-TXN-014": 30})

        for i in pick.take(20, lambda i: (rows[i]["fee"] or 0) > 0 and rows[i]["amount"] is not None
                           and 0 < rows[i]["amount"] < rows[i]["fee"] * 100):
            rows[i]["fee"] = round(rows[i]["fee"] * 100, 2)
        key.plant("PI-31", "transactions", "Fee larger than the transaction amount",
                  "Fee posted in kobo by the pricing engine",
                  {"DQ-TXN-015": 20})

        for n, i in enumerate(pick.take(40, lambda i: rows[i]["channel"] == "TRANSFER")):
            rows[i]["counterparty_bank_code"] = ["58", "000", "0X4"][n % 3]
        key.plant("PI-32", "transactions", "Transfers with an unknown counterparty bank code",
                  "Leading zero stripped ('58' for GTBank '058') and placeholder codes on manual transfers",
                  {"DQ-TXN-013": 40})

        key.plant("PI-33", "transactions", "USSD feed silent for 30 hours",
                  "USSD aggregator SFTP credentials expired; table-level freshness still looks healthy",
                  {"DQ-TXN-019": 1})

        for _ in range(15):
            a = rng.choice(self.closed_accounts)
            span = int((as_of - timedelta(hours=1) - a["closed_at"]).total_seconds())
            created = a["closed_at"] + timedelta(seconds=rng.randrange(3600, span))
            appended.append(self.make_txn("CARD", created, a["account_id"], self.account_tier[a["account_id"]],
                                          status="SUCCESSFUL", direction="DR"))
        key.plant("PI-34", "transactions", "Successful debits on accounts after they were closed",
                  "Card not hot-listed when the account was closed",
                  {"DQ-TXN-017": 15})

        rows.extend(appended)
        rng.shuffle(rows)
        key.plant("PI-35", "transactions", "Transactions file has fewer rows than its control total",
                  "Extract truncated mid-transfer; the loader does not check the control file",
                  {"DQ-TXN-022": 1})

    # ---- output

    def write(self, out_dir: Path, key_dir: Path):
        out_dir.mkdir(parents=True, exist_ok=True)
        key_dir.mkdir(parents=True, exist_ok=True)

        def fmt(v):
            if v is None:
                return ""
            if isinstance(v, datetime):
                return v.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(v, date):
                return v.isoformat()
            if isinstance(v, float):
                return f"{v:.2f}"
            return str(v)

        feeds = {
            "customers": (CUSTOMER_FIELDS, self.customer_rows),
            "accounts": (ACCOUNT_FIELDS, self.account_rows),
            "terminals": (TERMINAL_FIELDS, self.terminal_rows),
            "transactions": (TXN_FIELDS, self.txn_rows),
        }
        for name, (fields, rows) in feeds.items():
            with open(out_dir / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(fields)
                w.writerows([fmt(r[c]) for c in fields] for r in rows)

        truncated_rows = 150
        with open(out_dir / "batch_control.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["dataset", "file_name", "record_count", "extracted_at"])
            for name, (_, rows) in feeds.items():
                declared = len(rows) + (truncated_rows if name == "transactions" else 0)
                w.writerow([name, f"{name}.csv", declared, fmt(self.as_of)])

        answer_key = {
            "seed": self.seed,
            "as_of": fmt(self.as_of),
            "row_counts": {name: len(rows) for name, (_, rows) in feeds.items()},
            "issues": sorted(self.key.issues, key=lambda x: x["issue_id"]),
        }
        (key_dir / "planted_issues.json").write_text(json.dumps(answer_key, indent=2), encoding="utf-8")
        return answer_key

    def run(self, out_dir: Path, key_dir: Path):
        self.customers()
        self.plant_customer_defects()
        self.accounts()
        self.plant_account_defects()
        self.terminals()
        self.plant_terminal_defects()
        self.transactions()
        self.plant_transaction_defects()
        return self.write(out_dir, key_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--as-of", help="batch timestamp in WAT, 'YYYY-MM-DD HH:MM' (default: now)")
    parser.add_argument("--customers", type=int, default=5000)
    parser.add_argument("--transactions", type=int, default=60000)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--answer-key", type=Path, default=ROOT / "data" / "answer_key")
    args = parser.parse_args()

    as_of = (datetime.strptime(args.as_of, "%Y-%m-%d %H:%M") if args.as_of
             else datetime.now(WAT).replace(tzinfo=None, second=0, microsecond=0))
    key = Generator(args.seed, as_of, args.customers, args.transactions).run(args.out, args.answer_key)
    counts = ", ".join(f"{k}={v:,}" for k, v in key["row_counts"].items())
    print(f"as_of {key['as_of']} WAT | {counts} | {len(key['issues'])} planted issues")


if __name__ == "__main__":
    main()
