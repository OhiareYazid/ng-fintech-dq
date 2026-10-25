# Unix shortcuts. On Windows, use `python run_pipeline.py` (same steps).
PY ?= python
DBT ?= dbt
DBT_FLAGS = --profiles-dir .

.PHONY: all setup data build publish score reports docs clean

all:            ## generate data, build, score and report
	$(PY) run_pipeline.py

setup:          ## install dependencies
	$(PY) -m pip install -r requirements.txt

data:           ## regenerate the synthetic extracts and answer key
	$(PY) scripts/generate_data.py --seed 42

build:          ## bronze -> silver -> gold + DQ rules + silver contracts
	$(DBT) build $(DBT_FLAGS) --exclude tag:dq_reporting

publish:        ## load rule results (with denominators) into dq_audit
	$(PY) scripts/publish_dq_results.py

score:          ## build the gold DQ scorecard models
	$(DBT) build $(DBT_FLAGS) --select tag:dq_reporting

reports:        ## write reports/ and docs/rule_library.md
	$(PY) scripts/render_reports.py

docs:           ## browse lineage and model docs
	$(DBT) docs generate $(DBT_FLAGS) && $(DBT) docs serve $(DBT_FLAGS)

clean:
	rm -rf target data warehouse/*.duckdb
