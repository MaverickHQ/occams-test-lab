---
status: decided 2026-09-13 — adopted by the author the day it was drafted, before M12.5 opened; `audit` is exhaustive and per fill, both engines return the entries the auditor refused as `missed` and open no position on them, and every survey cell and baseline counts them by name; the verdict-side census landed with M12.6 the same day: `EraDecomposition` carries the winner cell's missed entries by name (M12.10 closed)
---

# The fill audit is exhaustive, and an unobtainable fill is a missed trade

M5.5 made the engine audit every fill it books: three refusals adapted
to daily equities — the overnight gap, the opening auction, the halt —
per strategy family, default-deny (M5.7). The principle is right and
stays. Its implementation has two properties the first survey exposed,
both in `occams/costs/auditors.py::audit`.

**1. The audit is a sample.** `audit(family, fills, actions, *,
sample=500)` checks `fills[:sample]`. The engines build `fills` in
`sorted(bars_by_name)` order, so the sample is the first five hundred
fills of the alphabetically first names. Whether a run is refused is
therefore a property of the alphabet:

- **Sector ETFs.** XLB sorts first, and its bars of 1998-12-29 (700
  shares, open = high = low) and 1999-02-26 have no printed range. Every
  ungated and every up-regime always-long baseline is refused by the
  halt auditor on one of those two bars: **2,324 cells have no margin**
  (1,162 + 1,162), and 268 sector cells are refused outright.
- **Dow 30.** AAPL sorts first and its early history is clean, so the
  ungated baselines pass — the sample never leaves AAPL. Where the
  regime gate thins AAPL's fills below five hundred, the sample reaches
  AMGN's bar of 1994-01-04: every ranging-regime baseline is refused,
  **754 cells have no margin**, and 506 cells are refused, 388 of them
  on that one bar.
- **S&P 100.** C's 254 close-only bars of 1996 sit behind AAPL, ABBV,
  ABT, ACN, ADBE, AMAT, AMD, AMGN, AMT and AMZN. They are reached only
  when the names before them fire rarely enough; AMD's own 1996 bars
  (927, 1006) and AMGN's are what the sample usually meets first. 520
  cells have a refused baseline; **1,510 cells are refused**.

Across the grid: 2,284 cells refused by the halt auditor and 3,598 with
a refused baseline, from 331 flat bars (ADR-0042), chosen by sort order.

**2. The refusal is of the whole run.** One unobtainable fill among
thousands refuses the cell. That is the right contract for the fixture
the auditor was built against — a strategy whose *rule* books fills no
order could produce — and the wrong one for a source defect on one bar
of one name in a pooled universe of eighty-three. A mechanism's
measurability should not depend on whether C's 1996 is inside the first
five hundred fills of the alphabet.

## Decision (adopted 2026-09-13)

1. **The audit is exhaustive.** Every fill the engine books is audited;
   `sample` is removed. The audit is three predicates per fill over
   trades the engine has already computed; its cost is linear and small
   against the simulation that produced them.
2. **An unobtainable fill is a missed trade.** The position is not
   opened: the engine drops the trade whose entry fill an auditor
   refuses, records it — name, bar, the auditor's sentence — as
   `missed` on the run, and continues. `Unobtainable` is no longer
   raised for a fill the engine can name; `UnauditedFamily` still is
   (a family with no auditor cannot be measured: default-deny stays).
3. **The missed count travels with the trade count.** A survey cell, a
   baseline and a verdict's evidence carry `missed` beside `trades`, per
   name and per bar, so a reader can see what the data did not let the
   strategy do. It is a diagnostic on the run, not a field of the
   `Measurement` contract the guards read.

The controls do not move: `make null` still refuses and `make signal`
still accepts (S3, S10) — neither fixture has a flat bar or a gapped
limit — and a change that moved either stops everything else (CLAUDE.md).

## Consequences

- `audit()` returns the problems it finds instead of raising on the
  fifth; the engines' `run` (both) drop the trades named and record
  them. Tests: a fixture with one flat bar among clean bars yields
  `n − 1` trades and one `missed` and is not refused; a family with no
  auditor is still refused by name; the existing fixtures for each
  auditor still name their bar.
- The survey runner's refusal census becomes a missed census: the index
  counts `missed` per universe, and the page shows it beside the trade
  count. Cells computed after the change carry a new `engine_code_sha`;
  record #9 is not recomputed.
- The consequence for the flat bars themselves is ADR-0042's: with this
  decision they cost one missed trade each where a strategy would have
  entered, named in the record, and the calendar need not move for them.
  Without it, the calendar question returns.
- Programme 1's verdicts (Q-003, Q-004, Q-005) were measured under the
  sampled audit and are closed; they are not recomputed. Programme 2 has
  registered nothing; this decision precedes M12.5 so that no registered
  question is measured under one audit and re-measured under another.

## Considered options

- **Keep the sample; take it in time order rather than name order.**
  Rejected: still a sample, still a threshold, and it trades the
  alphabet for the calendar — early-listed names and early bars would
  decide measurability instead.
- **Exhaustive, and keep the whole-run refusal.** Rejected: it makes
  measurability a property of a name's early data. Every S&P 100 cell
  that enters C in 1996 or AMD in 1996 would be refused, and the pooled
  universe would be measured on the names with clean vendor history —
  a selection nobody declared.
- **Fill at the close on a bar with no printed range.** Rejected: a
  market order placed before the open fills at the auction print, and
  a bar with open = high = low = close carries no print at the time the
  order would have filled. Booking the close invents one.
- **Drop the names or the years that carry flat bars.** That is a
  universe or calendar decision (ADR-0042), not an audit decision; the
  audit has to be right whatever the data is.
