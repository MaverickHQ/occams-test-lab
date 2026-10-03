# The inference review of 2026-10-03, verified by rerun

Before anything in the review was planned or built, its claims were checked
against this repository at `2e86d58` (`TASKS-v4.md` M16.0). Every claim read
in the code holds at the file and line it names. Its probes were rerun
independently, from its descriptions, in a scratch environment that touched
no Register.

| Claim (review id) | The review's figure | Rerun here |
|---|---|---|
| position-boxed beats-null on a world with no effect, false positives at 0.01 and 0.05 (F01) | 0.140, 0.225 | 0.140, 0.225 (200 seeds) |
| the same null resampled at the winner's trade count | 0.015, 0.100 | 0.015, 0.100 |
| the fifth check on that world | 0.065, 0.135 | 0.065, 0.135 |
| day-boxed beats-null under a common factor of 0.5 (F02) | 0.090, 0.200 | 0.093, 0.213 (150 seeds) |
| the same with no common factor | 0.010, 0.050 | 0.000, 0.020 |
| a coin flip passes the fifth check on the day-boxed null control (F04) | passes | passes: `make null --engine=day_boxed` has printed it since ADR-0043 |
| a forged and re-chained Register verifies; a truncated one verifies (F11) | 37, 20 | 37, 20 |
| the required counts and bounds of its appendix (A5) | — | match; one count differs by one |

## What the reruns mean

- On the engine that measured Q-005 and both programme 2 questions, the
  beats-null check fires fourteen times as often as its declared 0.01 on a
  world with nothing in it.
- On the day-boxed engine the null is exact when trades are independent and
  far too narrow when they share a date and a market.
- The fifth check, added so that a supported verdict attests the entry and
  not the side, can be passed by a coin flip when the paths drift.
- The chain shows that one line was not changed without the rest. It does
  not show that the file is the one that was written.

Every one of these errs toward a false positive. The four null verdicts
therefore stand under every correction, and the one supported verdict,
Q2-001, is where a correction can bite.

## Three corrections to the review

1. **A survey's readiness cannot be recomputed from recorded results.** A
   survey cell file holds summaries and no per-date series, so survey-wide
   inference needs every cell run again.
2. **The lab imports four more vendored modules than the review lists:**
   `audit`, `result`, `privacy` and `charset`.
3. **Its cross-check rule misfires at small values.** Refusing when two
   p-values differ by more than a factor of two refuses harmless
   disagreements far below alpha; this lab refuses when the two fall on
   opposite sides of the corrected alpha.

## What was not rerun

The verdicts themselves. They are re-scored, as diagnostics beside the
record and never in its place, by M16.18 under ADR-0047.
