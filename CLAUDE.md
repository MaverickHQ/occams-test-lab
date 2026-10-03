# Occams — project context

**State on 2026-10-03: published and complete.** `MaverickHQ/occams-test-lab`
is public and begins at a single snapshot commit; the release is `v1.0.0`; the
pages are live at `https://maverickhq.github.io/occams-test-lab/`; three
programmes are run, stopped by record and concluded; M0–M15 are closed or closed by decision; nothing is open. The rest
of this file is how it got here, in order, and the rules that bind any further
change: *Standing rules*, *Naming*, and the status-log entry of 2026-10-03 in
`TASKS-v4.md` headed *where it stands, for the next context*, which says how a
change is made from here.

**All work happens in this repository.** M0 closed and M1-M9 were built on 2026-09-10
(M5.0 closed by decision on 2026-09-20: the cost basis stays bounded); four real verdicts are in — three null in the first programme, whose
**lab closed on 2026-09-12 (ADR-0033)** so nothing registers in its Register again, and
one supported in the second (Q2-001, 2026-09-17) with its margin over always-long
recorded beside it at −0.001, and a fifth, Q2-002, null on the floor alone (2026-09-19)
under five checks and the margin surface. **M12 —
the second programme — ran and is closed (2026-09-20)**: breadth by survey on the definition partition at zero
alpha, depth by registration on the measurement partition, in batch, rendered
(`TASKS-v4.md` M12); its Register ends at the author's stop (#36) and its conclusion is adopted. **M12.0–M12.4 and M12.9–M12.11 are done (2026-09-13): the first survey, 38,976 cells over four universes, is programme 2's Register record #9, rendered, and the three decisions it surfaced are adopted and built; M12.5 closed on 2026-09-14 — Q2-001 is registered from the survey at the author's floor; **on 2026-09-17 it resolved SUPPORTED, the lab's first, with a margin over always-long of −0.001 on the measurement partition recorded beside it** (the pages are rebuilt); M12.6 and M12.7 are done, and M11.7's publication check exists; M12.8 done on 2026-09-20 — a stop is a Register record, the conclusion is written from the Register after it, and programme 2's is adopted; M12.12 done on 2026-09-17: ADR-0043 makes beating always-long at the same geometry and gate the fifth check, from the next registration.**
Both programmes' conclusions are adopted (2026-09-20). **M13 — the third programme — opened (ADR-0046, 2026-09-20)**: whether a margin the screen finds transfers, on its own Register `register/programme-3.jsonl` and its own gitignored `configs/programme-3.toml`; its universes are declared and `surveys/grid-002.toml` supersedes grid-001. **M13.0–M13.4 and the readiness pass are done (2026-09-20):** the configuration declared as programme 2's, calendars and classifier frozen, grid-002 surveyed on the burst as record #9 (38,976 cells, none refused), the page and the readiness table committed, twenty Drafts with no standing. **The first registration attempt — the author's, the index-ETF `breakout_low` family — was refused UNDERPOWERED at the declared floor before any spend** (447 effective signals against 718 required); then **Q3-001 was registered by the author from the sector-ETF pullback family (#10–#11, 0.15 alpha on regime) and refused by the guard at measurement (#12): the winning cell holds 863 trades against the 1,068 the power plan requires — no verdict, the alpha spent, regime 0.05 left.** Prepare had promised the hold-1 template's signals; it now promises the sweep's thinnest cell's trades. **Programme 3 was stopped by the author on 2026-09-22 (record #13, an author's stop with its reason; an alpha stop would have been refused) and its conclusion — `docs/PROGRAMME-3-CONCLUSION.md`, no verdict — was adopted by the author the same day: M13 is closed, and three programmes are run, stopped by record and concluded.** Nothing prepares, registers, surveys or measures in that Register again. The breakout sentences no longer hard-code "no regime gate": a registered claim is the grid's sentence, and a cell file's recorded wording is stamped beside it when the two differ. Question ids are numbered by the Register's name (`programme-N.jsonl` → `QN-`; a Register named otherwise needs `--id-prefix`), so programme 3's first question is `Q3-001`. **M14 opened (2026-09-20): operational maturity from an external review, verified claim by claim** — **M14.0–M14.5 done 2026-09-21** (a pytest path line, the `slow` marker and `make test-fast`, `docs/RUNBOOK.md`, the loop's engine sha stamped before its first append with `.clu/` ignored, the seventh requirements audit in `REQUIREMENTS-v4.md` §8, a state line for a question refused at measurement); **M14.6 done and M14.7 built 2026-09-23** — `occams/register/` is a package (`store.py`, `records.py`, the two stores bound in `__init__`; no import changed, nothing recorded changed) and the burst uploads only the manifest and the bars the grid's universes need (`python -m occams survey inputs`, `BarArchive.latest_bars(names=…)`; the box-level proof waits for the next burst); five findings rejected on the facts, recorded in `TASKS-v4.md` M14 so they are not rediscovered. **The definition of done and the path to it are written in `TASKS-v4.md` after the milestone table**: the M13 decision, the stop and the conclusion, M14, the closing statement, the publication decision — every step but M14's code turning on the author's act.

## Read order

1. `README.md` — what this snapshot is; `docs/INTEGRITY.md` — how the lab
   prevents p-hacking, guard by guard with its record (M15.1);
   `docs/RUNBOOK.md` — what to do by situation (M14.2); `docs/programme.html` — what each
   programme searched, what it cost, what it found (M12.7);
   `docs/surveys/grid-001-seed20260912-readiness.md` and
   `docs/surveys/grid-002-seed20260920-readiness.md` — each survey's
   candidates under the fifth check, beside the measured priors;
   `docs/PROGRAMME-CONCLUSION.md`, `docs/PROGRAMME-2-CONCLUSION.md` and
   `docs/PROGRAMME-3-CONCLUSION.md` — what each programme established
   (adopted 2026-09-20, 2026-09-20 and 2026-09-22); `docs/LAB-CONCLUSION.md` —
   the lab's closing statement across the three (adopted 2026-09-24);
   `docs/PUBLICATION.md` — the publication decision and its amendment of
   2026-10-03; `SECURITY.md` — what a security report here is about
2. `REQUIREMENTS-v4.md` — the normative obligations
3. `DESIGN-v4.md` — the implementation shape
4. `TASKS-v4.md` — the executable sequence and gates; `docs/M0-ANSWERS.md`
   is its M0 evidence, dated 2026-09-10
5. `CONTEXT.md` — canonical language. Use these words; avoid the listed alternatives
6. `docs/adr/0001-0046` — the decisions and their rejected alternatives
7. `docs/drafts/` — proposed hypotheses. **No standing, no alpha spent** until
   a human registers one at M8.1

Within this snapshot the normative order is **ADR amendment → requirements →
design → task evidence**. A contradiction between them is a release blocker,
not a precedence question to defer. `ALIGNMENT-v4.md` is non-normative.

## The second programme — the approach (M12)

**Breadth where it is free, depth where it costs.** A **survey** runs every
declared mechanism × parameter × universe cell on the **definition
partition only** — the calibration set, which may be read (D13) — against
the always-long baseline at the same geometry, with power, era breakdown
and gate readiness per cell; in batch, seeded, resumable; recorded in the
Register at zero alpha; rendered as one static page per survey. **Nothing
in a survey is a verdict.** From a survey the author registers the cells
worth alpha as questions (`--yes` naming the ids, the mechanism sentence
as the R4.9 distinction), and the loop measures them on the **measurement
partition** with the five checks and their evidence (ADR-0043). Every cell screened
is counted beside every question registered from it (N6); the shrinkage
from screening is recorded per question; the reserve stays sealed.

- **Universes are records** (`UniverseDeclared`): index ETFs, sector ETFs,
  a declared large-cap list with its survivorship bias named, and any set
  the author adds. Each has its own frozen calendar. "Multiple histories"
  means these, side by side, and the definition partition read by era.
- **Grids are committed, hashed TOML** under `surveys/`; a grid is
  superseded, never edited. The first grid is the full set on the closed
  entry enum: breakouts, MA crosses, down-runs, return-belows, pullbacks,
  each with and without the regime gate, across holds, stops and targets.
- **A second Register and config** (ADR-0039). `register/programme-2.jsonl`
  and `register/programme-2-queue.jsonl`; `configs/programme-2.toml`,
  gitignored; the first programme's Register is never written again.
  The floor, the falsifier count and the alpha split for programme 2 are
  the author's, declared after `python -m occams whatif --archive archive
  --register register/programme-2.jsonl` shows the falsifier arithmetic —
  P(first N verdicts all null | base rate) — and the universe
  affordability table. Recommend none. Every command takes `--config`.
- **Everything the first programme learned is enforced, not remembered:**
  a gate is shown passable before alpha moves; the calendar is frozen
  before the first cut; ρ is measured; the seed is required; a kind is
  added only by ADR.
- **Big surveys run on the burst** (`tools/aws/burst.sh`, M12.3b): a spot
  instance with an S3 checkpoint that resumes on failure; the box never
  records — `survey record` runs here after every file is verified. Its resources exist only around a run: `setup` before, `teardown --all` after.
- **The outputs are pages, committed:** the survey page, the console with
  a Surveys section and the shrinkage table, the programme page for both
  programmes. A reader with no code can say what was asked, on what, what
  it showed, and what it cost.
- **A programme stops by record** (M12.8): the falsifier's `LabClosed`
  (the loop's, ADR-0033), or `ProgrammeStopped` by the author's act —
  its alpha exhausted, verified against the ledger, or a stated reason.
  After any of the three nothing prepares, registers, surveys or measures
  in that Register; `python -m occams conclude` writes the conclusion
  from the Register after a stopping record and refuses before one.

## Other repositories are read-only references

Read them freely for context. **Never modify them, and never push to them.**

| Repo | What it is |
|---|---|
| `prop-challenge-lab` (a sibling checkout) | The closed programme. **Complete, published, public.** Source *donor* for the vendored core — not a dependency |
| `oldschool-investor` (a sibling checkout) | Company research producing verified claims. Reference only |
| the planning vault (private, outside this repository) | The planning history (v1–v4). This repo holds the live v4 baseline |
| `MaverickHQ/occams-test-lab-history` (the `history` remote) | This lab's own history before publication. **Private and archived**; nothing is pushed there, and nothing from it goes to `origin` |

## Naming — the trap that has already caught us twice

- The project is **`occams`** (Occam's razor). **`occums`** with a *u* was a
  typo; a folder named `occums-trader` is an empty leftover.
- **`MaverickHQ/occams-trader` on GitHub redirects to the public
  `prop-challenge-lab`** — it is that repo's former name. **Never set it as a
  remote here.** Since 2026-10-03 this checkout has two remotes. `origin` is
  `MaverickHQ/occams-test-lab`, the published line on `main`: it begins at a
  single snapshot commit and has been **public since 2026-10-03**.
  `history` is `MaverickHQ/occams-test-lab-history`, private and archived (read-only since 2026-10-03), holding the full
  pre-publication history on the local branch `history-main`. **The history
  line is never pushed to `origin`**; a local pre-push hook refuses it.

## Standing rules

- **Published under a recorded decision** (R7, `docs/PUBLICATION.md`): public
  since 2026-10-03. The publication gate still binds every commit
  (`make prepublish`, `make prepublish-all`).
- **`occams.toml` is gitignored and must never be committed** — it carries the
  capital, drawdown and risk figures (R9) and the alpha split (R4).
- **No credentials, account identifiers or broker terms** in the repository
  (R5, R6).
- **Three sets of numbers are the author's alone. Do not pick or recommend
  any of them, and do not supply a default — a default is a recommendation.**
  **Money** — capital, drawdown limits, risk per position, and the
  forward-window minimum size (M0.13, R9). **Alpha** — the total, the reserve
  and the per-axis split (M0.11, R4). **The lab falsifier** — the count of
  resolved mechanism verdicts at which the lab closes (M0.18, ADR-0033). The
  system refuses to start without each.
- **A Draft is not a plan.** Anything in `docs/drafts/` carries no standing
  and has spent no alpha until a human registers it at M8.1. A Draft on a
  zero-budget axis is not registrable at all (ADR-0017).
- **Append, never overwrite.** Corrections supersede; nothing is edited away.
- **Register before measuring; state the detectable floor before running.**
- **A stop is the author's act.** `programme stop … --yes`, like the
  `--yes` at registration, is never run by an agent; a conclusion is a
  draft until the author adopts it (M12.8).
- **No agent performs `APPROVED -> LIVE`.** That transition is human-only and
  requires a signature (R1.1, R1.2).
- **History is never rewritten, on either line.** GitHub refuses a force-push
  or a deletion on `main`, and a moved or deleted release tag, for anyone; the
  private history is archived.
- **The private history never goes to `origin`.** No `git push --all`, no
  `--mirror`, no old tag. A local pre-push hook refuses any ref descending
  from the old root; a fresh clone needs the same guard before it is given
  the `history` remote.
- **A merge is made in this checkout and pushed, never on GitHub's side.** A
  server-side merge commit carries the account's web address, which the
  snapshot exists to keep out of the public line. Check a Dependabot pin
  against its release tag first.
- **Every change ends with the record.** `make check` with `.venv/bin` on the
  path, push, both CI jobs green, then the S1, S3, S10 entry in `TASKS-v4.md`;
  after a change under `docs/` or to a Pages action, `gh workflow run
  pages.yml`. The virtual environment has no `pip`: `uv pip install --python
  .venv/bin/python -e ".[dev]"`.

## Where the work is

**M0 stages 1-3 ran 2026-09-10; the evidence is `docs/M0-ANSWERS.md`.** Read
its verdict table before proposing work. Every price there is as displayed
on that date — re-check before relying on one.

**M1-M9 were built the same day (M5.0 closed by decision on 2026-09-20, not by measurement).** `make check` (tests · lint · credscan · provenance · prepublish · null · signal) and `make quickstart` are the proof; `occams/core/`
is the donor's code at a recorded hash and **is never edited here** — a
change to it is a re-vendor through `tools/vendor_core.py` with a new
PROVENANCE. `occams/config.py` has no defaults and a test that keeps it so.
**The guards read `occams/measurement.py` and nothing else**; an engine
meets that contract or it is not an engine. **`make null` must refuse and
`make signal` must accept** — if either ever changes, stop and fix the
guards before anything else (S3, S10). **The spec is the single source** (`occams/spec/`): identity is D4's nine
fields and nothing else; `to_engine` refuses the v1.8 defect by name.
**The entry enum is extended only by ADR** (ADR-0037, M3.9): nine kinds,
the last three added by decision on 2026-09-12; a kind is added, never
discovered, and every kind belongs to an auditor family or its fills are
refused. **Every source has a rights record
or it is not ingested** (`occams/data/rights.py`); an unanswered right is a
refusal. **The cost model says
which spread it holds** (`declared`, `bounded`, `measured`) and approval
refuses anything but the last two. **A proposer emits drafts and nothing
else** (`occams/proposers/`): no `register`, no `Confirmation(`, no
credentials. **The forward window executes for real
through the proposal path; the paper venue is refused by name.** **The accountant
keeps no state** (`occams/ledger/`): balances replay from the Register. **The Verdict
freezes the winner cell's hash; the template measures, the winner trades**
(ADR-0036). **The loop never registers** (`occams/loop.py`, ADR-0035). The
archive holds 120 names across four declared universes; `python -m occams question prepare` shows
power, axis sensitivity and the overlap gate before anything is spent.
**The console is built (M11.4)**: `make console` renders `docs/console.html`
from the Register — controls first, no script, no network, no money by
construction; `make console-offline` is the CI proof. **The programme page is built (M12.7)**: `make programme` renders `docs/programme.html`. **The publication gate's check exists (M11.7)**: `tools/prepublish.py`, `make prepublish`, in `make check` and CI — publishing itself stays a recorded decision (R7). **Reproduction never skips (M11.5, M11.6, 2026-09-18)**: `make reproduce-private QUESTION=…` recreates a stamped Verdict from the licensed archive on a scratch Register, or fails with the reason; `make reproduce-public` proves the pipeline on synthetic fixtures and refuses an exact-historical claim the rights forbid. **The label meets the bar through the instant gate (M4.11, 2026-09-18)**: a regime label known between two venues' closes admits the later venue's bar and refuses the earlier's in the engine. **M10 and M11.1–M11.3 are closed by decision (ADR-0044, 2026-09-19)**: the alerting path is the lab's own pages, the execution host is deferred outside this lab, `FORWARD` is a record; nothing trades. **The surface the sweep optimises is the margin over always-long (ADR-0045, 2026-09-19)**: the winner, the plateau and leave-one-out are judged on it; the floor stays absolute EV.

- **M1 is unblocked** on the R1.7 default build: M0.14 recorded a go at
  $129.17 of the $150 cap over twelve months, data at $0 (Tiingo Starter,
  US-listed), no execution host.
- **Two no-gos inside the cap are the author's to resolve**: M11's TradingView
  line, and the credentialed execution host (ADR-0030). Do not propose a cap
  figure; do not redesign M11 without an ADR.
- **`cross_sectional` stays at 0** — now on sample size as well as money
  (M0.15). DRAFT-001 and DRAFT-002 remain Drafts.
- **M0.11, M0.13 and M0.18 are in** (2026-09-10) — the author overrode the
  three-numbers rule once each and adopted derived sets; the values live in
  the gitignored `occams.toml` only. **The rule stands for every future
  change to them.** `python -m occams` starts. **`python -m occams whatif
  [config ...]` shows what a candidate set implies before it is adopted**;
  scenarios live in the gitignored `configs/`. A registered question is
  stamped with its config; changing alpha, partitions or the falsifier after
  that is a recorded decision, not a re-run.
- **M5.0 is closed by decision (2026-09-20):** no account is used in this lab
  and no order is placed (ADR-0044), so the cost model stays on the `bounded`
  basis with the M0.2 declared ranges as its provenance — the basis every
  verdict carries. A measured spread is the first act of any programme that
  trades; it is never substituted by a recommended figure.
- **The first real verdict is in: Q-003 (DRAFT-003) resolved NULL on
  2026-09-11** — beats-null and the floor refused; the record and its
  evidence are in `register/register.jsonl`. **A pooled set needs at least
  three names** or registration refuses it, and **a plateau the sweep cannot
  hold** is refused the same way. **Q-004 (2026-09-12) resolved NULL** — the
  same mechanism on SPY, QQQ and DIA, stop axis only, superseding Q-003:
  EV −0.045 net R over 2,088 trades, every check refused with evidence.
  **The falsifier stands at 2 of 3: the next null mechanism verdict on any
  axis closes the lab** (ADR-0033). **A price_daily question is prepared
  and not recommended** (DRAFT-004, 2026-09-12): the `PriceProposer`
  exists, `question prepare --axis price_daily` works, three candidates are
  powered or nearly so, and the definition partition puts every one of
  them at or below zero gross against a floor of +0.15 net R. **DRAFT-005
  (`DOWN_RUN`, reversal after a streak, ADR-0037) is the first with
  positive gross cells on the definition partition, was REGISTERED as
  Q-005 and RESOLVED NULL (2026-09-12)**: EV +0.051 net R over 893 trades,
  beats-null and plateau passed, the floor (+0.15) and leave-one-out
  (carried by IWM) refused. **The third null: `LabClosed` is in the
  Register and the lab is closed (ADR-0033).** Registration after it is
  refused by name; the loop stops; the console shows it. **The calendar is
  frozen (ADR-0038)**: every partition is cut from the `CalendarFrozen`
  record (1993-01-29 → 2026-09-10); `python -m occams calendar show`.
  **The programme conclusion is drafted from the Register**
  (`docs/PROGRAMME-CONCLUSION.md`, 2026-09-12) and was adopted by the author
  on 2026-09-20, with what changed since the draft appended.
- **Programme 2 (M12), where it stands on 2026-09-13.** **M12.0 closed
  (ADR-0039):** its own Register `register/programme-2.jsonl` and queue;
  its config the gitignored `configs/programme-2.toml`, declared by the
  author as programme 1's values byte for byte (sha `56592c718bea`);
  every command takes `--config`; the console renders both programmes.
  **M12.1 done:** four universes are records, each frozen on its own
  calendar — `index_etfs` (4), `sector_etfs` (11), `dow_30` (30) and
  `sp_100` (101, both with survivorship named in the same words); 120
  symbols archived, 122 of 500 this month. **M12.1b done, M12.1c closed:**
  the source serves no delisted history and a reassigned symbol serves
  its new holder — *a symbol is not an identity*; survivorship stays a
  named bias at $0. **M12.2 done:** the first grid `surveys/grid-001.toml`
  (sha `b98ce89d7cd8`), 1,920 families, 38,976 cells; a grid is never
  edited; `python -m occams survey show`. **M12.3 done:** the runner
  (`survey run`, definition partition only by construction), programme
  2's classifier frozen on SPY alone (record #8, `0434836a176a`), and
  **the first survey is record #9** — computed in 47 minutes on an AWS
  spot burst by the reusable `tools/aws/burst.sh` (S3 checkpoint, resume
  on failure, no credential leaves this machine, `--no-record` there and
  `survey record` here); the Mac's 20,271 cells match at trade level. **The burst's resources were torn down on 2026-09-13; `setup` recreates them.**
  **What the survey surfaced, the author's to decide (M12.9–M12.11):**
  every `breakout_low` cell is refused by the overnight-gap auditor (the
  limit fill model); the fill audit samples the first 500 fills in name
  order; flat bars in the sector and S&P 100 histories (C's 1996 is
  close-only prints). **ADR-0040–0042 were adopted and built the same day:** a resting limit the bar opens through fills at the open, in both engines and never in `core`; the fill audit is exhaustive and an unobtainable entry is a *missed* trade — both engines return `Trades` with `.missed`, every survey cell and baseline counts them by name, `Unobtainable` no longer exists; the flat bars are named in superseding universe records #10 and #11, no calendar moved. The engine code hash changed; record #9's cells carry none (the box ran before the stamp). **The screen's standout** is reversal after a
  four-day down-run on single names; a screen is not a verdict. **M12.4
  done (2026-09-13):** the survey page `docs/surveys/grid-001-seed20260912.html`
  (`make survey GRID= OUT=`; trust, never profit; four cells in full per
  universe with what registering each would cost) and the console's
  Surveys section. **M12.5 built 2026-09-13, closed 2026-09-14:** `python -m occams survey candidates` lists one gate-ready cell per family with the accountant's price and writes Drafts with no standing under `docs/drafts/survey/`; `python -m occams question register --from-survey … --ids … --floor-ev X --floor-frequency Y --by NAME --yes` registers one question per family through the accountant, the cell's sentence as the R4.9 distinction, the screened-cell count stamped on the record (N6), the universe's own calendar and members for pre-commit and measurement. The floor has no default: it is the author's, declared at that command. **The author declared it on 2026-09-14 — 0.15 net R and 50 a year, programme 1's pair — and registered Q2-001** from cell `f2199b5b297d85bb` (sp_100, reversal after a four-day down-run in the up regime, hold 5, stop 2 %): POWERED at k 15, alpha 0.15 on regime with 0.05 left there, 38,976 cells stamped, records #12–#13, queued in `register/programme-2-queue.jsonl`. The engine hash at registration is `4db62afbf0480200` (the survey runner file changed for M12.8's guard; no engine behaviour changed). **M12.6 done (2026-09-13):** the loop runs only with a declared `--seed`; after every verdict it appends `EraDecomposition` (the winner's three eras on the measurement partition, each held out, its missed entries by name) and, for a question from a survey, `Shrinkage` (the cell's definition EV and margin beside the measured ones against always-long at the winner's geometry); the console card shows the survey cell, the shrinkage, the eras and the missed entries, and the position section carries the shrinkage table. **M12.7 done (2026-09-14):** `python -m occams programme` (`make programme`) renders `docs/programme.html` — what did we search, what did it cost, what did we find, for both programmes, every verdict beside its survey cell or marked as from a Draft. **M11.7 done:** `tools/prepublish.py` (`make prepublish`, in `make check` and CI) is the publication gate's check on every committed page and Register: no script, network, credential shape, broker term, raw bars or money key; publishing stays a recorded decision. **M12.8 opened and built (2026-09-14), closed 2026-09-20 on the author's stop (#36) and adoption:** the three stopping conditions are each a record — `LabClosed` (the loop's) and `ProgrammeStopped` (`python -m occams programme stop --kind alpha|author … --by NAME --yes`; an alpha stop is verified against the ledger, an author's stop names its reason; nothing appends without `--yes`); after any of them nothing prepares, registers, surveys or measures in that Register; `python -m occams conclude --register R --out PATH` writes the conclusion from the Register with the survey layer and is refused until a stopping record exists; never overwrites. **`whatif` was run on programme 2's config on 2026-09-14** with the archive and Register, before any floor is declared: the falsifier arithmetic and the universe affordability it showed are in the task list's log of that date, money excluded; the table prints one row per universe since the same day. The floor, the falsifier count and the alpha split stay the author's; nothing was declared. **Q2-001 resolved SUPPORTED on 2026-09-17** (records #14–#24, seed 20260917 by the date convention): winner hold 20 / stop 2 %, EV +0.213 net R over 6,946 trades, 412.7 a year, all four checks passed, eras +0.188 / +0.288 / +0.162, one missed entry (C), the Strategy at `FORWARD`. **The shrinkage record beside it:** always-long at the winner's geometry and gate makes +0.214 on the same partition — the margin is −0.001 (it was +0.239 on the survey's definition cell). The beats-null null is random entry with a coin-flip side; the always-long comparison is long-only, and there the entry signal adds nothing. The margin is a recorded diagnostic, not one of the four checks; the verdict stands; making it a gate is the author's decision by ADR, for future questions only. The engine sha on the verdict carries `-dirty` from the donor's `git status --porcelain` (the untracked `.clu/` and the Register appended mid-run); the engine code hash is the clean `4db62afbf0480200`. Falsifier 0 of 3 null; regime has 0.05 alpha left, price_daily 0.20; the queue is empty. **ADR-0043 adopted and built (2026-09-17, M12.12 done):** beating always-long at the same geometry and gate is the fifth check — `Measurement.baseline_ev`, `guards/beats_always_long.py`, five names in `forward.CHECKS`, both engines and the synthetic control supply the distribution, a verdict names the checks it was judged against, `prepare` shows the baseline on the definition partition; it binds from the next registration and Q2-001 is not re-judged. **Readiness under the fifth check (2026-09-18):** `survey candidates … --fifth-check` re-runs always-long at each candidate's geometry and gate on the definition partition, the guard's Monte Carlo and the margin per era, at zero alpha; on grid-001's 20 candidates all 20 pass with positive margins in every era — including Q2-001's cell, whose measured margin was −0.001 — so the screen's statistic did not predict transfer and the definition eras gave no warning; the table is `docs/surveys/grid-001-seed20260912-readiness.md`. Q2-001's EV barely moved; always-long at the winner's geometry (hold 20, the longest, chosen by raw EV under ADR-0036) moved from +0.016 to +0.214 between eras. **ADR-0045 adopted and built (2026-09-19, M12.13 done):** the surface the sweep optimises is the margin over always-long — every cell carries always-long at its own geometry and gate, the winner and the plateau and leave-one-out are judged on the margin, the floor stays absolute EV, the resolved record names its surface; from the next registration, Q2-001 not re-judged. **ADR-0044 adopted (2026-09-19):** M0.22 closed as a design change — the alerting path is the lab's own pages, the execution host is deferred, `FORWARD` is a record; M10 deferred, M11.1–M11.3 not built. **M12.1e closed (2026-09-19):** this lab stays above large caps. **The 20 candidates prepared at the declared floor (2026-09-18):** the regime axis buys none (0.05 against 0.15 or 0.30 per family); price_daily's 0.20 buys exactly one 15-cell family from three powered down-run families with no gate — index ETFs `78e13cce5e21fb83`, S&P 100 `f8500a69db544a3c`, Dow 30 `7d8f04aa2066452a` — after which every axis is exhausted for every survey family. **Q2-002 (2026-09-19):** registered by the author from the S&P 100 ungated down-run family `f8500a69db544a3c`, the last question price_daily's alpha buys; **resolved NULL on the floor alone** with seed 20260919 (records #27–#35) — the winner by margin is hold 5 / stop 2 %, EV +0.109 net R over 12,732 trades, the plateau, beats-null, leave-one-out and beats-always-long all passed, the floor refused; measured margin over always-long +0.075 against the screen's +0.201; eras +0.100 / +0.156 / +0.067. Beside Q2-001: chosen by EV, that one cleared the floor where the entry added nothing; chosen by margin, this one beat always-long and missed the floor. The falsifier stands at 1 of 3 null; 0.05 alpha on each axis, no survey family affordable; the queue is empty. **Programme 2 stopped by the author on 2026-09-20 (#36)** — "every family the survey holds is beyond both axes; the two verdicts, one by each winner rule, have answered what grid-001 could ask at this floor" — and **its conclusion is drafted** (`docs/PROGRAMME-2-CONCLUSION.md`, from the Register, the author's to adopt). Nothing prepares, registers, surveys or measures in that Register again. **M12.8 closed 2026-09-20: the author adopted the conclusion; M12 is closed.** **M13 opened (2026-09-20, ADR-0046); M13.0–M13.4 done the same day.** `configs/programme-3.toml` is programme 2's configuration byte for byte, declared by the author (sha `56592c718bea`, gitignored); the four universes (#0–#3), their calendars (#4–#7) and the classifier (#8, hash `0434836a176a`, seed 20260920) are records; **grid-002 (sha `1716f9f1c506`) is survey record #9** — 38,976 cells on the corrected engine, computed on the burst with `CONFIG=configs/programme-3.toml REGISTER=register/programme-3.jsonl tools/aws/burst.sh …` (the scripts take the Register as a parameter since today) and torn down after: no cell refused (8,924 on grid-001), `breakout_low` measurable with 1,235 held cells, 3,992 held in all, and grid-001's twenty candidates unchanged to ±0.002. The survey page is `docs/surveys/grid-002-seed20260920.html`. **Readiness done (2026-09-20):** `docs/surveys/grid-002-seed20260920-readiness.md` — twenty candidates, fourteen of them `breakout_low` families, all passing the fifth check on the definition partition, programme 2's two priors cited beside them; seventeen of the twenty are 30-cell families at 0.30 against 0.20 per axis as declared, three are 15-cell on the regime axis. **Q3-001 (2026-09-20):** registered by the author from `e02384ae41677547` (sector ETFs, pullback in trend in the up regime, hold 10, stop 2 %; records #10–#11, 0.15 on regime, k 15) and refused by the loop at REGISTERED→MEASURED with seed 20260920 (record #12): the winning cell holds 863 trades on the measurement partition, the power plan requires 1,068; no verdict, the question stays REGISTERED, the alpha spent, regime 0.05 left, price_daily 0.20. Prepare had counted the hold-1 template's signals (2,187 → 2,327 effective); it now bounds `available_n` by the sweep's thinnest cell from the survey (`bound_by_thinnest_cell`), and the Draft path does the same since 2026-09-23 (`precommit(…, sweep=)` runs the sweep's cells on the definition partition; M13.9). Under the bound Q3-001's family is UNDERPOWERED (293 effective against 1,068) and the S&P 100 down-run family stays POWERED but the regime axis holds 0.05 against its 0.15: at the declared numbers nothing on grid-002 is registrable in programme 3. **Stopped by the author 2026-09-22 (#13):** "At the declared numbers no family on grid-002 is registrable … Whether a margin the screen finds transfers was not answered on this grid at these numbers." The conclusion (`docs/PROGRAMME-3-CONCLUSION.md`: no verdict, one question, one survey, 0.15 spent; five findings that outlast it) was adopted by the author on 2026-09-22 — M13 closed. **M13.9 built 2026-09-23; the lab's closing statement (`docs/LAB-CONCLUSION.md`) was adopted by the author on 2026-09-24.** **M15 opened (2026-09-24): the lab for others.** The research lab is done but for the publication decision; M15 packages it for four audiences — hedge fund research teams (integrity, seen), prop firms (rules as guards, by ADR), independent quants (run it on your own bars in an afternoon), retail traders (the negative result, told well) — and builds the setup path a stranger needs — **built 2026-09-24 (M15.4):** `make setup`, `python -m occams init` (a skeleton with placeholders, never a value; never overwrites), `python -m occams doctor` (what is missing, by name; never a secret), `docs/SETUP.md` (eight steps, clone to burst), `tools/aws/burst.env.example` (every variable, no value); the clean-machine proof passed on the CI machine on 2026-09-26. **M15.0 done 2026-09-24, extended 2026-09-26:** `README.md` is the front door — what is published here and what is not, what it found, what it refuses, what a stranger gets by cloning it (three ways, increasing cost), what the output looks like (real output, captured), run it in five minutes, set it up — with the build below. **M15.1 done 2026-09-24:** `docs/INTEGRITY.md` maps nineteen ways a backtest lies to the guard, its code and the record that showed it. **The author's decisions of 2026-09-26:** M15.6, M15.7, M15.8 and M14.7's proof closed by decision (each reopens by an ADR, M15.8 with the author's numbers); M15.12 held for review after the rest close; **M15.4's proof, M15.5, M15.9, M15.10 and M15.11 done 2026-09-26** on the author's instruction, end to end: the clean-machine job in CI; `ingest --csv` under a user-declared rights record kept in the archive; `question remeasure` — a rolling window inside the measurement partition, records in a rolls Register beside the programme's, never a verdict; `surveys/grid-template.toml` and `docs/EXTENDING.md`; `docs/EXPLAINER-Q2-001.md`. No number chosen, no Register written, no ADR adopted, nothing published. **M15.12 decided 2026-09-26: publish** — `docs/PUBLICATION.md` in the author's name; the Pages source and the repository's visibility are the author's settings on GitHub, and the `pages` workflow deploys only because the record exists. **The lab is done by its own definition (`TASKS-v4.md`, *Definition of done*).** **Where it stands on 2026-09-27:** the lab is done, the decision is publish, and the repository is hardened for the flip (commit `0e26060`, CI run `36340947417` green): the eight workflow actions pinned by commit, the Pages write permissions scoped to the deploy job, `SECURITY.md`, Dependabot for actions and pip, `.mcp.json` and `.claude/settings.local.json` ignored. A read-only pre-publication audit the same day found no secret in the tree or in the 219-commit history and four accepted exposures the author confirms before the flip: the studio's e-mail on the first two commits (history is never rewritten), the venue's name and an article id in dated evidence by recorded decision, the donor's figures in a fixture. After the flip, the author's settings: secret scanning with push protection, Dependabot alerts, private vulnerability reporting, a ruleset on `main` requiring the two checks and blocking force-pushes, a restricted Actions policy, the Pages source; then `gh workflow run pages.yml` on the author's word. **On 2026-09-30** the README gained the rendered site's address (`https://maverickhq.github.io/occams-test-lab/`, live with the `pages` dispatch) and a table of where to find things, the package became 1.0.0 (engine code hash unchanged), and the release is tagged `v1.0.0` with a GitHub release and an About — description, homepage, topics; the flip itself remains the author's act. **On 2026-10-03 the author decided the public repository carries no history:** a single snapshot commit, so the studio's address on the first two commits is never published; the venue's name, the article id and the donor's figures stay as kept by recorded decision. The full history remains private and whole; the commit ids in the log and the `engine_sha` stamps refer to it; the snapshot goes only to a repository that has never held the old commits (a force-push over the existing remote would leave them reachable through the tag, the release and by id). From the snapshot on, history is never rewritten. **Done the same day on the author's choice ("Rename and replace"):** the repository that carried the history is now `MaverickHQ/occams-test-lab-history` (private, head `21a7d66`); a fresh `MaverickHQ/occams-test-lab` holds the snapshot `d14ad4b` (CI run `37125612092` green) and the commits after it; `v1.0.0` and its release are on the published line. **Published 2026-10-03:** the author set `MaverickHQ/occams-test-lab` public; the archive stays private. Set the same day: secret scanning with push protection, Dependabot alerts and security updates, private vulnerability reporting, three rulesets (no force-push and no deletion on `main` for anyone; the `check` and `setup` checks before a merge, with the admin's bypass for direct pushes; a release tag is never moved or deleted), an Actions policy of GitHub-owned and verified actions only, and the Pages source. The site is live at `https://maverickhq.github.io/occams-test-lab/` (pages run `37126438066`; all 109 links on its index answer). Five Dependabot pull requests opened that day were merged on the author's word (merge head `1c9d900`, CI run `37130491074` green): `actions/checkout` 7.0.1, `actions/setup-python` 7.0.0, `actions/upload-pages-artifact` 5.0.0, `actions/deploy-pages` 5.0.1, each pinned by commit, and the `ruff` pin moved to 0.16.9; the site was redeployed with the new actions (pages run `37130499783`). **A merge is made locally and pushed, never on GitHub's side**, where the commit would carry the account's web address. The history repository is archived: read-only. `docs/PUBLICATION.md` carries the author's amendment of 2026-10-03 (appended, nothing above it edited): the public repository has no history before publication, and why. On 2026-09-26/27 this tree also served as the test bed for an unrelated tool; every artefact of that trial was removed on 2026-09-27 and nothing of it was ever tracked. Nothing else is open. **M15.3 done 2026-09-26:** `tools/prepublish.py --all` walks every committed text file and a hit is kept only by an entry in `tools/publication-decisions.toml`; the author applied the recommended set — `.council/` removed, the venue's name out of the code and the requirements, the vault and home paths out of the living documents, 306 hits kept by 24 recorded decisions — and the scan reports zero unresolved; history is unchanged and stays so. **M15.2 built 2026-09-24:** `make site` renders `docs/` into `build/site` (106 pages, no script, no network, both themes) and refuses if any page fails the publication check — clean since M15.3; `.github/workflows/pages.yml` deploys on manual dispatch only and never without `docs/PUBLICATION.md` recording the R7 decision. The rows are `TASKS-v4.md` M15; nothing in M15 writes a Register or changes a number; **the publication decision (R7) is M15.12 and closes the lab** — the repository's visibility is the author's act.
  M5.0, M0.22 and M0.21(c) are closed (2026-09-20): by decision, by ADR-0044, and
  by the author's confirmation — the EDGAR contact string lives in the macOS
  Keychain under `EDGAR_CONTACT`, beside the Tiingo key, and is read the same way.
  120 names are archived, 119 across four declared universes and SHLD (the
  2023 fund, no universe) from the M12.1b probe; programme 1's classifier
  is frozen at `0434836a176a` and regime has 0.14 of 0.20 left there. The loop takes `--seed N` and refuses to run without it (M12.6). The M0 rows
  carry dated state markers; *Constraints recorded by M0* lists the facts
  later milestones must not rediscover.
