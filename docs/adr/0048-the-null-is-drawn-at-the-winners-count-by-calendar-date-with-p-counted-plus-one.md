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

## As built (M16.14, 2026-10-03)

**The draw is studentised.** In every resample the difference is divided by
its own standard error, blocks of days as clusters, and the observed
difference by its own; the comparison is of the two ratios (Götze & Künsch
1996). A draw then carries the noise of the variance estimate as well as of
the mean.

**Random entry is its expectation.** The reference for beats-null is half
the long passive outcome of every admitted box and half the short, summed by
day — the expectation of a coin's side, with no single coin's luck in it.
The multi-day engine's coin-flip probe is no longer drawn.

**The cross-check is the larger p.** §5's refusal when the two disagree
means a check passes only when the bootstrap's p and the clustered standard
error's p are both at or under the corrected alpha. The size table measures
that decision.

**What the size table reads** (200 seeds a row, beats-null alone, at a
declared 0.01 and 0.05; tolerance 0.026 and 0.086):

| World | As built | Now |
|---|---|---|
| day-boxed, independent names | 0.005, 0.030 | 0.000, 0.035 |
| day-boxed, names sharing a market | 0.095, 0.200 | 0.010, 0.045 |
| multi-day, independent names | 0.130, 0.210 | 0.010, 0.040 |
| multi-day, names sharing a market, a stop that binds | 0.295, 0.340 | 0.010, **0.100** |
| multi-day, names sharing a market, a stop too far to bind | — | 0.005, **0.095** |

The review's two probes — rows two and three — are inside tolerance at both
rates. So is every row at 0.01, the per-cell alpha every question in this
lab was registered at.

**The multiple is two, and no multiple closes the last two rows at 0.05.**
§3 asked for the smallest multiple of the hold for which every calibration
world is within tolerance. On the multi-day engine, over the same 200 seeds:

| Block | Independent names | Names sharing a market |
|---|---|---|
| 1 × hold | 0.010, 0.045 | 0.015, 0.105 |
| 2 × hold | 0.010, 0.040 | 0.010, 0.100 |
| 4 × hold | 0.010, 0.040 | 0.010, 0.100 |
| 8 × hold | 0.010, 0.025 | 0.025, 0.100 |

A block is two holds of consecutive calendar days, or the vendored rule's
length for the daily series when that is longer, and never so long that
fewer than four blocks remain.

**The residual, measured.** ADR-0047 §6 says a fix that leaves a measured
size above tolerance is not done. For the multi-day engine on names that
share a market, at 0.05, this one is not done, and it is recorded as open
rather than closed by choosing seeds:

- *How large.* The last row's world puts the stop where it cannot bind, so a
  long position mirrors a short one exactly and a coin's side is the null by
  construction. It reads 0.095 on the table's 200 seeds, 0.060 on 800 fresh
  ones, and 0.067 over the thousand, where the tolerance is 0.066. The true
  rate is about six or seven in a hundred against a declared five.
- *Why.* Over 400 seeds of that world the studentised difference has a
  spread of 1.08 where a correct reference has one. Positions entered fewer
  than a hold apart share days and a market; a block keeps that covariance
  when both entries fall inside it and loses it when they straddle its edge,
  and the clustered standard error discounts the same lags. The bootstrap's
  own 99th percentile matches the statistic's (2.41 against 2.38); its 95th
  does not (1.69 against 2.04 on those seeds).
- *What was tried.* Longer blocks: the table above. A standard error that
  keeps the covariance whole out to the hold (a flat-top kernel): over 400
  seeds it moved the shared-market world from 0.083 to 0.077 and the
  independent one from 0.062 to 0.070, and was not adopted. A reference
  distribution with fewer degrees of freedom: no change at 0.05.
- *What was ruled out.* That the entry's count rises after its losses and
  biases the mean per trade: the two are correlated at −0.49 across seeds,
  and the bias that gives is two hundredths of a standard error.
- *Where the stop binds, part of the excess is not an error.* In that world
  always-short loses 0.0074 R a trade and always-long 0.0018 — the stop bites
  a short harder — so a long entry with no skill is ahead of a coin's side by
  a tenth of a standard error. Refusing that is the fifth check's work, and
  ADR-0049 makes it so.
- *What would close it.* Re-running the entry on resampled price paths keeps
  every dependence and is not built: these simulators answer in seconds, not
  milliseconds.

Both rows are strict expected failures at 0.05 that name this section, and
the README lists the residual as a limitation.
