.PHONY: prepublish-all site setup doctor test test-fast calibrate lint credscan provenance prepublish check quickstart null signal console console-offline survey programme reproduce-private reproduce-public

QUESTION ?= Q-005
REPRO_REGISTER ?= register/register.jsonl
REPRO_QUEUE ?= register/queue.jsonl
REPRO_CONFIG ?= occams.toml

setup:                    ## M15.4 — a virtual environment with the lab and its dev extras; then `python -m occams init`
	python3 -m venv .venv && .venv/bin/python -m pip install --quiet --upgrade pip && .venv/bin/python -m pip install --quiet -e ".[dev]"
	@echo "setup complete: put .venv/bin on PATH, then \`python -m occams init\` and \`python -m occams doctor\` (docs/SETUP.md)"

doctor:                   ## M15.4 — what is missing, by name; never a secret
	python3 -m occams doctor

site:                     ## M15.2 — every page and document under docs/ as one static site in build/site, checked by the publication gate
	python3 -m occams site --out build/site

test:
	python3 -m pytest

test-fast:                ## M14.1 — every test not marked slow; the fast cycle, never the proof
	python3 -m pytest -m "not slow and not calibration"

calibrate:                ## M16.7 / ADR-0047 — the size-and-power table: each Monte Carlo guard in isolation, hundreds of seeds, against the rate it declares
	python3 -m occams.calibrate --save build/calibration.json
	OCCAMS_CALIBRATION_CACHE=build/calibration.json python3 -m pytest -m calibration tests/test_apparatus_size.py

lint:
	python3 -m ruff check occams/ tests/ scripts/ tools/

credscan:                 ## R5 / S5 — credential-shaped strings anywhere in the tree fail
	python3 tools/credscan.py

provenance:               ## M1.5 — every vendored file still matches its recorded hash
	python3 tools/vendor_core.py --verify

prepublish:               ## M11.7 / R7 — the publication gate's check on every committed page and Register: no script, network, credential shape, broker term, raw bars or money key
	python3 tools/prepublish.py

prepublish-all:           ## M15.3 — every committed text file: broker terms, money figures, private paths, e-mail, account ids; hits kept only by recorded decision
	python3 tools/prepublish.py --all

check: test lint credscan provenance prepublish null signal

quickstart:               ## S2 — $0, no data, no keys, no network, under ten seconds
	python3 scripts/quickstart.py

null:                     ## S3 — a coin flip through the whole pipeline is REFUSED, naming which refusal fired
	python3 -m occams.controls null
	python3 -m occams.controls null --engine=day_boxed

signal:                   ## S10 — a planted effect at the floor is ACCEPTED, naming that all five checks passed
	python3 -m occams.controls signal
	python3 -m occams.controls signal --engine=day_boxed

console:                  ## M11.4 — the author's build of the console: balances and the falsifier count from occams.toml; committed under docs/
	python3 -m occams console --register register/register.jsonl --register register/programme-2.jsonl --register register/programme-3.jsonl --archive archive --config occams.toml --out docs/console.html

console-offline:          ## M11.4 — the plain build from the committed Register alone; no config, no archive needed, no network, no credentials
	python3 -m occams console --register register/register.jsonl --register register/programme-2.jsonl --register register/programme-3.jsonl --archive archive --out build/console.html

survey:                   ## M12.4 — the survey page from a results directory: make survey GRID=surveys/grid-001.toml OUT=archive/surveys/<job>-<box>
	python3 -m occams survey page $(GRID) --out $(OUT) --register register/programme-2.jsonl --config configs/programme-2.toml

programme:                ## M12.7 — the programme page for both programmes, the author's build; committed under docs/
	python3 -m occams programme --register register/register.jsonl --register register/programme-2.jsonl --register register/programme-3.jsonl --archive archive --config occams.toml --out docs/programme.html

reproduce-private:        ## M11.5 / F14 — exact reproduction of a stamped Verdict from the licensed archive; FAILS without it, never skips. QUESTION=Q-005 REPRO_REGISTER= REPRO_QUEUE= REPRO_CONFIG=
	python3 -m occams reproduce private --question $(QUESTION) --register $(REPRO_REGISTER) --queue $(REPRO_QUEUE) --archive archive --config $(REPRO_CONFIG)

reproduce-public:         ## M11.6 / F14 — the pipeline on synthetic fixtures: no vendor access, no licensed bar, no exact-historical claim
	python3 -m occams reproduce public
