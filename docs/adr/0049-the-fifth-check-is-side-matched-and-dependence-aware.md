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
