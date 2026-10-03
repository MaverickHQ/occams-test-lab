# The regime classifier is frozen before any strategy question

Regime-conditional strategies are the first proposer, and a regime classifier
carries parameters of its own — lookback, threshold, index-level or
per-instrument. Tuning those until a strategy works is a search that
`search_space_size` never sees, because it happens *inside* a single
hypothesis: the declared space says 12 while the real space was 12 times the
classifier space. **Consumed-observation and search-budget accounting cannot
detect this hidden search.** We therefore
commit the classifier in its own registration, before any strategy hypothesis
exists, on a priori grounds, calibrated only on an early **definition
period** that is then permanently excluded from strategy measurement.

## Considered options

- **Classifier parameters inside each strategy's declared search space.**
  Honest, and sacrifices no history. Rejected because the multiplied search
  size makes the per-test alpha tiny under correction, which would leave the
  first real question either unaffordable or underpowered.
- **Classifier declared free per hypothesis.** Cheapest and most flexible,
  and precisely the failure this apparatus exists to refuse: nothing prevents
  choosing the classifier that makes the answer come out, and no guard can
  see it happening.

## Consequences

A slice of history is spent on definition and can never be measured on.

Two constraints follow and are not optional. **The label must be causal** —
computable at time *t* from data no later than *t* — enforced through the
same point-in-time gate as everything else, not checked by eye. And **whether
regime is index-level or per-instrument is itself a declared parameter**,
because an index-level regime makes every concurrent trade share a common
factor. The resulting intra-cluster correlation must be **measured** and used
in the power plan. The donor programme asserted that correlation at 0.9 and
measured it at 0.38.
