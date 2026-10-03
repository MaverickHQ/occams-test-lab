# Programme conclusion — what 2 verdicts established

**Dated 2026-09-20. Adopted by the author on 2026-09-20** (M12.8); §4–§6 were drafted from the Register and the task list's log on the author's instruction and adopted with the document. Written from `programme-2.jsonl` because a stopping condition is a record in it (M12.8): the author (MaverickHQ) stopped it: Every family the survey holds is beyond both axes; the two verdicts, one by each winner rule, have answered what grid-001 could ask at this floor — record `#36`, 2026-09-20 09:12 UTC. Nothing here is new analysis. Every number below is in the Register; the record number is given as `#n`. The Register holds **37 records**, chain-verified, head `23cf22aa6586`, from 2026-09-12 12:01 UTC to 2026-09-20 09:12 UTC. No money appears in it and none appears here (ADR-0008, S7).

## 1. The scoreboard

2 questions registered by the author, 2 measured on a partition no one looked at before registration, 2 resolved by the machine against a floor declared before the run. The falsifier was declared as 3 null mechanism verdicts before the first question; it stands at 1.

| | `Q2-001` | `Q2-002` |
|---|---|---|
| axis | regime | price_daily |
| tier | mechanism | mechanism |
| mechanism | After 4 consecutive lower closes, an S&P 100 constituent as listed on 2026-09-12 carries positive EV in net R over the next 5 bars because a streak of declines exhausts short-horizon sellers and the next days correct (reversal after a streak; ADR-0037) — inside the up regime of the classifier frozen on SPY (F11) | After 4 consecutive lower closes, an S&P 100 constituent as listed on 2026-09-12 carries positive EV in net R over the next 20 bars because a streak of declines exhausts short-horizon sellers and the next days correct (reversal after a streak; ADR-0037) |
| universe | sp_100 | sp_100 |
| names | 98 names: AAPL, ABBV, ABT, ACN, ADBE, AMAT … WFC, WMT, XOM | 98 names: AAPL, ABBV, ABT, ACN, ADBE, AMAT … WFC, WMT, XOM |
| measurement span | 2003-02-12 to 2019-12-17 | 2003-02-12 to 2019-12-17 |
| origin | survey cell `f2199b5b297d85bb` of results `80f551b4de5c`, 38,976 cells screened | survey cell `f8500a69db544a3c` of results `80f551b4de5c`, 38,976 cells screened |
| engine | position_boxed | position_boxed |
| search space k | 15 | 15 |
| alpha spent | 0.1500 (#12) | 0.1500 (#25) |
| required / available N | 2,561 / 6,286 (#13) | 8,704 / 10,944 (#26) |
| trades measured | 6,946 (#15) · 1 missed | 12,732 (#28) · 1 missed |
| seed | 20260917 | 20260919 |
| floor declared: net R, trades per year | 0.15, 50 | 0.15, 50 |
| EV per trade, net R | **+0.213** at bounded costs (#19) | **+0.109** at bounded costs (#33) |
| trades per year | 412.7 | 756.5 |
| beats-null | passed | passed |
| plateau | passed | passed |
| floor | passed | refused — EV per trade in net R is below the declared floor |
| leave-one-out | passed | passed |
| beats-always-long | not evaluated | passed |
| outcome | **supported** (#19) | **null** (#33) |
| winner chosen by | EV (before ADR-0045) | margin |
| paths archived | 2,000 draws (#18) | 2,000 draws (#32) |
| eras on the measurement partition | 2,107 at +0.188 / 2,391 at +0.288 / 2,448 at +0.162; each held out +0.225, +0.174, +0.241; 1 missed (#23) | 4,183 at +0.100 / 4,432 at +0.156 / 4,117 at +0.067; each held out +0.113, +0.084, +0.129; 1 missed (#34) |
| shrinkage from screening | EV +0.256 → +0.213 (Δ -0.042); margin +0.239 → -0.001 (Δ -0.240) (#24) | EV +0.333 → +0.109 (Δ -0.224); margin +0.201 → +0.075 (Δ -0.127) (#35) |

**The survey layer.** Breadth on the definition partition at zero alpha; nothing in a survey is a verdict; every cell screened is counted beside every question registered from it (N6).

- `grid-001`, grid `b98ce89d7cd8`, seed 20260912: 38,976 cells over dow_30, index_etfs, sector_etfs, sp_100; results `80f551b4de5c`; classifier `0434836a176a` (#9). Questions registered from it: `Q2-001` (cell `f2199b5b297d85bb`), `Q2-002` (cell `f8500a69db544a3c`).

Cells screened: 38,976 across 1 survey(s), stamped on every question registered from them (77,952 in all, N6); questions registered: 2; verdicts: 2.

| Question | Survey cell | Screened | EV, definition | EV, measured | Δ EV | Margin, definition | Margin, measured | Δ margin | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `Q2-001` | `f2199b5b297d85bb` | 38,976 | +0.256 | +0.213 | -0.042 | +0.239 | -0.001 | -0.240 | supported (#24) |
| `Q2-002` | `f8500a69db544a3c` | 38,976 | +0.333 | +0.109 | -0.224 | +0.201 | +0.075 | -0.127 | null (#35) |

Net R per trade. The definition numbers are the survey cell's on the calibration set; the measured ones are the winner cell's on the measurement partition against always-long at the same geometry.

**Lab-level records.** The classifier: index-level on SPY, short 20, long 100, band 0.01, frozen on the definition partition 1993-01-04 to 2003-02-12, regime shares down 24.0 %, ranging 18.9 %, up 57.1 %, persistence 0.970 (#8). The universes, each the latest record under its name: `index_etfs` — 4 names, us_large, tiingo-starter; bias: currently-listed only; all four have survived, which is the class's one declared bias (M0.7); index ETFs carry no single-name survivorship (#0); `sector_etfs` — 11 names, us_large, tiingo-starter; bias: currently-listed only; the sector set is rules-based and complete, so no selection bias beyond the class's own; XLRE (2015-10) and XLC (2018-06) listed late and contribute to the later partitions only (#10); `dow_30` — 30 names, us_large, tiingo-starter; bias: survivorship by construction: a current membership list contains only names that survived and prospered to 2026; every historical verdict on this set is conditioned on that selection and says nothing about the names the index dropped (#4); `sp_100` — 101 names, us_large, tiingo-starter; bias: survivorship by construction: a current membership list contains only names that survived and prospered to 2026; every historical verdict on this set is conditioned on that selection and says nothing about the names the index dropped (#11). The calendars: [index_etfs] 1993-01-29 to 2026-09-11, definition to 2003-03-02, measurement to 2019-12-23, reserve after, split 0.3 / 0.5 / 0.2 (#1); [sector_etfs] 1998-12-22 to 2026-09-11, definition to 2007-04-17, measurement to 2021-02-25, reserve after, split 0.3 / 0.5 / 0.2 (#3); [dow_30] 1993-01-04 to 2026-09-11, definition to 2003-02-12, measurement to 2019-12-17, reserve after, split 0.3 / 0.5 / 0.2 (#5); [sp_100] 1993-01-04 to 2026-09-11, definition to 2003-02-12, measurement to 2019-12-17, reserve after, split 0.3 / 0.5 / 0.2 (#7). 

**Alpha.** Spent: 0.1500 of the 0.20 declared on price_daily; 0.1500 of the 0.20 declared on regime; the reserve declared at 0.10 (the author's build, from the configuration the questions were stamped with). The reserve was never looked at (ADR-0006).

**The archive.** 120 names from tiingo-starter; the questions consumed 98 names: AAPL, ABBV, ABT, ACN, ADBE, AMAT … WFC, WMT, XOM; no bars in the repository.

**The controls.** Before every verdict the same pipeline refused a dead world and accepted a planted edge on both engines (S3, S10), and does so again on every build of the console (`docs/console.html`); they are not re-run here.

## 2. What the Register establishes

**`Q2-001` resolved supported** (#19). After 4 consecutive lower closes, an S&P 100 constituent as listed on 2026-09-12 carries positive EV in net R over the next 5 bars because a streak of declines exhausts short-horizon sellers and the next days correct (reversal after a streak; ADR-0037) — inside the up regime of the classifier frozen on SPY (F11). On `sp_100` (98 names: AAPL, ABBV, ABT, ACN, ADBE, AMAT … WFC, WMT, XOM), the measurement partition 2003-02-12 to 2019-12-17, position_boxed, seed 20260917: EV +0.213 net R per trade over 6,946 trades at bounded costs, 412.7 a year, against a floor of 0.15 net R and 50 a year declared at registration (#13). Passed: beats-null, plateau, floor, leave-one-out. Every check passed. Eras: 2,107 at +0.188 / 2,391 at +0.288 / 2,448 at +0.162; each held out +0.225, +0.174, +0.241; 1 missed (#23). From the survey: cell `f2199b5b297d85bb` of 38,976 screened; EV +0.256 → +0.213 (Δ -0.042); margin +0.239 → -0.001 (Δ -0.240) (#24). 

**`Q2-002` resolved null** (#33). After 4 consecutive lower closes, an S&P 100 constituent as listed on 2026-09-12 carries positive EV in net R over the next 20 bars because a streak of declines exhausts short-horizon sellers and the next days correct (reversal after a streak; ADR-0037). On `sp_100` (98 names: AAPL, ABBV, ABT, ACN, ADBE, AMAT … WFC, WMT, XOM), the measurement partition 2003-02-12 to 2019-12-17, position_boxed, seed 20260919: EV +0.109 net R per trade over 12,732 trades at bounded costs, 756.5 a year, against a floor of 0.15 net R and 50 a year declared at registration (#26). Passed: beats-null, plateau, leave-one-out, beats-always-long. Refused: floor (EV per trade in net R is below the declared floor). Eras: 4,183 at +0.100 / 4,432 at +0.156 / 4,117 at +0.067; each held out +0.113, +0.084, +0.129; 1 missed (#34). From the survey: cell `f8500a69db544a3c` of 38,976 screened; EV +0.333 → +0.109 (Δ -0.224); margin +0.201 → +0.075 (Δ -0.127) (#35). 

## 3. What is not established

- **Anything about the reserve.** Sealed, never looked at (ADR-0006): no reserve look is in the Register.
- **Anything about costs beyond the bounded model.** Every verdict is at bounded costs; at measured costs (M5.0) the numbers move.
- **Obtainability in a forward window.** No forward window was opened; the Strategy of `Q2-001` reached `FORWARD` and stands there as a record (ADR-0044: the execution host is deferred).
- **38,974 of the 38,976 cells screened.** Registered from them: 2. A screen is not a verdict; a cell not registered has no standing and says nothing.
- **The universes no question was registered on: `dow_30`, `index_etfs`, `sector_etfs`.** Declared and surveyed, not measured.
- *The rest of this section is the author's, written on adoption: what was not asked, and why.*

## 4. The findings that outlast the questions

**The geometry the rule picks decides which question the checks can
answer.** Q2-001's winner was chosen by EV and landed on the longest hold,
where always-long inside the up regime of 2003–2019 pays most; it cleared
the floor and the record beside it (#24) shows the entry added nothing —
margin −0.001. Q2-002's winner was chosen by margin and landed on the short
hold, where always-long is small; it beat the passive alternative at the
corrected alpha (#33) and missed the floor by 0.041 R. One rule asked
*is there money here?* and got yes for the wrong reason; the other asked
*does the entry earn it?* and got yes, not enough. The lab now asks both,
in that order.

**A screen's statistic must be the verdict's statistic.** The survey
ranked every cell by its margin over always-long (M12.3, M12.4); the
verdict chose its winner by EV until ADR-0045. The one verdict reached
under the disagreement is the one whose margin vanished.

**The always-long return at a geometry is a property of the era, not of
the entry.** At hold 20 inside the up regime it was +0.016 on 1993–2003
and +0.214 on 2003–2019 (#9, #24). No statistic on the definition
partition could see that: all twenty candidates passed the fifth check
there with positive margins in every era
(`docs/surveys/grid-001-seed20260912-readiness.md`), the one that lost
its whole margin among them.

**Four checks could not see it; a fifth can.** Beats-null draws a
two-sided null and asks *better than chance?*; the floor asks *big
enough?*; the plateau and leave-one-out ask about shape. None asked
*better than being long at the same geometry and gate?* ADR-0043 made
that the fifth check the day the verdict showed the gap, binding from the
next registration and never re-judging the one that showed it.

**Alpha priced per cell makes the family the unit of spend.** At 0.01 per
cell, a 15-cell family costs 0.15 and a 30-cell family 0.30; each axis's
0.20 bought exactly one family and could buy no second (the prepare pass
of 2026-09-18). A survey that screens 38,976 cells at zero alpha and a
budget that affords two questions are the breadth and the depth this
programme declared; the ratio is the author's, and it was the author's
to change.

**What was found was found on the way, not on a verdict.** The limit
fill model, the sampled fill audit and the flat bars (ADR-0040–0042) came
out of the survey before any cell was registered; a target family's
template that could not compile, an archive that had grown under a
reproduction, and a working tree that stamps `-dirty` on an engine sha
came out of preparing, reproducing and measuring. Each is a guard or a
record now. No verdict was reached on a defect that was known at the
time.

## 5. The decision

The author stopped the programme on 2026-09-20 (#36): *every family the
survey holds is beyond both axes; the two verdicts, one by each winner
rule, have answered what grid-001 could ask at this floor.* The ledger's
arithmetic sits beside the record — 0.05 on each axis against a smallest
charge of 0.04 — so it is the author's stop, not an alpha stop; the
falsifier stands at 1 of 3. Alpha left unspent: 0.05 on regime, 0.05 on
price_daily; the reserve of 0.10 untouched.

Decided with it, each by ADR or a dated entry: the surface a sweep
optimises is the margin over always-long (ADR-0045); beating always-long
is the fifth check (ADR-0043); the alerting path is the lab's own pages
and the execution host is deferred outside this lab, so Q2-001's
Strategy stands at `FORWARD` as a record and nothing trades (ADR-0044);
this lab stays above large caps (M12.1e). What follows is a new programme
under its own M0, its own Register and its own numbers — a second grid
screened and measured under the margin surface, a forward window only
when a host exists, publication only as a recorded decision (R7) — and
the Register does not choose among them.

## 6. Was it worth doing?

Two verdicts on ninety-eight names over sixteen years, at bounded costs,
against a floor declared before the survey ran, from a screen of 38,976
cells computed in 47 minutes for about the price of a coffee and recorded
at zero alpha. One verdict supported, and its own record — written by
the machinery this programme added for exactly that purpose — says what
the four checks could not: the return was the gate and the side, not the
entry. One verdict null on the floor alone, with the entry shown to beat
the passive alternative it was compared with. Three decisions taken from
what the survey surfaced and two from what the verdicts showed, every one
adopted before the next question was registered rather than after the
next verdict was read. The apparatus that closed the first programme on
three nulls now has five checks, a surface the screen and the verdict
share, reproduction that fails rather than skips, and a stop that is a
record. That is what the second programme bought with 0.30 of alpha, and
it is more than the first bought with 0.10: not an edge, but a lab that
could tell it had not found one, and said so in its own words.

---

Generated by `python -m occams conclude` at 2026-09-20T09:13:33+00:00 from `programme-2.jsonl`: 37 records, head `23cf22aa6586`, stopping record `#36` · repo `22727f7`. Adopted by the author on 2026-09-20 on the author's instruction (M12.8 closed); §4–§6 drafted from the record and adopted with it.
