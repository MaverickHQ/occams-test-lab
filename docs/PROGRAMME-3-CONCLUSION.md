# Programme conclusion — what 0 verdicts established

**Dated 2026-09-22. Adopted by the author on 2026-09-22** (M13.8); §3's remainder and §4–§6 were drafted from the Register and the task list's log on the author's instruction and adopted with the document. Written from `programme-3.jsonl` because a stopping condition is a record in it (M12.8): the author (MaverickHQ) stopped it: At the declared numbers no family on grid-002 is registrable: the one question the regime axis could buy, Q3-001, was refused at measurement before a verdict, and what remains on either axis affords no survey family. Whether a margin the screen finds transfers was not answered on this grid at these numbers — record `#13`, 2026-09-22 11:54 UTC. Nothing here is new analysis. Every number below is in the Register; the record number is given as `#n`. The Register holds **14 records**, chain-verified, head `e92fda14a7f1`, from 2026-09-20 13:35 UTC to 2026-09-22 11:54 UTC. No money appears in it and none appears here (ADR-0008, S7).

## 1. The scoreboard

1 question registered by the author, 0 measured on a partition no one looked at before registration, 0 resolved by the machine against a floor declared before the run. The falsifier was declared as 3 null mechanism verdicts before the first question; it stands at 0.

| | `Q3-001` |
|---|---|
| axis | regime |
| tier | mechanism |
| mechanism | After a close below its 20-bar average while above its 200-bar average, a US sector ETF carries positive EV in net R over the next 10 bars because a dip inside an uptrend is bought back (reversal conditioned on trend; ADR-0037) — inside the up regime of the classifier frozen on SPY (F11) |
| universe | sector_etfs |
| names | — |
| measurement span | — |
| origin | survey cell `e02384ae41677547` of results `f5b7a3470c77`, 38,976 cells screened |
| engine | — |
| search space k | 15 |
| alpha spent | 0.1500 (#10) |
| required / available N | 1,068 / 2,327 (#11) |
| trades measured | — |
| seed | — |
| floor declared: net R, trades per year | 0.15, 50 |
| EV per trade, net R | — |
| trades per year | — |
| beats-null | — |
| plateau | — |
| floor | — |
| leave-one-out | — |
| beats-always-long | — |
| outcome | registered, refused at measurement, unresolved — the winning cell holds fewer trades than the power plan requires (n 863, required_n 1,068; #12) |
| winner chosen by | — |
| paths archived | — |
| eras on the measurement partition | — |
| shrinkage from screening | — |

**The survey layer.** Breadth on the definition partition at zero alpha; nothing in a survey is a verdict; every cell screened is counted beside every question registered from it (N6).

- `grid-002`, grid `1716f9f1c506`, seed 20260920: 38,976 cells over dow_30, index_etfs, sector_etfs, sp_100; results `f5b7a3470c77`; classifier `0434836a176a` (#9). Questions registered from it: `Q3-001` (cell `e02384ae41677547`).

Cells screened: 38,976 across 1 survey(s), stamped on every question registered from them (38,976 in all, N6); questions registered: 1; verdicts: 0.

**Lab-level records.** The classifier: index-level on SPY, short 20, long 100, band 0.01, frozen on the definition partition 1993-01-04 to 2003-02-12, regime shares down 24.0 %, ranging 18.9 %, up 57.1 %, persistence 0.970 (#8). The universes, each the latest record under its name: `index_etfs` — 4 names, us_large, tiingo-starter; bias: currently-listed only; all four have survived, which is the class's one declared bias (M0.7); index ETFs carry no single-name survivorship (#0); `sector_etfs` — 11 names, us_large, tiingo-starter; bias: currently-listed only; the sector set is rules-based and complete, so no selection bias beyond the class's own; XLRE (2015-10) and XLC (2018-06) listed late and contribute to the later partitions only (#1); `dow_30` — 30 names, us_large, tiingo-starter; bias: survivorship by construction: a current membership list contains only names that survived and prospered to 2026; every historical verdict on this set is conditioned on that selection and says nothing about the names the index dropped (#2); `sp_100` — 101 names, us_large, tiingo-starter; bias: survivorship by construction: a current membership list contains only names that survived and prospered to 2026; every historical verdict on this set is conditioned on that selection and says nothing about the names the index dropped (#3). The calendars: [index_etfs] 1993-01-29 to 2026-09-11, definition to 2003-03-02, measurement to 2019-12-23, reserve after, split 0.3 / 0.5 / 0.2 (#4); [sector_etfs] 1998-12-22 to 2026-09-11, definition to 2007-04-17, measurement to 2021-02-25, reserve after, split 0.3 / 0.5 / 0.2 (#5); [dow_30] 1993-01-04 to 2026-09-11, definition to 2003-02-12, measurement to 2019-12-17, reserve after, split 0.3 / 0.5 / 0.2 (#6); [sp_100] 1993-01-04 to 2026-09-11, definition to 2003-02-12, measurement to 2019-12-17, reserve after, split 0.3 / 0.5 / 0.2 (#7). 

**Alpha.** Spent: 0.0000 of the 0.20 declared on price_daily; 0.1500 of the 0.20 declared on regime; the reserve declared at 0.10 (the author's build, from the configuration the questions were stamped with). The reserve was never looked at (ADR-0006).

**The archive.** 120 names from tiingo-starter; no question consumed a name; no bars in the repository.

**The controls.** Before every verdict the same pipeline refused a dead world and accepted a planted edge on both engines (S3, S10), and does so again on every build of the console (`docs/console.html`); they are not re-run here.

## 2. What the Register establishes

No verdict. 1 question registered, 0 measured, none resolved: the programme stopped before a verdict, and the Register establishes nothing about any mechanism.

## 3. What is not established

- **Anything about the reserve.** Sealed, never looked at (ADR-0006): no reserve look is in the Register.
- **Obtainability in a forward window.** No forward window was opened; no Strategy passed MEASURED.
- **38,975 of the 38,976 cells screened.** Registered from them: 1. A screen is not a verdict; a cell not registered has no standing and says nothing.
- **The universes no question was registered on: `dow_30`, `index_etfs`, `sp_100`.** Declared and surveyed, not measured.
- **The question ADR-0046 asked — whether a margin the screen finds
  transfers to the measurement partition.** Not asked to a verdict: the
  one question registered never reached the checks. The margin surface,
  the fifth check and the readiness pass were built for it and stand
  ready; the numbers this programme declared could put one family in
  front of them, and the measurement partition could not power that one.
- **Nineteen of the twenty readiness candidates.** Seventeen are 30-cell
  families and cost 0.30 against the 0.20 declared per axis, whatever
  their power — every price_daily candidate among them, so that axis
  bought nothing on this grid; the index-ETF `breakout_low` family was
  refused UNDERPOWERED at the declared floor before any spend (the
  attempt of 2026-09-20); the S&P 100 four-day down-run family, Q2-001's
  cell, was powered and affordable and was not the one the author
  registered. After `Q3-001` the regime axis held 0.05 against its 0.15.
- **Every `breakout_low` family.** Measurable for the first time on the
  corrected engine (ADR-0040): 1,235 cells held on the screen, fourteen
  of the twenty candidates, none measured.
- **Whether prepare's corrected promise would have changed the choice.**
  Under the thinnest-cell bound (2026-09-20) `Q3-001`'s family reads
  UNDERPOWERED — 293 effective against 1,068 — and the S&P 100 down-run
  family stays POWERED; that arithmetic came after the registration and
  says nothing about what the author would have registered with it.

## 4. The findings that outlast the questions

**Prepare must promise what the guard will count.** Registration's power
plan took the family's template — its first hold, one bar — and scaled
its 2,187 definition-partition signals to 4,469 on the measurement
partition, 2,327 effective; the guard at measurement counts the winning
cell's own trades, and a hold-10 cell of a signal that persists for days
holds 863 (#12). The two numbers were never the same quantity. The
survey had every cell's count all along — the registered cell at 517, the
sweep's thinnest at 276 — and now `question prepare` promises the thinnest
cell's trades and prints both. The refusal cost 0.15 alpha and was the
first refusal at `REGISTERED -> MEASURED` in three programmes; the guard
did exactly what M8.2 asked of it.

**A gate that passes "some floor" says nothing about the declared one.**
The screen's readiness column is keyed by k = 4 and 9 and passed a cell any
floor could afford; the declared floor at k = 15 is checked at prepare,
which refused the index-ETF `breakout_low` family before a spend. The two
answers were consistent and the second was the only one that mattered.

**The claim registered is the grid's sentence, not the cell file's.** A
proposer template that hard-coded "with no regime gate" put "…with no
regime gate … inside the up regime" on fifteen of twenty Drafts and in
record #9's cell files, which are under the results hash and stay as
written. Registration now takes the sentence from the grid and stamps the
recorded wording beside it when the two differ; nothing recorded was
rewritten.

**Numbers declared for one grid's shape price another's families.** This
programme took programme 2's configuration byte for byte and grid-002 made
targets measurable, so seventeen of twenty readiness candidates were
30-cell families at 0.30 against 0.20 per axis. The Register records the
fact and does not say what the numbers should have been.

**The definition partition still predicts nothing about transfer.** All
twenty candidates passed the fifth check there with a positive margin in
every era, beside programme 2's two measured priors, as all twenty of
grid-001's had; the one registered never reached the check. Two
programmes have now shown the readiness pass to be necessary and not
sufficient, and it stays a readiness pass.

**What was found was found on the way.** The question-id prefix was a
constant and would have numbered this programme's first question as the
second's; the engine sha on every verdict carried `-dirty` from the
loop's own appends; the burst scripts hard-coded programme 2's Register.
Each is a parameter, a stamp or a derivation now, with a test. No verdict
was reached on a defect that was known at the time, because no verdict
was reached.

## 5. The decision

The author stopped the programme on 2026-09-22 (#13): *at the declared
numbers no family on grid-002 is registrable: the one question the regime
axis could buy, `Q3-001`, was refused at measurement before a verdict, and
what remains on either axis affords no survey family; whether a margin the
screen finds transfers was not answered on this grid at these numbers.*
The ledger's arithmetic sits beside the record — 0.05 on regime and 0.20
on price_daily against a smallest charge of 0.04 — so it is the author's
stop, not an alpha stop, and an alpha stop would have been refused; the
falsifier stands at 0 of 3. Alpha left unspent: 0.05 on regime, 0.20 on
price_daily; the reserve of 0.10 untouched.

No ADR was adopted during the programme; ADR-0046 opened it and the three
corrections it forced — the sentence, the id prefix, the power promise —
are code with tests, recorded in the task list's log, none of them a
change to a number or a rule. What follows is the lab's: the closing
statement across three programmes, the two deferred items of M14, the
fate of the Draft path's power promise, and the publication decision
(R7) — the author's acts, and the Register does not choose among them.

## 6. Was it worth doing?

One survey of 38,976 cells on the corrected engine, computed on the burst
in about an hour and a half and recorded at zero alpha, with no cell
refused where 8,924 had been and grid-001's twenty candidates reproduced
to ±0.002 — the corrected engine changed what could be measured, not what
the screen ranked. One registration, one refusal, no verdict: 0.15 of
alpha for the first refusal at measurement the lab has recorded, which
exposed a promise prepare had made in every programme and could not keep
on a persisting signal. Three defects found by trying to register and
fixed the same day with tests; a readiness table with two measured
priors beside it; and, in the programme's wake, a runbook, a seventh
requirements audit, a fast cycle, an engine sha that reports the tree the
run began on, and a name for a question refused at measurement. The
question the programme was opened to ask is where it was on the day it
opened, with the apparatus to ask it ready and the numbers to afford it
undeclared. That is less than the second programme bought and it is not
nothing: a registration path that can no longer promise what the guard
will not count, proven on the one question it let through.

---

Generated by `python -m occams conclude` at 2026-09-22T11:56:25+00:00 from `programme-3.jsonl`: 14 records, head `e92fda14a7f1`, stopping record `#13` · repo `79c62b8`. Adopted by the author on 2026-09-22 on the author's instruction (M13.8 closed; M13 closed); §3's remainder and §4–§6 drafted from the record and adopted with it.
