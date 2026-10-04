# Setup — clone, configure, run, and burst

The path a stranger walks from a clone to a first survey (M15.4). Every
command runs from the repository root. Nothing here supplies a number the
lab treats as the author's: the capital figures, the alpha split and the
falsifier count are yours, and the lab refuses to start until you declare
them (R9, R4, ADR-0033). `docs/RUNBOOK.md` is what to do when something
goes wrong; `README.md` is what this is.

## 1. Clone and install

Python 3.12 or later. Then:

```bash
make setup
```

That creates `.venv` with the lab and its dev extras. Put it on the path
for the rest of the session:

```bash
export PATH="$PWD/.venv/bin:$PATH"
```

## 2. Declare your numbers

```bash
python -m occams init
```

This writes `occams.toml` — every required key with a placeholder and no
value. The file is gitignored: it carries capital, drawdown and risk
figures and the alpha split, and it is never committed. Replace every
placeholder. Before you settle on a set, see what it implies:

```bash
python -m occams whatif occams.toml
```

`whatif` shows the falsifier arithmetic and, with an archive and a
Register, what each universe can afford at a floor. It recommends
nothing. A registered question is stamped with its configuration;
changing the numbers afterwards is a recorded decision, not a re-run.

## 3. Check the machine

```bash
python -m occams doctor
```

It names what is missing — the interpreter, the install, unfilled keys
in the configuration, the data key, the archive, the AWS CLI — and never
prints a secret. `MISSING` means the lab cannot start; `note` is
advisory.

## 4. Run without data

```bash
make quickstart          # $0, no data, no keys, no network, under ten seconds
make null                # a coin flip through the whole pipeline is REFUSED, naming why
make signal              # a planted effect at the alternative is ACCEPTED, naming all five checks
make reproduce-public    # the pipeline on synthetic fixtures; refuses an exact-historical claim
make test-fast           # every test not marked slow; `make check` is the proof
```

If `make null` ever accepts or `make signal` ever refuses, stop: the
guards have drifted (S3, S10).

## 5. Data

The lab ingests from Tiingo under a rights record; bars never enter the
repository and are never redistributed. The key lives outside the
repository — on macOS in the Keychain, elsewhere in the environment — and
is substituted at the moment of use:

```bash
security add-generic-password -U -s TIINGO_API_KEY -a occams -w     # macOS: prompts; nothing in shell history
```

```bash
TIINGO_API_KEY="$(security find-generic-password -s TIINGO_API_KEY -w)" python -m occams ingest SPY QQQ DIA IWM --start 1993-01-29 --end 2026-09-10 --archive archive
```

On another platform, export `TIINGO_API_KEY` for the one command. Symbols
are charged against the monthly budget before the fetch; a refused symbol
costs nothing.

## 6. A first programme, in order

Each step is a Register record before the next (`docs/RUNBOOK.md`,
*Opening a programme*):

1. a universe — `python -m occams universe declare --register register/programme-N.jsonl --name … --members … --rule … --bias … --chosen-on …`
2. its calendar — `python -m occams calendar freeze --register … --universe …`
3. the classifier — `python -m occams classifier freeze --archive archive --register … --config … --seed N`
4. a grid — a committed, hashed TOML under `surveys/`; `python -m occams survey show GRID --register …`
5. the survey — `python -m occams survey run GRID --archive archive --register … --config … --seed N`, on this machine, or on the burst below
6. the candidates — `python -m occams survey candidates GRID --out DIR --register … --config … --fifth-check --readiness-out …`
7. a question — `python -m occams question register --from-survey DIR --grid GRID --ids … --floor-ev X --floor-frequency Y --by NAME --yes` — the floor is yours, declared at that command; the `--yes` is a human's
8. the loop — `python -m occams loop register/programme-N.jsonl archive register/programme-N-queue.jsonl --config … --seed N`
9. the pages — `make console && make programme`

Question ids follow the Register's name (`programme-N.jsonl` → `QN-`).

## 7. The burst — a survey on a spot instance

A grid of 38,976 cells takes about an hour on 128 vCPUs and days on a
laptop. `tools/aws/burst.sh` runs it on one spot instance in an auto
scaling group of one with an S3 checkpoint, resumes after an interruption,
uploads only the manifest and the bars the grid needs, and never records:
`survey record` runs here after every file is verified.

What you need: the AWS CLI configured with credentials (`aws configure`
or a named profile) and a default region. Nothing else is stored anywhere
in this repository. The variables the script reads are named, with no
value, in `tools/aws/burst.env.example`; copy it to `tools/aws/burst.env`
(gitignored) or export them:

```bash
export CONFIG=configs/programme-N.toml REGISTER=register/programme-N.jsonl
```

Then, in order:

```bash
tools/aws/burst.sh setup                       # bucket, config parameter, instance role, launch template, group — idempotent
tools/aws/burst.sh start surveys/grid-NNN.toml SEED
tools/aws/burst.sh watch surveys/grid-NNN.toml SEED
tools/aws/burst.sh pull  surveys/grid-NNN.toml SEED
tools/aws/burst.sh record surveys/grid-NNN.toml SEED archive/surveys/<job>-<type>
tools/aws/burst.sh teardown --all              # the same day; then verify every resource is absent
```

The box reads the configuration from SSM Parameter Store as a
SecureString and the code from a git bundle of the committed HEAD; the
data key never reaches it. `python -m occams survey inputs GRID
--register R --archive archive` lists exactly what goes up.

## 8. Before publishing anything

Publication is a recorded decision (R7). `make prepublish` is the gate's
check on every page, Register and document that would go out — no
script, no network, no credential shape, no broker term, no raw bars, no
money key — and it is the check, not the decision.
