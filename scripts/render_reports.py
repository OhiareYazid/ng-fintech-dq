#!/usr/bin/env python
"""Render the DQ scorecard, issue log and rule library from the warehouse.

Inputs: the gold DQ models, the triage register (dq/issue_triage.yml), the dbt
manifest (each rule's check logic) and, when present, the generator's answer
key (to prove which planted defects were caught).

Outputs:
  reports/dq_scorecard.md        scorecard by dimension and table, breaches, containment, coverage
  reports/scorecard_heatmap.svg  table x dimension heatmap used in the README
  reports/issue_log.md / .csv    detected issues joined to their triage
  reports/rule_results.csv       latest result of every rule
  docs/rule_library.md           the rule catalogue, generated from the dbt project
  reports/rule_library.csv
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from html import escape
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "warehouse" / "ng_fintech_dq.duckdb"
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs"
ANSWER_KEY = ROOT / "data" / "answer_key" / "planted_issues.json"

DATASETS = ["customers", "accounts", "terminals", "transactions"]
DIMENSIONS = ["completeness", "validity", "uniqueness", "referential_integrity", "consistency", "freshness"]
DIMENSION_LABEL = {"completeness": "Completeness", "validity": "Validity", "uniqueness": "Uniqueness",
                   "referential_integrity": "Ref. integrity", "consistency": "Consistency",
                   "freshness": "Freshness", "ALL": "Overall"}
DATASET_LABEL = {"customers": "Customers", "accounts": "Accounts", "terminals": "Terminals",
                 "transactions": "Transactions", "ALL": "All tables"}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
PRIORITY_ORDER = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
RAG_ICON = {"GREEN": "🟢", "AMBER": "🟠", "RED": "🔴"}

# Status palette (fixed, never themed) and chart chrome for the light surface.
STATUS_COLOR = {"GREEN": "#0ca30c", "AMBER": "#fab219", "RED": "#d03b3b"}
SURFACE, INK, MUTED, RULE_LINE = "#fcfcfb", "#1f1f1e", "#6b6b67", "#e4e4e0"


# --------------------------------------------------------------------------- helpers

def query(con, sql, params=None):
    cur = con.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def pct(x, digits=1):
    return "—" if x is None else f"{float(x) * 100:.{digits}f}%"


def score(x):
    """Scores are floored, so 99.96% never displays as 100.0% next to a RED badge."""
    return "—" if x is None else f"{math.floor(float(x) * 1000) / 10:.1f}%"


def ngn(x):
    return "—" if x is None else f"₦{float(x):,.0f}"


def num(x):
    return f"{int(x or 0):,}"


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def blend(hex_color, alpha):
    """hex_color at `alpha` over the chart surface, as an opaque hex."""
    fg = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    bg = [int(SURFACE[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a * alpha + b * (1 - alpha)):02x}" for a, b in zip(fg, bg))


def rule_logic(node):
    meta, kwargs = node["test_metadata"]["name"], node["test_metadata"]["kwargs"]
    col = node.get("column_name")
    strip_ref = lambda s: re.sub(r"ref\('([^']+)'\)", r"\1", s)  # noqa: E731
    text = {
        "dq_not_null": lambda: f"`{col}` is not null",
        "dq_unique": lambda: f"`{col}` is unique",
        "dq_accepted_values": lambda: f"`{col}` in ({', '.join(map(str, kwargs.get('values', [])))})",
        "dq_matches_regex": lambda: f"`{col}` matches `{kwargs.get('pattern')}`",
        "dq_relationships": lambda: f"`{col}` exists in `{strip_ref(kwargs.get('to', ''))}.{kwargs.get('field')}`",
        "dq_valid_nuban": lambda: f"`{col}` is a 10-digit NUBAN with a valid CBN check digit",
        "dq_expression_is_true": lambda: f"`{kwargs.get('expression')}`",
    }.get(meta, lambda: meta)()
    where = node["config"].get("where")
    return f"{text} where `{where}`" if where else text


# --------------------------------------------------------------------------- data

def load(con):
    data = {
        "rules": query(con, "select * from gold.gold_dq_rule_results"),
        "scorecard": query(con, "select * from gold.gold_dq_scorecard"),
        "trend": query(con, "select * from gold.gold_dq_score_trend order by published_at desc limit 10"),
        "contracts": query(con, "select * from gold.gold_dq_contract_results"),
        "first_seen": {r["rule_id"]: r["first_seen"] for r in query(con, """
            select rule_id, min(batch_as_of) as first_seen
            from gold.gold_dq_rule_results_history where rows_failed > 0 group by rule_id""")},
    }
    data["containment"] = query(con, """
        select
            (select try_cast(record_count as bigint) from bronze.brz_batch_control
              where dataset = 'transactions')                                       as declared,
            (select count(*) from silver.stg_transactions)                          as received,
            (select count(*) - count(distinct _row_hash) from silver.stg_transactions) as exact_duplicates,
            (select count(*) - count(distinct transaction_id) from silver.stg_transactions) as all_duplicates,
            (select count(*) from silver.slv_transactions_quarantine)               as quarantined,
            (select sum(abs(amount)) from silver.slv_transactions_quarantine)       as quarantined_value,
            (select count(*) from silver.slv_transactions where dq_flags <> '')     as flagged,
            (select count(*) from silver.slv_transactions)                          as clean,
            (select sum(amount) filter (where status = 'SUCCESSFUL')
               from silver.slv_transactions)                                        as clean_value,
            (select sum(amount) filter (where status = 'SUCCESSFUL' and channel = 'USSD')
               from silver.slv_transactions)                                        as ussd_clean_value,
            (select sum(amount) filter (where status = 'SUCCESSFUL')
               from silver.slv_transactions_quarantine
              where quarantine_reasons like '%DQ-TXN-016%')                         as kobo_value_as_received,
            (select sum(amount) from silver.slv_transactions_quarantine
              where quarantine_reasons like '%DQ-TXN-012%')                         as double_debit_value,
            (select count(*) from silver.slv_transactions_quarantine
              where quarantine_reasons like '%DQ-TXN-012%')                         as double_debits
    """)[0]
    data["quarantine_by_rule"] = query(con, """
        select reason as rule_id, count(*) as rows, sum(abs(amount)) as value_ngn
        from silver.slv_transactions_quarantine,
             unnest(string_split(quarantine_reasons, ',')) as t(reason)
        group by 1 order by 2 desc""")
    data["flags_by_rule"] = query(con, """
        select reason as rule_id, count(*) as rows
        from silver.slv_transactions, unnest(string_split(dq_flags, ',')) as t(reason)
        where dq_flags <> '' group by 1 order by 2 desc""")
    return data


def load_rule_nodes():
    manifest = json.loads((ROOT / "target" / "manifest.json").read_text(encoding="utf-8"))
    nodes = {}
    for node in manifest["nodes"].values():
        rule_id = (node.get("config", {}).get("meta") or {}).get("rule_id")
        if node["resource_type"] == "test" and rule_id:
            nodes[rule_id] = node
    return nodes


# --------------------------------------------------------------------------- issue log

def build_issue_log(data):
    triage = yaml.safe_load((ROOT / "dq" / "issue_triage.yml").read_text(encoding="utf-8"))["issues"]
    by_rule = {r["rule_id"]: r for r in data["rules"]}
    triaged_rules = {rule for issue in triage for rule in issue["rules"]}

    log = []
    for issue in triage:
        results = [by_rule[r] for r in issue["rules"] if r in by_rule]
        failing = [r for r in results if r["rows_failed"] > 0]
        log.append({**issue, "results": results, "failing": failing,
                    "status": issue["status"] if failing else "READY_TO_CLOSE"})

    for rule in data["rules"]:
        if rule["rule_status"] == "BREACH" and rule["scored"] and rule["rule_id"] not in triaged_rules:
            log.append({
                "issue_id": f"NEW-{rule['rule_id']}", "title": rule["rule_name"], "rules": [rule["rule_id"]],
                "priority": "P2" if rule["severity"] in ("critical", "high") else "P3",
                "status": "NEW", "owner": rule["owner"], "root_cause": "Untriaged.",
                "impact": rule["why"], "remediation": "", "prevention": "", "related": [],
                "results": [rule], "failing": [rule],
            })

    for entry in log:
        failing = entry["failing"] or entry["results"]
        entry["datasets"] = sorted({r["dataset"] for r in entry["results"]})
        entry["dimensions"] = sorted({r["dimension"] for r in entry["results"]})
        entry["severity"] = min((r["severity"] for r in entry["results"]), key=SEVERITY_ORDER.get, default="")
        entry["rows_summary"] = "; ".join(f"{r['rule_id']}: {num(r['rows_failed'])} of {num(r['rows_checked'])}"
                                          for r in entry["results"])
        values = [r["value_affected_ngn"] for r in entry["results"] if r["value_affected_ngn"]]
        entry["value"] = max(values) if values else None  # rules in one issue overlap, so never sum
        seen = [data["first_seen"].get(r["rule_id"]) for r in entry["results"]]
        seen = [s for s in seen if s]
        entry["first_detected"] = min(seen).strftime("%Y-%m-%d") if seen else ""
        entry["sample_keys"] = next((r["sample_keys"] for r in failing if r["sample_keys"]), "")
    log.sort(key=lambda e: (PRIORITY_ORDER.get(e["priority"], 9), e["issue_id"]))
    return log


def render_issue_log(log, data):
    rules = data["rules"]
    run_id, batch = rules[0]["run_id"], rules[0]["batch_as_of"]
    open_states = {"NEW", "OPEN", "IN_REMEDIATION"}
    counts = defaultdict(int)
    for e in log:
        if e["status"] in open_states:
            counts[e["priority"]] += 1

    lines = [
        "# DQ issue log",
        "",
        f"Batch as of **{batch:%Y-%m-%d %H:%M} WAT** · run `{run_id[:8]}` · "
        f"{len(log)} issues, open by priority: " + ", ".join(f"{p} **{counts[p]}**" for p in ("P1", "P2", "P3", "P4")),
        "",
        "Detection fields (rules, failing rows, value, sample keys, first detected) are written by the pipeline. "
        "Triage fields (priority, owner, status, root cause, impact, remediation, prevention) come from "
        "[`dq/issue_triage.yml`](../dq/issue_triage.yml). Priority and status definitions are in "
        "[the DQ framework](../docs/dq_framework.md#issue-management).",
        "",
        md_table(
            ["Issue", "Priority", "Status", "Title", "Owner", "Failing rows", "Value affected"],
            [[f"[{e['issue_id']}](#{e['issue_id'].lower()})", e["priority"], e["status"], e["title"], e["owner"],
              e["rows_summary"], ngn(e["value"])] for e in log],
        ),
        "",
        "Value affected is the absolute naira value of failing rows as received (for the kobo issue, the inflated "
        "value). Where an issue spans several overlapping rules, the largest single-rule value is shown.",
        "",
        "## Detail",
        "",
    ]
    for e in log:
        related = ", ".join(f"[{r}](#{r.lower()})" for r in e.get("related") or []) or "—"
        lines += [
            f'<a id="{e["issue_id"].lower()}"></a>',
            f"### {e['issue_id']} · {e['title']}",
            "",
            f"**{e['priority']} · {e['status']} · {e['owner']}** · {', '.join(e['datasets'])} · "
            f"{', '.join(DIMENSION_LABEL.get(d, d).lower() for d in e['dimensions'])}  ",
            f"Rules: {e['rows_summary']} · Value affected: {ngn(e['value'])} · "
            f"First detected: {e['first_detected'] or '—'}  ",
            f"Sample keys: `{e['sample_keys']}`" if e["sample_keys"] else "Sample keys: —",
            "",
            f"- **Root cause:** {e['root_cause'].strip()}",
            f"- **Impact:** {e['impact'].strip()}",
            f"- **Remediation:** {(e.get('remediation') or '').strip() or '—'}",
            f"- **Prevention:** {(e.get('prevention') or '').strip() or '—'}",
            f"- **Related:** {related}",
            "",
        ]
    (REPORTS / "issue_log.md").write_text("\n".join(lines), encoding="utf-8")

    csv_rows = [{
        "issue_id": e["issue_id"], "title": e["title"], "priority": e["priority"], "status": e["status"],
        "owner": e["owner"], "rules": ";".join(e["rules"]), "datasets": ";".join(e["datasets"]),
        "dimensions": ";".join(e["dimensions"]), "severity": e["severity"], "failing_rows": e["rows_summary"],
        "value_affected_ngn": round(e["value"], 2) if e["value"] else "", "first_detected": e["first_detected"],
        "sample_keys": e["sample_keys"], "root_cause": e["root_cause"].strip(), "impact": e["impact"].strip(),
        "remediation": (e.get("remediation") or "").strip(), "prevention": (e.get("prevention") or "").strip(),
        "related": ";".join(e.get("related") or []),
    } for e in log]
    write_csv(REPORTS / "issue_log.csv", csv_rows, list(csv_rows[0].keys()))


# --------------------------------------------------------------------------- rule library

def render_rule_library(data, nodes):
    rules = sorted(data["rules"], key=lambda r: r["rule_id"])
    scored = [r for r in rules if r["scored"]]
    matrix = defaultdict(int)
    for r in rules:
        matrix[(r["dataset"], r["dimension"])] += 1

    lines = [
        "# DQ rule library",
        "",
        f"{len(rules)} rules ({len(scored)} scored, {len(rules) - len(scored)} source-conformity monitors) "
        f"across {len(DATASETS)} tables and {len(DIMENSIONS)} dimensions.",
        "",
        "Generated from the dbt project by `scripts/render_reports.py`. Each rule is a dbt test in "
        "[`models/dq_rules/`](../models/dq_rules/) and its catalogue entry (ID, dimension, severity, action, "
        "threshold, owner, rationale) is the test's `config.meta`, so this page cannot drift from what runs. "
        "Severity, action and threshold are defined in [the DQ framework](dq_framework.md).",
        "",
        "## Coverage",
        "",
        md_table(["Table"] + [DIMENSION_LABEL[d] for d in DIMENSIONS] + ["Total"],
                 [[DATASET_LABEL[ds]] + [matrix[(ds, d)] or "·" for d in DIMENSIONS]
                  + [sum(matrix[(ds, d)] for d in DIMENSIONS)] for ds in DATASETS]),
        "",
    ]
    csv_rows = []
    for ds in DATASETS:
        lines += [f"## {DATASET_LABEL[ds]}", ""]
        table_rows = []
        for r in (r for r in rules if r["dataset"] == ds):
            node = nodes.get(r["rule_id"])
            logic = rule_logic(node) if node else ""
            threshold = "" if r["threshold"] >= 1 else f" (pass ≥ {pct(r['threshold'], 0)})"
            scored_note = "" if r["scored"] else " · not scored"
            table_rows.append([
                f"**{r['rule_id']}**", f"**{r['rule_name']}**<br>{r['why']}", DIMENSION_LABEL[r["dimension"]],
                r["severity"], f"{r['action']}{threshold}{scored_note}", f"`{r['model_name']}`: {logic}",
                r["owner"],
            ])
            csv_rows.append({
                "rule_id": r["rule_id"], "rule_name": r["rule_name"], "dataset": ds, "dimension": r["dimension"],
                "severity": r["severity"], "action": r["action"], "threshold": r["threshold"],
                "scored": r["scored"], "model": r["model_name"], "column": r["column_name"] or "",
                "test_type": r["test_type"], "check": logic.replace("`", ""), "where": r["where_clause"] or "",
                "owner": r["owner"], "why": r["why"], "dbt_test": r["test_name"],
            })
        lines += [md_table(["ID", "Rule and why it matters", "Dimension", "Severity", "Action", "Check", "Owner"],
                           table_rows), ""]
    (DOCS / "rule_library.md").write_text("\n".join(lines), encoding="utf-8")
    write_csv(REPORTS / "rule_library.csv", csv_rows, list(csv_rows[0].keys()))


# --------------------------------------------------------------------------- heatmap

def heatmap_svg(score_cells, batch, n_rules):
    cols, rows = DIMENSIONS + ["ALL"], DATASETS + ["ALL"]
    pad, label_w, cell_w, cell_h, gap, split = 24, 116, 118, 58, 4, 12
    top = 92
    width = pad * 2 + label_w + len(cols) * (cell_w + gap) + split
    grid_h = len(rows) * (cell_h + gap) + split
    height = top + grid_h + 64
    font = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

    def x_of(i):
        return pad + label_w + i * (cell_w + gap) + (split if cols[i] == "ALL" else 0)

    def y_of(j):
        return top + j * (cell_h + gap) + (split if rows[j] == "ALL" else 0)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{font}" role="img" '
        f'aria-label="DQ score by table and dimension">',
        f'<rect width="{width}" height="{height}" rx="12" fill="{SURFACE}"/>',
        f'<text x="{pad}" y="36" font-size="17" font-weight="600" fill="{INK}">DQ score by table and dimension</text>',
        f'<text x="{pad}" y="58" font-size="12" fill="{MUTED}">Batch {batch:%Y-%m-%d %H:%M} WAT · '
        f'severity-weighted rule pass rate · {n_rules} scored rules · a critical breach makes a cell RED</text>',
    ]
    for i, dim in enumerate(cols):
        weight = "600" if dim == "ALL" else "400"
        out.append(f'<text x="{x_of(i) + 12}" y="{top - 10}" font-size="12" font-weight="{weight}" '
                   f'fill="{MUTED}">{DIMENSION_LABEL[dim]}</text>')
    for j, ds in enumerate(rows):
        weight = "600" if ds == "ALL" else "400"
        out.append(f'<text x="{pad}" y="{y_of(j) + cell_h / 2 + 5}" font-size="13" font-weight="{weight}" '
                   f'fill="{INK}">{DATASET_LABEL[ds]}</text>')
        for i, dim in enumerate(cols):
            x, y = x_of(i), y_of(j)
            c = score_cells.get((ds, dim))
            if not c:
                out.append(f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{cell_w - 1}" height="{cell_h - 1}" rx="6" '
                           f'fill="none" stroke="{RULE_LINE}" stroke-dasharray="3 3"/>')
                out.append(f'<text x="{x + 12}" y="{y + 34}" font-size="11" fill="{MUTED}">no rules</text>')
                continue
            rag = c["rag"]
            if c["critical_breaches"]:
                detail = f"{c['critical_breaches']} critical"
            elif c["rules_breached"]:
                detail = f"{c['rules_breached']} breach" + ("es" if c["rules_breached"] > 1 else "")
            else:
                detail = "all pass"
            tip = (f"{DATASET_LABEL[ds]} · {DIMENSION_LABEL[dim]}: {score(c['dq_score'])} {rag}. "
                   f"{c['rules']} rules, {c['rules_breached']} breached ({c['critical_breaches']} critical), "
                   f"{num(c['rows_failed'])} failing rows")
            out += [
                f'<g><title>{escape(tip)}</title>',
                f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" rx="6" fill="{blend(STATUS_COLOR[rag], 0.16)}"/>',
                f'<circle cx="{x + cell_w - 16}" cy="{y + 18}" r="5" fill="{STATUS_COLOR[rag]}"/>',
                f'<text x="{x + 12}" y="{y + 25}" font-size="16" font-weight="600" fill="{INK}">{score(c["dq_score"])}</text>',
                f'<text x="{x + 12}" y="{y + 44}" font-size="11" fill="{MUTED}">{rag} · {detail}</text>',
                '</g>',
            ]
    legend_y = top + grid_h + 30
    legend = [("GREEN", "≥ 99% and no high/medium breach"), ("AMBER", "a high/medium breach or < 99%"),
              ("RED", "a critical breach or < 95%")]
    lx = pad
    for rag, text in legend:
        out.append(f'<circle cx="{lx + 5}" cy="{legend_y - 4}" r="5" fill="{STATUS_COLOR[rag]}"/>')
        out.append(f'<text x="{lx + 16}" y="{legend_y}" font-size="12" fill="{INK}">'
                   f'<tspan font-weight="600">{rag}</tspan> <tspan fill="{MUTED}">{escape(text)}</tspan></text>')
        lx += 270
    out.append("</svg>")
    (REPORTS / "scorecard_heatmap.svg").write_text("\n".join(out), encoding="utf-8")


# --------------------------------------------------------------------------- detection coverage

def detection_coverage(rules):
    if not ANSWER_KEY.exists():
        return None
    key = json.loads(ANSWER_KEY.read_text(encoding="utf-8"))
    observed = {r["rule_id"]: r["rows_failed"] for r in rules}
    expected_by_rule = defaultdict(int)
    for issue in key["issues"]:
        for rule_id, n in issue["expected_failing_rows"].items():
            expected_by_rule[rule_id] += n
    rows = []
    for issue in key["issues"]:
        exp = issue["expected_failing_rows"]
        detected = all(observed.get(r, 0) > 0 for r in exp)
        exact = all(observed.get(r) == expected_by_rule[r] for r in exp)
        rows.append({**issue, "detected": detected, "exact": exact,
                     "observed": {r: observed.get(r, 0) for r in exp}})
    false_positives = [r for r in rules if r["rule_id"] not in expected_by_rule and r["rows_failed"] > 0]
    quiet_rules = [r for r in rules if r["rule_id"] not in expected_by_rule]
    return {"rows": rows, "false_positives": false_positives, "quiet_rules": quiet_rules,
            "expected_by_rule": expected_by_rule}


# --------------------------------------------------------------------------- scorecard

def render_scorecard(data, log, coverage):
    rules, sc, k = data["rules"], data["scorecard"], data["containment"]
    run_id, batch = rules[0]["run_id"], rules[0]["batch_as_of"]
    cells = {(r["dataset"], r["dimension"]): r for r in sc}
    overall = cells[("ALL", "ALL")]
    scored = [r for r in rules if r["scored"]]
    issue_of = {rule: e["issue_id"] for e in log for rule in e["rules"]}
    contracts = data["contracts"]
    contracts_passing = sum(c["dbt_status"] == "pass" for c in contracts)
    heatmap_svg(cells, batch, len(scored))

    def rag(c):
        return f"{RAG_ICON[c['rag']]} {c['rag']}"

    lines = [
        "# DQ scorecard",
        "",
        f"Batch as of **{batch:%Y-%m-%d %H:%M} WAT** · run `{run_id[:8]}` · {len(scored)} scored rules "
        f"(+{len(rules) - len(scored)} source-conformity monitors) · "
        "method: [DQ framework](../docs/dq_framework.md#scoring)",
        "",
        md_table(["Overall DQ score", "Rules breached", "Critical breaches", "Open P1 issues", "Silver contract"], [[
            f"**{score(overall['dq_score'])}** {rag(overall)}",
            f"{overall['rules_breached']} of {overall['rules']}",
            overall["critical_breaches"],
            sum(1 for e in log if e["priority"] == "P1" and e["status"] in ("NEW", "OPEN", "IN_REMEDIATION")),
            f"{'✅' if contracts_passing == len(contracts) else '❌'} {contracts_passing} of {len(contracts)} tests pass",
        ]]),
        "",
        "![DQ score by table and dimension](scorecard_heatmap.svg)",
        "",
        "Scores measure the data **as received** (bronze and staging). The Silver contract figure measures "
        "what reaches gold after dedupe and quarantine: the raw feeds are red, the reporting layer is clean.",
        "",
        "## By dimension",
        "",
        md_table(["Dimension", "Score", "RAG", "Rules", "Passed", "Tolerated", "Breached", "Critical breaches",
                  "Failing rows"],
                 [[DIMENSION_LABEL[d], score(c["dq_score"]), rag(c), c["rules"], c["rules_passed"],
                   c["rules_tolerated"], c["rules_breached"], c["critical_breaches"], num(c["rows_failed"])]
                  for d in DIMENSIONS if (c := cells.get(("ALL", d)))]),
        "",
        "## By table",
        "",
        md_table(["Table", "Score", "RAG", "Rules", "Breached", "Critical breaches", "Failing rows"],
                 [[DATASET_LABEL[ds], score(c["dq_score"]), rag(c), c["rules"], c["rules_breached"],
                   c["critical_breaches"], num(c["rows_failed"])]
                  for ds in DATASETS if (c := cells.get((ds, "ALL")))]),
        "",
        "## Table × dimension",
        "",
        md_table(["Table"] + [DIMENSION_LABEL[d] for d in DIMENSIONS] + ["Overall"],
                 [[DATASET_LABEL[ds]] + [f"{score(c['dq_score'])} {RAG_ICON[c['rag']]}" if (c := cells.get((ds, d)))
                                         else "·" for d in DIMENSIONS + ["ALL"]] for ds in DATASETS + ["ALL"]]),
        "",
        "## Rule breaches",
        "",
        "Sorted by severity, then pass rate. Feed-level rules (freshness, control totals) check one row per "
        "feed or channel, so a single stale feed scores 0% on its rule: by design, a missing feed is never "
        "averaged away.",
        "",
    ]
    breaches = sorted((r for r in scored if r["rule_status"] == "BREACH"),
                      key=lambda r: (SEVERITY_ORDER[r["severity"]], r["pass_rate"]))
    lines += [md_table(
        ["Rule", "Table", "Dimension", "Severity", "Failing / checked", "Pass rate", "Action", "Value affected",
         "Issue"],
        [[f"**{r['rule_id']}** {r['rule_name']}", r["dataset"], DIMENSION_LABEL[r["dimension"]], r["severity"],
          f"{num(r['rows_failed'])} / {num(r['rows_checked'])}", pct(r["pass_rate"], 2), r["action"],
          ngn(r["value_affected_ngn"]),
          f"[{issue_of[r['rule_id']]}](issue_log.md#{issue_of[r['rule_id']].lower()})" if r["rule_id"] in issue_of
          else "untriaged"] for r in breaches]), ""]

    tolerated = [r for r in scored if r["rule_status"] == "TOLERATED"]
    if tolerated:
        lines += ["## Within tolerance", "",
                  md_table(["Rule", "Failing / checked", "Pass rate", "Threshold"],
                           [[f"**{r['rule_id']}** {r['rule_name']}", f"{num(r['rows_failed'])} / {num(r['rows_checked'])}",
                             pct(r["pass_rate"], 2), f"≥ {pct(r['threshold'], 0)}"] for r in tolerated]), ""]

    monitors = [r for r in rules if not r["scored"]]
    if monitors:
        lines += ["## Source conformity (monitored, not scored)", "",
                  "How much each source deviates from the target format before silver standardises it. "
                  "Not a defect in what gold sees; it is the evidence for a data-contract conversation with the "
                  "source team.", "",
                  md_table(["Rule", "Non-conformant / checked", "Conformant"],
                           [[f"**{r['rule_id']}** {r['rule_name']}", f"{num(r['rows_failed'])} / {num(r['rows_checked'])}",
                             pct(r["pass_rate"])] for r in monitors]), ""]

    quarantine = "; ".join(f"{q['rule_id']} {num(q['rows'])}" for q in data["quarantine_by_rule"])
    flags = "; ".join(f"{f['rule_id']} {num(f['rows'])}" for f in data["flags_by_rule"])
    cdc_versions = k["all_duplicates"] - k["exact_duplicates"]
    kobo = k["kobo_value_as_received"] or 0
    lines += [
        "## What silver contained (transactions)",
        "",
        md_table(["Step", "Rows", "Detail"], [
            ["Declared in control file", num(k["declared"]), ""],
            ["Received", num(k["received"]),
             f"{num(k['declared'] - k['received'])} missing (DQ-TXN-022)" if k["declared"] != k["received"] else ""],
            ["Collapsed as duplicates", num(k["all_duplicates"]),
             f"{num(k['exact_duplicates'])} re-deliveries + {num(cdc_versions)} superseded CDC versions"],
            ["Quarantined", num(k["quarantined"]), f"{ngn(k['quarantined_value'])} held back. By rule: {quarantine}"],
            ["Passed with flags", num(k["flagged"]), f"By rule: {flags}"],
            ["Clean rows in silver", num(k["clean"]), f"{ngn(k['clean_value'])} successful value"],
        ]),
        "",
        f"- **Kobo amounts kept out of reporting.** The quarantined USSD rows would have added "
        f"{ngn(kobo)} of successful value; their real value is about {ngn(kobo / 100)}. Clean USSD value for the "
        f"whole period is {ngn(k['ussd_clean_value'])}, so letting them through would have overstated USSD value "
        f"{(k['ussd_clean_value'] + kobo) / k['ussd_clean_value']:.1f}x.",
        f"- **Double debits held for reversal.** {num(k['double_debits'])} second legs of duplicated NIP sessions "
        f"({ngn(k['double_debit_value'])}) are quarantined and routed to Settlement for refund.",
        "",
    ]

    if coverage:
        rows = coverage["rows"]
        defects = [r for r in rows if r["kind"] == "defect"]
        lines += [
            "## Detection coverage against planted defects",
            "",
            f"The synthetic data has {len(rows)} planted issues recorded in an answer key the rules never read. "
            f"**{sum(r['detected'] for r in rows)} of {len(rows)} were detected**, "
            f"{sum(r['exact'] for r in rows)} with exactly the expected failing-row count. "
            f"Of the {len(coverage['quiet_rules'])} rules with nothing planted against them, "
            f"{len(coverage['false_positives'])} fired (false positives).",
            "",
            md_table(["Planted", "Kind", "What was planted", "Catching rule", "Rows planted",
                      "Rule expected", "Rule detected", "Result"],
                     [[r["issue_id"], r["kind"].replace("_", " "), r["title"], ", ".join(r["observed"]),
                       ", ".join(num(n) for n in r["expected_failing_rows"].values()),
                       ", ".join(num(coverage["expected_by_rule"][x]) for x in r["observed"]),
                       ", ".join(num(v) for v in r["observed"].values()),
                       "✅ exact" if r["exact"] else ("⚠️ count differs" if r["detected"] else "❌ missed")]
                      for r in rows]),
            "",
            "*Rows planted* is this issue's own contribution. *Rule expected* adds up every planted issue that "
            "feeds the same rule (PI-11 and PI-12 both fail DQ-ACC-003; PI-18 and PI-19 both fail DQ-TXN-002), "
            "and *exact* means the rule's failing-row count equals that total. "
            f"{len(defects)} are defects; the rest are standardisable formats, a tolerated gap and expected CDC "
            "behaviour, planted to check the rules tell them apart from real defects.",
            "",
        ]

    if len(data["trend"]) > 1:
        lines += ["## Run history", "",
                  md_table(["Published (UTC)", "Batch as of", "Score", "RAG", "Breached", "Critical"],
                           [[f"{t['published_at']:%Y-%m-%d %H:%M}", f"{t['batch_as_of']:%Y-%m-%d %H:%M}",
                             score(t["dq_score"]), f"{RAG_ICON[t['rag']]} {t['rag']}", t["rules_breached"],
                             t["critical_breaches"]] for t in data["trend"]]), ""]

    failing_contracts = [c for c in contracts if c["dbt_status"] != "pass"]
    lines += ["## Silver contract", "",
              f"{contracts_passing} of {len(contracts)} contract tests pass (uniqueness, not-null, accepted values "
              "and relationships on silver and gold, plus reference-data checks). These run at severity `error`: "
              "a failure stops the build before gold is refreshed."]
    if failing_contracts:
        lines += ["", md_table(["Test", "Model", "Status", "Failures"],
                               [[c["test_name"], c["model_name"], c["dbt_status"], c["failures"]]
                                for c in failing_contracts])]
    lines.append("")
    (REPORTS / "dq_scorecard.md").write_text("\n".join(lines), encoding="utf-8")

    write_csv(REPORTS / "rule_results.csv", sorted(rules, key=lambda r: r["rule_id"]),
              ["rule_id", "rule_name", "dataset", "dimension", "severity", "action", "scored", "threshold",
               "rows_checked", "rows_failed", "pass_rate", "rule_status", "value_affected_ngn", "sample_keys",
               "owner", "run_id", "batch_as_of"])
    return overall


def main():
    REPORTS.mkdir(exist_ok=True)
    DOCS.mkdir(exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    data = load(con)
    con.close()
    if not data["rules"]:
        raise SystemExit("gold.gold_dq_rule_results is empty: run the pipeline first.")

    log = build_issue_log(data)
    coverage = detection_coverage(data["rules"])
    render_issue_log(log, data)
    render_rule_library(data, load_rule_nodes())
    overall = render_scorecard(data, log, coverage)

    summary = f"overall {score(overall['dq_score'])} {overall['rag']}, {len(log)} issues"
    if coverage:
        summary += f", detected {sum(r['detected'] for r in coverage['rows'])}/{len(coverage['rows'])} planted issues"
    print(f"reports written: {summary}")


if __name__ == "__main__":
    main()
