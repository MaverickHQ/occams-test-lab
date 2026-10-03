---
status: decided 2026-10-03 — adopted by the author's instruction to run M16 ("run M16. Add including M16.21") after the inference review of 2026-10-03 was verified by rerun (`TASKS-v4.md` M16.0); built by M16.8 (p plus one, evidence) and M16.14 (the null)
---

# The null is drawn at the winner's count, by calendar date, with p counted plus one

Beats-null (R4.4) asks whether the winner does better than random entry
under the same costs and geometry, at the corrected alpha. Three things make
the answer looser than the alpha it is asked at.

**The count.** The day-boxed engine draws each null value as a mean over the
winner's trade count. The position-boxed engine does not: its bootstrap
resamples the random-entry pool to the pool's own length, so each draw is a
mean over about three times as many positions as the winner holds and the
null is too narrow. On a world with no effect, at one cell, the check fires
at **0.140 against a declared 0.01** and 0.225 against 0.05. Q-005 and both
programme 2 questions were measured on that engine.

**The dependence.** Both engines treat the draws as independent. The
winner's trades are not: a signal fires on many names on the same day, and
multi-day positions entered on neighbouring days hold the same days. With
names that share a market the day-boxed null, exact when trades are
independent, fires at **0.093 against 0.01** and 0.213 against 0.05. The
registered questions' own measured same-day correlations run from 0.19 to
0.56.

**The count of exceedances.** `p = exceed / B` reports zero when no draw
reaches the winner, and nothing at all is recorded when a check passes:
Q2-001's resolution carries no p, no null mean, no standard error.

## Decision (adopted 2026-10-03)

1. **Every draw is a mean at the winner's trade count.** A measurement
   records the count its null and its baseline were drawn at, and both
   Monte Carlo guards refuse one drawn at any other.
2. **The null resamples whole calendar days, in blocks.** The winner and the
   reference it is compared with — random entry with a coin's side for
   beats-null, the side-matched passive alternative for the fifth check
   (ADR-0049) — are summed by calendar day, and the same resampled days are
   used for both. Blocks are runs of consecutive calendar days, long enough
   to hold the overlap of positions entered on neighbouring days: a declared
   multiple of the hold, never less than the hold. Trades that share a date
   stay together; positions that overlap stay together; the reference's own
   sampling error is in the comparison.
3. **The multiple is whatever the size table requires.** The build uses the
   smallest multiple for which every calibration world is within tolerance
   (ADR-0047 §6), and records it beside the rule.
4. **p is counted plus one**: `(1 + exceed) / (1 + B)`, everywhere a Monte
   Carlo p is computed. The draws needed to resolve the corrected alpha are
   unchanged.
5. **A standard error is recorded beside the bootstrap.** Clustered by entry
   date, with a correction across dates out to the block length. When the
   bootstrap's p and the analytic p fall on opposite sides of the corrected
   alpha the check refuses, naming both: the two are answers to one
   question, and a verdict does not rest on the one that agrees.
6. **Every check leaves its evidence, pass or fail.** A `GuardEvidence`
   record per check precedes each resolution, with the winner's count, EV,
   dispersion and standard error, the p, the reference's mean and spread,
   the draws and the method.
7. **From the next registration, never backwards.**

## Consequences

- The position-boxed engine's `block_bootstrap_means` takes a target
  length; `Measurement` gains `null_n` and `baseline_n`, zero on a
  measurement made before this.
- Every p-value on a multi-day question widens. A null verdict cannot be
  revived by it; a pass can become a refusal.
- The synthetic engine draws independent trades by construction and keeps an
  independent null, which says so.
- The survey's readiness uses the same function as the guard, at the cell's
  own count.

## Considered options

- **Resample the random-entry pool at the winner's count**, as the review's
  first fix proposes. Measured: it brings the position-boxed check from
  0.140 to 0.015 at 0.01 and leaves 0.100 at 0.05 — a pool whose sides were
  fixed by one coin carries its own mean's noise into every draw.
- **Resample the pool in date clusters shaped like the winner's**, as the
  review's second fix proposes. Rejected: a passive pool laid out one
  position at a time cannot reproduce positions entered on neighbouring days
  that hold the same days, which is where multi-day dependence lives.
- **A t-test on the clustered standard error alone.** Kept as the cross-check
  of §5, not as the test: the bootstrap needs no distributional form for
  outcomes that are stopped and gapped.
- **Refuse when the two p-values differ by more than a factor of two**, as
  the review proposes. Rejected: at 1e-6 against 3e-6 it refuses a
  disagreement that changes nothing.
