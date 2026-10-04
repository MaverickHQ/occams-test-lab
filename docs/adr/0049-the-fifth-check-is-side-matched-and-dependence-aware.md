---
status: decided 2026-10-03 — adopted by the author's instruction to run M16 ("run M16. Add including M16.21") after the inference review of 2026-10-03 was verified by rerun (`TASKS-v4.md` M16.0); built by M16.15
---

# The fifth check is side-matched and dependence-aware

ADR-0043 made beating always-long the fifth check *so a supported verdict
attests the entry, not the gate and the side*. As built it does not do that.
The baseline is always **long**, whatever sides the winner took, and its
draws are means of independent boxes. On the day-boxed null control the
synthetic paths drift down, a coin flip is short half the time, and the
coin's EV of −0.080 beats always-long's −0.103 with p near 0.005: **a coin
flip passes the fifth check** — `make null --engine=day_boxed` has printed
*checks that passed: plateau, leave_one_out, beats_always_long* since the
check was added, and nobody read it as a defect. On a world with no effect
and a long-only entry the check fires at 0.065 against a declared 0.01.

## Decision (adopted 2026-10-03)

1. **The baseline takes the winner's side mix.** The passive alternative is
   a market entry on every box the gate admits, under the same exits, stop
   and horizon — long and short — and the baseline weights the two by the
   winner's own share of each side. For a long-only entry it is always-long,
   as before. For a coin flip it is the coin's own expectation, and the
   check refuses.
2. **The margin is measured against that baseline everywhere.** The surface
   the sweep optimises (ADR-0045) and the fifth check use one number; a
   cell records which rule its baseline followed, so an older measurement
   reads as always-long.
3. **The test resamples whole calendar days.** The winner and the baseline
   are recomputed together on the same resampled days (ADR-0048's
   bootstrap), so trades that share a date, positions that overlap, and the
   baseline's own sampling error are all in the comparison. p is counted
   plus one.
4. **The margin's two parts are recorded.** *Selection* is the passive
   outcome on the boxes the winner chose, less the passive outcome on every
   admitted box; *execution* is the winner's outcome less the passive
   outcome on the same boxes. They sum to the margin. For a market entry
   execution is exactly nil and the whole margin is selection.
5. **From the next registration, never backwards.** A re-score reports what
   this rule would have said (ADR-0047).

## Consequences

- S3's output changes once, and this ADR names the change: on the day-boxed
  engine the null control is now refused by beats-always-long as well.
- Q2-001's margin of −0.001 gives a p near one half under any baseline; the
  re-score records it. The fifth check was not in force when it resolved.
- A cell's `baseline_ev` means the side-matched baseline from here on.

## Considered options

- **Pair every trade with the passive trade on the same box**, as the phrase
  *paired on shared boxes* suggests. Rejected as the whole test: for a market
  entry the two are the same trade and the difference is identically nil.
  Kept as the execution part.
- **Compare with the passive outcome on the winner's own dates only.**
  Rejected: an entry's contribution is largely *which dates* it picks, and
  that comparison removes it.
- **Resample the passive pool with the winner's clustering**, as the review
  proposes. Rejected for ADR-0048's reasons: a pool cannot reproduce
  positions that overlap across neighbouring entry days.

## As built (M16.15, 2026-10-04)

**One helper gives the baseline everywhere.** `probes.baseline_of` runs the
long passive probe for a cell, and the short one only when the cell holds a
short trade; the engines' sweeps, the definition surface shown before alpha
moves and the survey's readiness all take the baseline from it, so the
surface and the guard cannot hold two numbers. A long-only cell's baseline
is always-long, number for number: every cell of every long-only world in
`tests/test_probes_unchanged.py` is what it was.

**The comparison is ADR-0048's.** The winner and its side-matched baseline
are summed by calendar day and resampled together, studentised, at the
winner's count; the clustered standard error is read beside it and the
check passes only when both agree. A baseline drawn at any other count is
refused.

**What the size table reads** (200 seeds a row, the fifth check alone, at a
declared 0.01 and 0.05; tolerance 0.026 and 0.086):

| World | As built | Now |
|---|---|---|
| day-boxed, a rising shared market; long, no timing skill | 0.015, 0.060 | 0.000, 0.020 |
| multi-day, a martingale; long, no skill | 0.055, 0.165 | 0.005, 0.040 |
| multi-day, a shared market, a stop that binds; long, no skill | — | 0.000, 0.060 |
| day-boxed, a falling market, entered by a coin flip | 0.960, 0.985 | 0.010, 0.035 |

Every row is inside tolerance at both rates. The third is the world where
beats-null lets a long entry with no skill through one time in ten at 0.05
(ADR-0048, *As built*): the stop bites a short harder there, so being long
is ahead of a coin. This check is the one that refuses it.

**It still sees what is there.** The signal control's planted reversal
passes the fifth check in 100 of 100 seeds at the control's corrected alpha
of 0.05 / 9, against a planned 0.80.

**S3 changed once, as §Consequences said.** `make null --engine=day_boxed`
is refused by beats-null, the floor and beats-always-long, and passes the
plateau and leave-one-out. `make signal` is accepted on both engines.

**Execution is simulated only where it can differ.** For a market entry it
is nil by construction and nothing is run. For a resting order the passive
market entry is simulated on each of the winner's boxes, same side, and the
difference averaged; selection is the margin less that.

**The refusal reads as it judges:** *the passive alternative at the same
geometry, gate and side mix does as well*. Records made before this say
*being long at the same geometry and gate does as well*, and stand.

**The survey's readiness uses the guard's comparison** at the cell's own
count, on the cell's trades re-run now. It still tests each candidate alone:
twenty candidates are the best of thousands of cells, and nothing corrects
for that here (the review's F08; the successor lab's).
