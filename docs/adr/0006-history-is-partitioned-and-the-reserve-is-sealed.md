---
status: amended by ADR-0031 (the forward period runs before approval) and ADR-0038 (the calendar the partitions are cut from is frozen as a Register record)
---

# History is partitioned, and the reserve permits one look per spec hash

Price history is split four ways: a **definition period** (oldest) for fixing
pre-committed components such as the regime classifier, a **measurement
period** where hypotheses resolve, a **reserve** of recent history, and the
**forward period** in wall-clock time. Split percentages live in
configuration and are stamped into every result.

> **Amended 2026-09-06 by ADR-0031.** As written this said the forward
> period runs "from approval onward", which contradicts the state machine
> and would leave ADR-0023's window unable to refuse anything. It runs from
> entry into `FORWARD`, **before** approval. It is also not a slice of price
> history and carries **no** split percentage: **three** configured splits
> partition the archive.

The reserve is only a holdout if it is looked at once. Because every Strategy
has a spec hash and the event log is append-only, that can be enforced rather
than promised: **a reserve look is recorded against the spec hash, and a
second look on the same hash is refused.** Another look requires a different
spec — which is a new hash, a new Hypothesis, and new alpha.

## Considered options

- **No historical reserve; wall-clock forward as the only holdout.** Spends
  no history and maximises measurement power. Rejected because killing an
  overfit strategy would take a quarter rather than an afternoon, making
  forward capacity the limit on how many questions can be asked.
- **Walk-forward across the measurement period.** The best use of a finite
  sample and standard practice. Rejected as the primary guard because every
  re-run reuses the same data, so it does not constrain repeated looks — the
  one thing the reserve exists to do. It remains available *within* the
  measurement period.

## Consequences

Definition and reserve come out of the measurement sample, lowering power.
Acceptable here: a regime strategy across roughly twenty liquid names over a
decade yields thousands of trades. It would not be acceptable for the
fundamentals axis, where the effective sample is 2.
