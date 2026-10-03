# Occams

[![check](https://github.com/MaverickHQ/occams-test-lab/actions/workflows/check.yml/badge.svg)](https://github.com/MaverickHQ/occams-test-lab/actions/workflows/check.yml)

A falsification lab for retail trading hypotheses. You declare a floor and
an alpha budget before anything runs; the lab registers a question, spends
the alpha, measures on a partition no one looked at, and refuses the
strategy unless it clears five checks — including one that asks whether
the entry beats simply being long at the same geometry. Every question,
verdict, refusal and decision is a record in a hash-chained Register, and
the pages are rendered from the Register alone. Nothing here places an
order.

**Read the results, rendered:** <https://maverickhq.github.io/occams-test-lab/> — the console, the programme page,
both surveys and every document below as one static site, with no script and
no network reference. On GitHub the `.html` pages show as source; the site is
where to read them.

## Where to find things

| You want | Read |
|---|---|
| what three programmes found, on one page | [The lab's closing statement](docs/LAB-CONCLUSION.md); each programme's own conclusion: [first](docs/PROGRAMME-CONCLUSION.md), [second](docs/PROGRAMME-2-CONCLUSION.md), [third](docs/PROGRAMME-3-CONCLUSION.md) |
| the reports, rendered from the Registers | [the research console](https://maverickhq.github.io/occams-test-lab/console.html), [the programme page](https://maverickhq.github.io/occams-test-lab/programme.html), the surveys [grid-001](https://maverickhq.github.io/occams-test-lab/surveys/grid-001-seed20260912.html) and [grid-002](https://maverickhq.github.io/occams-test-lab/surveys/grid-002-seed20260920.html), and their readiness tables [one](docs/surveys/grid-001-seed20260912-readiness.md) and [two](docs/surveys/grid-002-seed20260920-readiness.md) |
| how the lab prevents p-hacking, guard by guard | [docs/INTEGRITY.md](docs/INTEGRITY.md) |
| the verdict that turned out to be the market | [docs/EXPLAINER-Q2-001.md](docs/EXPLAINER-Q2-001.md) |
| to run it, extend it, or recover from a failure | [docs/SETUP.md](docs/SETUP.md), [docs/EXTENDING.md](docs/EXTENDING.md), [docs/RUNBOOK.md](docs/RUNBOOK.md) |
| the record itself | the three Registers under [register/](register/), the decisions under [docs/adr/](docs/adr/), the dated log in [TASKS-v4.md](TASKS-v4.md) |
| what it was built to | [REQUIREMENTS-v4.md](REQUIREMENTS-v4.md), [DESIGN-v4.md](DESIGN-v4.md), [CONTEXT.md](CONTEXT.md) |
| the publication decision, the security policy, the licence | [docs/PUBLICATION.md](docs/PUBLICATION.md), [SECURITY.md](SECURITY.md), [LICENSE](LICENSE) and [NOTICE](NOTICE) |

## What is published here

- **The lab.** The code: the spec and its compiler, both simulators, the
  five guards, the alpha accountant, the survey runner, the burst scripts,
  the console and the pages, the reproduction paths, the setup path.
- **The record.** Three hash-chained Registers — every question, verdict,
  refusal, stop and decision, 85 records across three programmes — with
  forty-six ADRs and a task list whose log says what happened each day and
  why.
- **The results.** The console, the programme page, two survey pages of
  38,976 cells each with their readiness tables, the three programme
  conclusions and the lab's closing statement, all rendered from the
  Registers; [docs/INTEGRITY.md](docs/INTEGRITY.md) on how the lab prevents p-hacking;
  [docs/EXPLAINER-Q2-001.md](docs/EXPLAINER-Q2-001.md) on the verdict that turned out to be the market.
- **Not published.** The market data: the archive is not in the repository
  and the vendor's licence forbids redistribution, but every verdict names
  the series it consumed, so a licence holder can reproduce it exactly with
  `make reproduce-private`. The author's configuration — the capital, alpha
  and falsifier numbers — which is gitignored and never had a default. Any
  credential. Publication itself is a recorded decision (R7),
  [docs/PUBLICATION.md](docs/PUBLICATION.md) of 2026-09-26; the same pages go
  out as a static site, built by `make site` and deployed by the `pages`
  workflow. The commit history before publication: by the author's decision
  the public repository begins at a single snapshot, because two early
  commits carried a private address. The commit ids cited in the task list
  and stamped on the verdicts (`engine_sha`) name commits in that private
  history; the Registers, the decisions and the dated log are all here.

## What it found

Three programmes, fourteen days, 77,952 cells screened at zero alpha, six
questions registered by the author, five verdicts reached by the machine
against a floor declared before each run: **four null, one supported — and
the supported one carries beside it the record that undid its meaning.**
Q2-001 cleared beats-null, plateau, floor and leave-one-out with +0.213 net
R over 6,946 trades; always-long at the winner's geometry and gate, on the
same partition, made +0.214. The entry added nothing. That record is why
the lab now has a fifth check (ADR-0043) and judges every sweep on the
margin over always-long (ADR-0045). The same mechanism chosen by margin
beat always-long and missed the floor (Q2-002). The third programme's one
question was refused before a verdict: its winning cell held fewer trades
than the power plan required — which exposed a promise `prepare` had made
in every programme, fixed the same day.

| question | origin | EV net R | trades | outcome |
|---|---|---|---|---|
| `Q-003` | Draft, index ETFs, regime axis | −0.047 | 1,391 | null — beats-null and the floor refused |
| `Q-004` | Draft, superseding `Q-003` | −0.045 | 2,088 | null — every check refused |
| `Q-005` | Draft, reversal after a down-run | +0.051 | 893 | null — the floor and leave-one-out refused |
| `Q2-001` | survey cell, S&P 100, down-run in the up regime | +0.213 | 6,946 | **supported** by four checks; margin over always-long −0.001 |
| `Q2-002` | survey cell, S&P 100, the same mechanism ungated | +0.109 | 12,732 | null on the floor alone, under five checks |
| `Q3-001` | survey cell, sector ETFs, pullback in trend | — | 863 held | refused at measurement: 1,068 required |

The lab's product is its refusals. What three programmes established, and
what they did not, is in [docs/LAB-CONCLUSION.md](docs/LAB-CONCLUSION.md);
each programme's own conclusion is beside it; [the programme page](https://maverickhq.github.io/occams-test-lab/programme.html) says
what was searched, what it cost and what was found, for a reader with no
code. No edge was found. The lab can tell when it has not found one, and
says so in its own words.

## What it refuses, by construction

- **A question that was not registered first**, with its floor, its sweep
  and its alpha charged by the accountant before a bar of the measurement
  partition is read. The loop never registers; the `--yes` is a human's.
- **A verdict under-powered for its floor**, at registration and again at
  measurement, where the guard counts the winning cell's own trades.
- **A winner that random entry matches, that a plateau cannot hold, that
  one name carries, that misses the floor, or that being long would have
  earned anyway** — the five checks, each named on the record with its
  evidence.
- **A coin flip.** `make null` runs one through the whole pipeline and must
  be refused; `make signal` plants an effect at the floor and must be
  accepted, naming all five checks. Both run on every build and in CI.
- **A number the author did not declare.** Capital, drawdown, risk, the
  alpha split and the falsifier count have no defaults anywhere; the lab
  refuses to start without them, and no page carries money.
- **A record rewritten.** The Register is append-only and hash-chained; a
  correction supersedes; a tampered file cannot be extended.

## What you get by cloning it

A research process, not a signal: a lab that refuses your idea unless it
clears five checks it declared before it looked — beats random entry,
holds across neighbouring settings, holds with any one name left out,
clears the floor you set, and beats simply being long at the same geometry
and gate — and that writes every refusal down with its evidence. Three ways
to use it, in increasing cost:

1. **Five minutes, no data.** `make quickstart`, `make null`, `make
   signal`: the pipeline refuses a coin flip and accepts a planted effect,
   naming every check. You have seen the guards work before you trust them.
2. **An afternoon, your own bars.** Ingest a CSV per symbol under a rights
   record you declare (`python -m occams ingest --csv`), declare a universe,
   freeze its calendar, freeze a classifier, copy
   `surveys/grid-template.toml`, and survey it: every cell of your idea
   against always-long at the same geometry, on the calibration half only,
   at no cost to your error budget, on one page. Nothing in a survey is a
   verdict, and it says so.
3. **A programme, with a data key.** Declare your numbers (`python -m occams
   init`, then `whatif` to see what they afford), ingest, survey 38,976 cells
   on a spot instance in about an hour, register the one cell worth your
   alpha, let the loop measure it on the half no one looked at, and read the
   verdict with the record beside it that says what being long would have
   made. Stop by record; the conclusion writes itself from the Register.

What you will not get: alerts, signals, or an edge. Three programmes found
none, and the lab said so in its own words. What you will get is a lab that
can tell when it has not found one — which is the half of a trading system
that is usually missing.

## What the lab's output looks like

Real output, captured on 2026-09-26. The quickstart's last lines:

```text
25 required fields; none has a default or a recommended value.
floor 0.15R, sigma 1.2R, Bonferroni over 4, power 80%: N = 714  (docs/M0-ANSWERS.md §M0.15 says 714)
ALL FOUR PASS in 0.03s. This touched no market data, no API key, and no network.
```

The null control — a coin flip through the whole pipeline — and the
signal control, a planted effect at the floor:

```text
NULL CONTROL [synthetic] — CONTROL-NULL, N = 1000 (required 837), winner EV = -0.0067 net R
REFUSED at MEASURED -> FORWARD, by:
  - beats-null: random entry under the same geometry does as well
  - floor: EV per trade in net R is below the declared floor
  - beats-always-long: being long at the same geometry and gate does as well
checks that passed: ['plateau', 'leave_one_out']

SIGNAL CONTROL [synthetic] — CONTROL-SIGNAL, N = 1000 (required 837), winner EV = +0.1583 net R
ACCEPTED at MEASURED -> FORWARD: all five checks passed — ['plateau', 'beats_null', 'clears_floor', 'leave_one_out', 'beats_always_long']
```

The programme page's one-line summary of the three programmes, from the
Registers alone:

```text
P1 register.jsonl: 34 records, 3 question(s), 3 resolved, 0 survey(s), closed
P2 programme-2.jsonl: 37 records, 2 question(s), 2 resolved, 1 survey(s), stopped
P3 programme-3.jsonl: 14 records, 1 question(s), 0 resolved, 1 survey(s), stopped
```

The top of a survey's readiness table — one gate-ready cell per family,
its EV on the calibration half, always-long at the same geometry, the
margin, the fifth check's verdict, the margin by era, and what registering
it would cost:

| # | Cell | Universe | EV | Always-long | Margin | Fifth check | Margin by era | Sweep · alpha |
|---:|---|---|---:|---:|---:|---|---|---|
| 1 | `5da80c610ab6da80` | dow_30 | +0.296 | −0.075 | +0.371 | pass | +0.344 / +0.367 / +0.408 | 30 · 0.3 |
| 2 | `151ea6728ab85559` | index_etfs | +0.233 | −0.108 | +0.341 | pass | +0.173 / +0.327 / +0.422 | 30 · 0.3 |
| 3 | `2f89cd3fc3abbd83` | sp_100 | +0.230 | −0.085 | +0.315 | pass | +0.341 / +0.287 / +0.331 | 30 · 0.3 |
| 4 | `5834abf51248fbb5` | index_etfs | +0.211 | −0.098 | +0.309 | pass | +0.173 / +0.336 / +0.361 | 15 · 0.15 |

Twenty of twenty passed that table's fifth check on the calibration half in
each of two surveys; the one that was measured lost its whole margin on the
other half. That is the lesson of the verdict table above, and why the
pages show the screen and the verdict side by side.

The pages themselves: [docs/console.html](docs/console.html) (every
record, the controls recomputed on each build),
[docs/programme.html](docs/programme.html) (what was searched, what it
cost, what was found), [docs/surveys/](docs/surveys/) (one page per survey
beside its readiness table) and the conclusions under [docs/](docs/). On
GitHub they show as source; the rendered site is <https://maverickhq.github.io/occams-test-lab/>, and
`make site` builds the same pages locally into `build/site`.

## Run it in five minutes, with no data and no keys

```bash
make setup                 # a virtual environment with the lab and its dev extras
export PATH="$PWD/.venv/bin:$PATH"
make quickstart            # $0, no data, no keys, no network, under ten seconds
make null                  # a coin flip is REFUSED, naming why
make signal                # a planted effect at the floor is ACCEPTED, naming all five checks
make reproduce-public      # the pipeline on synthetic fixtures; refuses an exact-historical claim
make site                  # every page and document as one static site under build/site, checked by the publication gate
```

## Set it up for your own questions

```bash
python -m occams init      # the configuration skeleton — every required key, no value: the numbers are yours
python -m occams doctor    # what is missing, by name; never a secret
```

Then [docs/SETUP.md](docs/SETUP.md): declare your numbers, see what they
imply with `whatif`, ingest under a rights record, open a programme in
order, and run a 38,976-cell survey on a spot instance with
`tools/aws/burst.sh`. [docs/RUNBOOK.md](docs/RUNBOOK.md) is what to do
when something goes wrong.

## What is built

This repository is Occams: a falsification lab for retail trading hypotheses.
**M0 closed on 2026-09-10** (`docs/M0-ANSWERS.md`); **M1-M9 are built** —
the vendored core, CI, the strict config loader, the two state machines, the
guards, the hash-chained Register, the two controls, the `StrategySpec` with
its compiler, the day-boxed engine, and the data path: a `DataSource` port
with a synthetic fixture, the rights matrix, the content-addressed archive,
instants, corporate actions, partitions and the point-in-time universe;
and the cost model — published components with provenance, a spread that
says whether it is declared, bounded or measured, FX as a cost and drift as
an exposure, and obtainability auditors on every fill; and the proposers —
draft emitters with no authority, a frozen causal regime classifier, and
measured clustering; the position-boxed simulator with its block-bootstrap
null; the forward window — declared in trades and time, executed for real
at minimum size through a Telegram card, evaluated once (never opened:
the execution host is deferred outside this lab, ADR-0044); and the alpha
accountant, whose balances replay from the Register; and the question
pipeline — registration through the accountant, measurement from the
archive, a Verdict that freezes the winner's hash, the archived path
distribution, and an unattended loop that never registers. Nothing places an
order; the human gate is human.

```bash
make setup           # a virtual environment with the lab and its dev extras (M15.4); then docs/SETUP.md
python -m occams init      # the configuration skeleton — every required key, no value: the numbers are yours
python -m occams doctor    # what is missing, by name; never a secret
make quickstart      # $0, no data, no keys, no network, under ten seconds
make null            # a coin flip through the whole pipeline is REFUSED, naming why (S3)
make signal          # a planted effect at the floor is ACCEPTED, naming all five checks (S10, ADR-0043)
make check           # tests · lint · credential scan · provenance · null · signal
make test-fast       # every test not marked slow — the fast cycle, never the proof (M14.1)
python -m occams --schema   # every required config key, no values
python -m occams whatif a.toml b.toml [--archive archive --register R]   # what candidate configs imply, side by side, with refusals flagged; the falsifier arithmetic and universe affordability (M12.0)
python -m occams loop REGISTER ARCHIVE QUEUE --seed N [--config C]   # run the registered queue unattended with a declared seed (no default, M12.6); after each verdict the winner's era decomposition with its missed entries and, for a question from a survey, the shrinkage from screening; stops when the falsifier fires
python -m occams classifier freeze --archive archive/ --register register/register.jsonl --seed N   # the classifier's own registration
python -m occams question prepare|register [--axis regime|price_daily] ...  # a question from the frozen classifier or on daily bars alone; register is the human act
python -m occams universe declare|show ...  # a universe is a Register record: members, rule, bias (M12.1)
python -m occams calendar freeze|show [--universe NAME] ...   # the calendar every partition is cut from, a Register record (ADR-0038); per universe in programme 2
python -m occams survey show|cells surveys/grid-001.toml --register register/programme-2.jsonl   # the survey grid: hash, families, cells, refusals by name; nothing runs (M12.2)
python -m occams ingest SYMBOLS --csv DIR --source-id ID --rights-provenance TEXT --permit private_retention,…   # M15.5: your own bars under a rights record you declare; no vendor, no key
python -m occams question remeasure --question ID --register R --queue Q --archive A --config C --seed N --rolls K --out register/programme-N-rolls.jsonl   # M15.9: a resolved question on a rolling window inside its measurement partition; records beside the programme, never a verdict
python -m occams survey inputs GRID --register R --archive A   # M14.7: the files a survey box needs — the manifest and the grid's bars — what the burst uploads
python -m occams survey run GRID --archive archive --register R --config C --seed N [--no-record]   # every cell on the definition partition, zero alpha; resumable (M12.3); `survey record` appends SurveyRecorded here
python -m occams survey page GRID --out DIR --register R --config C   # the survey page: trust, never profit (M12.4); `make survey GRID= OUT=`; big surveys run on the burst: tools/aws/burst.sh
python -m occams survey candidates GRID --out DIR --register R [--config C] [--top N | --ids a,b] [--drafts DIR | --no-drafts]   # M12.5: one gate-ready cell per family, priced by the accountant, a generated Draft each (no standing); a survey the Register does not hold is refused
python -m occams survey candidates GRID --out DIR --register R --config C --archive A --fifth-check [--draws 4000] [--seed N] [--readiness-out docs/surveys/<grid>-readiness.md]   # ADR-0043 on the definition partition, zero alpha: always-long at each candidate's geometry and gate, the guard's Monte Carlo at the corrected alpha, the margin per era; a table beside the survey page
python -m occams question prepare|register --from-survey DIR --grid GRID --ids a,b --archive A --register R --config C --floor-ev X --floor-frequency Y --by NAME --yes   # M12.5: the author's act — one question per family, the cell's sentence as the R4.9 distinction, screened cells stamped (N6); nothing registers without --yes
python -m occams programme --register register/register.jsonl --register register/programme-2.jsonl --archive archive --config occams.toml --out docs/programme.html   # M12.7: what did we search, what did it cost, what did we find — both programmes; `make programme`
python -m occams reproduce private --question ID --register R --queue Q --archive A --config C [--at-commit]   # M11.5 / F14: recreate a stamped Verdict from the licensed archive on a scratch Register; fails loudly without the archive, never skips; `make reproduce-private QUESTION=…`
python -m occams reproduce public [--claim-historical]   # M11.6 / F14: the pipeline on synthetic fixtures, no vendor access; an exact-historical claim is refused when the recorded rights forbid raw redistribution; `make reproduce-public`
python tools/prepublish.py [PATH ...]   # M11.7 / R7: the publication gate's check on every committed page and Register — no script, network, credential shape, broker term, raw bars or money key; `make prepublish`, in `make check` and CI
python -m occams programme stop --register R --config C --kind alpha|author [--reason "..."] --by NAME [--yes]   # M12.8: a stop is a Register record — alpha exhausted (verified against the ledger) or the author's reason; shows where the three stopping conditions stand; nothing appends without --yes; the falsifier's own stop is the loop's LabClosed
python -m occams conclude --register R --out PATH [--config C] [--archive A]   # M12.8: the conclusion from the Register in the shape of docs/PROGRAMME-CONCLUSION.md with the survey layer — refused until a stopping condition is a record; never overwrites
make console          # the research console from the Register: docs/console.html, the author's build (M11.4)
make console-offline  # the plain build from the committed Register alone; no config, no archive, no network
```

- **[CONTEXT.md](CONTEXT.md)** — canonical language and boundaries.
- **[REQUIREMENTS-v4.md](REQUIREMENTS-v4.md)** — intent, constraints, and
  acceptance surface.
- **[DESIGN-v4.md](DESIGN-v4.md)** — architecture and decision synthesis.
- **[TASKS-v4.md](TASKS-v4.md)** — executable delivery sequence and gates.
- **[ALIGNMENT-v4.md](ALIGNMENT-v4.md)** — non-normative reconciliation map
  from each prior review finding to its v4 proof.
- **[docs/adr/](docs/adr/)** — the decisions (0001–0046) and their rejected alternatives.
- **[docs/M0-ANSWERS.md](docs/M0-ANSWERS.md)** — the M0 evidence, dated 2026-09-10.
- **[PROVENANCE.md](PROVENANCE.md)** — the vendored core's donor commit and hashes.
- **[CLAUDE.md](CLAUDE.md)** — working rules: read order, read-only
  references, and the naming hazards.
- **[docs/RUNBOOK.md](docs/RUNBOOK.md)** — what to do by situation; **[docs/SETUP.md](docs/SETUP.md)** — clone, configure, run, burst.
- **[docs/INTEGRITY.md](docs/INTEGRITY.md)** — how the lab prevents p-hacking; **[docs/EXPLAINER-Q2-001.md](docs/EXPLAINER-Q2-001.md)** — the supported verdict, explained; **[docs/EXTENDING.md](docs/EXTENDING.md)** — a new entry kind, a new grid, your own bars.
- **[docs/LAB-CONCLUSION.md](docs/LAB-CONCLUSION.md)** — what three programmes established; **[SECURITY.md](SECURITY.md)** — what a security report here is about, and how to make one.

The implementation target is this repository, `occams-test-lab`
(remote `MaverickHQ/occams-test-lab`, published under the recorded decision
in `docs/PUBLICATION.md`, R7). `prop-challenge-lab` is a source donor, not a dependency, and is
complete, published and read-only. Within this snapshot, later ADR amendments define the
decision, `REQUIREMENTS-v4.md` states the normative obligation,
`DESIGN-v4.md` explains its implementation shape, and `TASKS-v4.md` supplies
the executable proof. A contradiction is a release blocker, not a precedence
choice to defer until implementation.
