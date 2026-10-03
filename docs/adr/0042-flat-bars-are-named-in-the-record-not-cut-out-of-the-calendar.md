---
status: decided 2026-09-13 — adopted by the author the day it was drafted, with ADR-0041; superseding `UniverseDeclared` records for `sector_etfs` (#10) and `sp_100` (#11) name the flat bars and their count, same members, rule and bias; no calendar moved; C stays (M12.11 closed)
---

# Flat bars are named in the record, not cut out of the calendar

A **flat bar** here is a daily bar with no printed range — open = high =
low — or no volume. The halt auditor (M5.5) refuses a fill on one:
nothing fills in a bar that did not trade, and a bar whose open, high
and low are the same number carries no print an order could have met.
The auditor is right. What the first survey showed is where such bars
are, and what refusing them costs under the audit as implemented
(ADR-0041).

**The census**, over the four universes' definition partitions, taken
2026-09-12 and re-taken per name for this record:

| universe | flat bars | where |
|---|---|---|
| index_etfs | 0 | — |
| sector_etfs | 3 | XLB 1998-12-29 (700 shares) and 1999-02-26; XLI 1999-01-26 (no volume). Days 5 and 45 of a calendar that starts 1998-12-22 |
| dow_30 | 9 | seven names: DIS 3 (2001-08-30 → 2002-01-16); AMGN 1994-01-04; KO 1993-04-16; CAT, CVX, PG and SHW all on 1998-05-20 |
| sp_100 | 319 | 28 names: **C 254 — every bar of 1996**, real volume and a different close each day, open, high and low collapsed onto the close; AMD 11 (1996); DHR 10 (1993–97); GILD 6 (three with no volume); COF 5; DIS 3; SPG 3; two each in AMT, DE, EMR, MO, TMO, UNP; single bars in sixteen names |

Three dates recur across names — 1998-05-20 in eight names, 1999-12-17
in six, 1995-01-31 in five. A day that is flat in eight large names at
once is the vendor's history, not eight halts. C's 1996 is the same
thing at scale: the closes are real (the year's moving averages,
down-runs and returns read correctly from them), and only the prints
inside each day are missing. This is a **source defect in the early
history of some names**, recorded beside M0.3 in `docs/M0-ANSWERS.md`
and in the Tiingo rights record's notes, not a property of the market.

**What it costs.** Under the sampled, whole-run audit: 2,284 cells
refused and 3,598 with a refused baseline, by sort order (ADR-0041).
Under ADR-0041 as proposed: one missed trade per flat bar per cell that
would have entered on it, named in the record. The always-long baseline
enters every box and so misses all of them — for C, 254 of its roughly
2,500 boxes in the window, one name in eighty-three.

## Decision (adopted 2026-09-13)

**Name the defect in the record; leave the calendars where they are.**

1. **The sector calendar stays at 1998-12-22**, the members' common span
   at declaration, and `sp_100`'s at 1993-01-04. No boundary moves for a
   source defect.
2. **C stays in `sp_100`, 1996 included.** Its closes are real and its
   signals read from them; the fills that the year cannot give are
   missed trades (ADR-0041), counted by name and bar.
3. **The bias is named where a universe is read.** A superseding
   `UniverseDeclared` record for `sector_etfs` and for `sp_100` — same
   members, a note naming the flat bars and their count — so the
   universe's own record says what its history cannot give, in the same
   way the two constituent lists already name survivorship. Every
   survey cell and every verdict on these universes carries the missed
   census beside the trade count; a verdict is never shown without it.

This is conditional on ADR-0041. If the audit stays as it is, the flat
bars refuse whole runs and the calendar question returns in the form
below.

## Consequences

- No apparatus change beyond ADR-0041's. Two appended universe records
  with notes; no calendar record.
- The sector definition partition keeps its first 45 days, and the
  measurement and reserve boundaries stay where record #9's cells were
  computed. The next grid's sector cells remain on the same partition as
  the first survey's.
- The missed census is part of what M12.7's programme page and M12.6's
  verdict evidence show; the shrinkage table is not affected.

## Considered options

- **Supersede `sector_etfs`'s calendar to start after 1999-02-26.**
  Available under ADR-0038 as a recorded supersession — `calendar freeze
  --universe sector_etfs --start 1999-03-01 --supersedes 729745-739870
  --reason …` — and allowed, because no registered question has used the
  sector cuts (a universe's cuts bind only itself). What it does: moving
  the start 68 days later shortens the span by 68 days; with the recorded
  split (0.3 / 0.5 / 0.2) the definition end moves about 48 days later
  and the measurement end about 14 days later — a fortnight of the sealed
  reserve becomes measurement, which is the drift ADR-0038 was written to
  stop, here by the author's act rather than the archive's growth. It
  removes three bars from 2,100 definition days and makes every later
  sector cell non-comparable to record #9's, which was computed on the
  earlier calendar and stays recorded on it. Not proposed; the author's
  to choose if the sector definition partition should be free of the
  defect at that price.
- **Exclude C's 1996 by a superseding `sp_100` record.** A universe
  record carries members, not per-name windows. This is either a record
  without C — ten clean years of one name dropped for one defective
  year, and its 1996 signals with them — or a new per-name exclusion
  field in the record and the archive slice, an apparatus change the row
  did not ask for. Rejected in both forms: the year's closes are real,
  and the audit already refuses exactly what is not.
- **Leave the refusals as they are and name them in every verdict.**
  This is the status quo under the sampled audit: measurability by sort
  order (ADR-0041). Rejected as a standing rule; the naming it asks for
  is what the decision above does, with the audit fixed.
