#!/usr/bin/env python
"""Run the whole thing end to end, on any OS.

  1. generate   synthetic extracts + answer key           scripts/generate_data.py
  2. build      seeds, bronze, silver, gold marts, DQ rules, silver contracts
  3. publish    rule results with denominators -> dq_audit  scripts/publish_dq_results.py
  4. score      gold DQ models (scorecard, history)
  5. report     scorecard, issue log, rule library          scripts/render_reports.py

DQ rules run at severity "warn", so step 2 only fails if a silver contract
breaks or a model errors, which is exactly when gold must not be refreshed.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def step(title):
    print(f"\n=== {title} " + "=" * max(0, 70 - len(title)), flush=True)


def python(script, *args):
    subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], check=True, cwd=ROOT)


def dbt(*args):
    # Each dbt step runs in its own process: dbt-duckdb holds the warehouse file
    # open for the life of the process, which on Windows locks out the next step.
    code = ("import sys; from dbt.cli.main import dbtRunner; "
            "sys.exit(0 if dbtRunner().invoke(sys.argv[1:]).success else 1)")
    cmd = [sys.executable, "-c", code, *args, "--project-dir", str(ROOT), "--profiles-dir", str(ROOT)]
    if subprocess.run(cmd, cwd=ROOT).returncode != 0:
        raise SystemExit(f"dbt {' '.join(args)} failed; gold was not refreshed.")


def main():
    parser = argparse.ArgumentParser(description="Generate data, build, score and report.")
    parser.add_argument("--skip-generate", action="store_true", help="reuse the extracts in data/raw")
    parser.add_argument("--seed", default="42")
    parser.add_argument("--as-of", help="batch timestamp in WAT, 'YYYY-MM-DD HH:MM' (default: now)")
    args = parser.parse_args()

    os.chdir(ROOT)  # dbt reads data/raw and the warehouse path relative to the project
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    (ROOT / "warehouse").mkdir(exist_ok=True)

    if not args.skip_generate:
        step("1/5 generate synthetic extracts")
        python("generate_data.py", "--seed", args.seed, *(["--as-of", args.as_of] if args.as_of else []))

    step("2/5 dbt build: bronze -> silver -> gold, DQ rules, silver contracts")
    dbt("build", "--exclude", "tag:dq_reporting")

    step("3/5 publish DQ rule results")
    python("publish_dq_results.py")

    step("4/5 dbt build: DQ scorecard models")
    dbt("build", "--select", "tag:dq_reporting")

    step("5/5 render reports")
    python("render_reports.py")
    print("\nDone. Open reports/dq_scorecard.md, reports/issue_log.md and docs/rule_library.md.")


if __name__ == "__main__":
    main()
