#!/usr/bin/env python
"""Publish DQ rule results from dbt artifacts into the warehouse.

A dbt test reports how many rows failed. A scorecard also needs how many rows
were checked, so for every rule (a test with meta.rule_id) this script:

  1. reads the rule's catalogue entry from target/manifest.json,
  2. reads its outcome and failing-row count from target/run_results.json,
  3. counts the rows in scope in the tested model (honouring config.where),
  4. pulls sample keys and the naira value of failing rows from the stored failures,

and appends one row per rule to dq_audit.rule_results. Every other test (silver
contracts, seed checks) is appended to dq_audit.contract_results. The gold DQ
models are built from these two tables.

Run it straight after `dbt build`, before anything overwrites target/.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "warehouse" / "ng_fintech_dq.duckdb"
TARGET = ROOT / "target"

DEFAULT_KEY = {"customers": "customer_id", "accounts": "account_id",
               "terminals": "terminal_id", "transactions": "transaction_id"}
# Tests that ignore nulls in the tested column, so nulls are not in their denominator.
NULLS_EXCLUDED = {"dq_unique", "dq_accepted_values", "dq_matches_regex",
                  "dq_relationships", "dq_valid_nuban"}
REQUIRED_META = ("rule_id", "rule_name", "dimension", "dataset", "severity", "action", "owner")

RULE_COLUMNS = {
    "run_id": "varchar", "published_at": "timestamp", "batch_as_of": "timestamp",
    "rule_id": "varchar", "rule_name": "varchar", "dimension": "varchar", "dataset": "varchar",
    "severity": "varchar", "action": "varchar", "scored": "boolean", "threshold": "double",
    "owner": "varchar", "why": "varchar", "test_name": "varchar", "test_type": "varchar",
    "model_name": "varchar", "column_name": "varchar", "where_clause": "varchar",
    "rows_checked": "bigint", "rows_failed": "bigint", "dbt_status": "varchar",
    "value_affected_ngn": "double", "sample_keys": "varchar", "failures_relation": "varchar",
}
CONTRACT_COLUMNS = {
    "run_id": "varchar", "published_at": "timestamp", "test_name": "varchar",
    "test_type": "varchar", "model_name": "varchar", "column_name": "varchar",
    "dbt_status": "varchar", "failures": "bigint",
}


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def relation_columns(con, relation: str) -> set[str]:
    return {row[0] for row in con.execute(f"describe {relation}").fetchall()}


def rule_row(con, node, result, manifest, run_id, published_at, batch_as_of):
    meta = node["config"].get("meta") or {}
    missing = [k for k in REQUIRED_META if k not in meta]
    if missing:
        raise SystemExit(f"{node['name']}: meta is missing {missing}")

    model = manifest["nodes"][node["attached_node"]]
    column = node.get("column_name")
    test_type = node["test_metadata"]["name"]
    where = node["config"].get("where")

    filters = [f"({where})"] if where else []
    if column and test_type in NULLS_EXCLUDED:
        filters.append(f"{column} is not null")
    where_sql = f" where {' and '.join(filters)}" if filters else ""
    rows_checked = scalar(con, f"select count(*) from {model['relation_name']}{where_sql}")

    rows_failed = result.get("failures") or 0
    failures_relation = node.get("relation_name")
    sample_keys, value_affected = None, None
    if rows_failed and failures_relation:
        cols = relation_columns(con, failures_relation)
        key = meta.get("key") or DEFAULT_KEY.get(meta["dataset"])
        if key in cols:
            keys = con.execute(f"select distinct cast({key} as varchar) as k from {failures_relation} "
                               f"where {key} is not null order by k limit 5").fetchall()
            sample_keys = ", ".join(k for (k,) in keys)
        if "amount" in cols:
            value_affected = scalar(con, f"select sum(abs(try_cast(amount as double))) from {failures_relation}")

    return {
        "run_id": run_id, "published_at": published_at, "batch_as_of": batch_as_of,
        "rule_id": meta["rule_id"], "rule_name": meta["rule_name"], "dimension": meta["dimension"],
        "dataset": meta["dataset"], "severity": meta["severity"], "action": meta["action"],
        "scored": bool(meta.get("scored", True)), "threshold": float(meta.get("threshold", 1.0)),
        "owner": meta["owner"], "why": meta.get("why"), "test_name": node["name"],
        "test_type": test_type, "model_name": model["name"], "column_name": column,
        "where_clause": where, "rows_checked": rows_checked, "rows_failed": rows_failed,
        "dbt_status": result["status"], "value_affected_ngn": value_affected,
        "sample_keys": sample_keys, "failures_relation": failures_relation,
    }


def ensure_table(con, name, columns):
    cols = ", ".join(f"{c} {t}" for c, t in columns.items())
    con.execute(f"create table if not exists dq_audit.{name} ({cols})")


def insert(con, name, columns, rows):
    if not rows:
        return
    placeholders = ", ".join("?" for _ in columns)
    con.executemany(f"insert into dq_audit.{name} ({', '.join(columns)}) values ({placeholders})",
                    [[r[c] for c in columns] for r in rows])


def main():
    manifest = json.loads((TARGET / "manifest.json").read_text(encoding="utf-8"))
    run_results = json.loads((TARGET / "run_results.json").read_text(encoding="utf-8"))
    run_id = run_results["metadata"]["invocation_id"]
    published_at = datetime.now(timezone.utc).replace(tzinfo=None)

    test_results = {r["unique_id"]: r for r in run_results["results"]
                    if r["unique_id"].startswith("test.")}
    if not test_results:
        sys.exit("run_results.json has no test results: run `dbt build` first.")

    con = duckdb.connect(str(WAREHOUSE))
    batch_as_of = scalar(con, "select max(try_cast(extracted_at as timestamp)) from bronze.brz_batch_control")

    rules, contracts, seen_rule_ids = [], [], set()
    for uid, result in sorted(test_results.items()):
        node = manifest["nodes"][uid]
        meta = node["config"].get("meta") or {}
        if "rule_id" in meta:
            if meta["rule_id"] in seen_rule_ids:
                sys.exit(f"duplicate rule_id {meta['rule_id']} ({node['name']})")
            seen_rule_ids.add(meta["rule_id"])
            rules.append(rule_row(con, node, result, manifest, run_id, published_at, batch_as_of))
        else:
            attached = manifest["nodes"].get(node.get("attached_node") or "", {})
            contracts.append({
                "run_id": run_id, "published_at": published_at, "test_name": node["name"],
                "test_type": (node.get("test_metadata") or {}).get("name", "singular"),
                "model_name": attached.get("name"), "column_name": node.get("column_name"),
                "dbt_status": result["status"], "failures": result.get("failures") or 0,
            })

    con.execute("create schema if not exists dq_audit")
    ensure_table(con, "rule_results", RULE_COLUMNS)
    ensure_table(con, "contract_results", CONTRACT_COLUMNS)
    for table in ("rule_results", "contract_results"):
        con.execute(f"delete from dq_audit.{table} where run_id = ?", [run_id])
    insert(con, "rule_results", RULE_COLUMNS, rules)
    insert(con, "contract_results", CONTRACT_COLUMNS, contracts)
    con.close()

    breached = sum(r["rows_failed"] > 0 for r in rules)
    contract_fails = sum(c["dbt_status"] not in ("pass",) for c in contracts)
    print(f"run {run_id}: {len(rules)} rules published ({breached} with failing rows), "
          f"{len(contracts)} contract tests ({contract_fails} not passing)")


if __name__ == "__main__":
    main()
