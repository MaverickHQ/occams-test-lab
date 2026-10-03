# Alpha exhaustion is terminal until new data, and replenishment is mechanical

The claim that separates this design from the reference architecture is that
**the alpha budget is the loop's termination condition**. A budget that can be
topped up on request is not one, so exhaustion must bite. But permanent
closure is not right either: family-wise error control constrains repeated
searches of the *same* data, and genuinely new non-overlapping observations
are a new family, not another look at the old sample.

**When an axis is exhausted, registration on it is refused. Budget then
accrues only against observations that no Hypothesis has consumed** — the
register records the date ranges and instruments each hypothesis used, so
replenishment is a computation rather than anyone's decision.

## Considered options

- **Terminal, reopened only by a written programme decision.** Strictest and
  simplest, and precisely what the closed programme did when it concluded at
  24 hypotheses rather than topping up. Rejected as the default only because
  it places a judgement call at the most tempting possible moment; kept as
  the fallback if the accrual bookkeeping proves unworkable.
- **Soft budget that warns and continues.** Never blocks legitimate work, and
  removes the only real termination condition. The donor register reached a
  search-size-corrected 1.70 by exactly this route.

## Consequences

The ledger tracks consumed observations per hypothesis, not merely a running
total — more bookkeeping than a counter, and the thing that makes accrual
computable.

An operator can wait for new data and continue. That is the legitimate move,
and it is the one the rule is designed to permit; what it forbids is
re-searching the same decade until something clears.
