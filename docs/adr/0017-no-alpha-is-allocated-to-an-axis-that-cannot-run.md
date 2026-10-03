# No alpha is allocated to an axis that cannot run

The fundamentals axis cannot run: the available claim set covers two
entities, so the effective sample is 2. Holding a share of the budget on it
starves the only axis actually working, and the obvious fix — reallocate now,
grant fundamentals a fresh share when it becomes viable — is the top-up
loophole of ADR-0011 in different clothing, arriving at a total above 1.

**An axis that cannot run is allocated 0.** When it becomes viable it draws
from the `reserve` slice by recorded decision.

The invariant, checked on every configuration load:

    sum(axis budgets) + reserve == declared total

## Considered options

- **Allocate and freeze.** Most conservative and needs no future decision,
  but it starves the running axis exactly where affordability was already
  tight.
- **Allocate and reallocate freely.** Most flexible, and frequent
  reallocation makes the split meaningless — an axis that keeps borrowing is
  an axis with no budget, and the discipline decays without anything ever
  failing.

## Consequences

The loophole becomes a build failure rather than a temptation: a
configuration whose allocations do not sum to the total will not load.
