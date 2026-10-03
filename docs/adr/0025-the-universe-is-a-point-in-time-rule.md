---
status: amends ADR-0012
---

# The universe is a point-in-time rule, not a list

ADR-0012 established that a declared universe is pooled and costs one search.
That is right about alpha and it invites the commonest way an equity backtest
lies. Twenty liquid names picked today and backtested over ten years are
liquid today *because they did well*; the names that delisted, were acquired
at a discount, or shrank out of the liquid set are absent from the list and
from the data. The result measures a portfolio of known survivors.

Declaring the universe in advance does not help, because the bias lies in how
it was chosen rather than when it was written down.

**Membership is therefore a rule evaluated at each date** — for example, the
top N by trailing median turnover, drawn from the full listed set including
names that later delisted. Names enter and leave the sample as they did in
life.

## Consequences

`StrategySpec` carries a `UniverseRule` rather than `instruments: tuple[str]`.
That is an improvement on its own terms: a rule can be inspected and checked,
a list is a claim that cannot be.

ADR-0012 is unaffected in substance — the *rule* is declared before looking,
so it remains one test rather than N.

**Delisting becomes a corporate action** (ADR-0004): the actions series needs
delistings and acquisition terms, or an open position in a vanishing name has
no exit price.

Historical constituent and delisting data become a dependency, and another
line on the data bill against a budget already at $128.09 of $150.

## Considered options

- **A fixed list chosen as of the backtest start date.** Removes
  forward-looking selection and needs only delisting data. The list decays
  through the sample, and it cannot express a strategy that trades whatever
  is liquid at the time.
- **A fixed list chosen today, with the bias declared.** Cheapest and
  honestly documented. Declaring a bias does not remove it: the number
  produced is still not the number the strategy would have made.
