---
status: amended by ADR-0025 (the universe is a point-in-time rule)
---

# A declared instrument universe is pooled and costs one search

Testing a Strategy across twenty names is either one large sample or twenty
searches, and the two are indistinguishable after the fact. We separate them
by when the universe was fixed: **a universe declared before looking is
pooled, and costs 1 on the instrument dimension.** Trying universes and
keeping the ones that worked is a search and is charged accordingly.

The `MEASURED -> FORWARD` guard's "splits pass independently" rule is
therefore a **robustness check on a pooled result** — leave-one-out, so the
effect may not be carried by a small minority of names — rather than N
separate hypotheses.

## Considered options

- **Each instrument as its own test, search size N.** Immune to
  instrument-shopping by construction, and unaffordable: a twenty-name
  universe with a twelve-cell parameter sweep is 240 tests, which would leave
  the regime axis unable to fund its first real question.
- **The universe as a searchable parameter.** Most honest if exploring
  universes is genuinely the point, but it adds a dimension to every sweep
  and normalises universe-shopping.

## Consequences

The universe must be justifiable a priori — liquidity, listing venue, sector
breadth — and widening it later changes the spec hash, so it is a new
Hypothesis and new alpha.

Pooled trades across names sharing a regime are correlated. The intra-cluster
correlation is **measured** and used in the power plan, so the effective
sample will be materially below the raw trade count. The donor programme
asserted this parameter at 0.9 and measured it at 0.38.
