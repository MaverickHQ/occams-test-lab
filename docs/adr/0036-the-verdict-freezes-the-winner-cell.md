---
status: decided · closes the question flagged at M3 and carried on the M8.3 row
---

# The Verdict freezes the winner cell's hash; the template names the family

A registered Hypothesis declares a sweep, and the engine measures one spec
per cell (M3.7). Every cell has its own hash — a different stop is a
different Strategy under D4 — while the Strategy that entered
`MEASURED` carried the template's hash, the one spec the sweep was built
from. Two hashes, one Verdict. Which does it freeze?

**The winner cell's.** D2 says the spec that measured is the spec that
trades, and deployment asserts hash equality against the Verdict
(ADR-0002). The only spec whose measured numbers a deployed Strategy can
inherit is the winner's; freezing the template's hash would let a
Strategy trade a stop that was never the one measured to clear the floor.

**The template's hash is recorded beside it as the family.** It names what
was searched — the sweep and its size are the search-correction's whole
input (R4.4) — and it is what the overlap gate and the Register's "what
did we search" answer point at (N6).

## Consequences

- `Verdict.spec_hash` is the winner cell's hash; `Verdict.family_hash` is
  the template's. `HypothesisResolved` carries both.
- **The template measures; the winner trades.** The Strategy built from the
  template runs `SPECIFIED -> COMPILED -> MEASURED` and stops there. On a
  supported Verdict a Strategy is specified from the winner cell's spec,
  compiled, given the same Measurement, and is the one that enters
  `FORWARD`. Its hash equals the Verdict's by construction, which is what
  the `FORWARD -> APPROVED` guard asserts (D2).
- The reserve permits one look per spec hash (ADR-0006). The look is
  charged to the winner's hash. A second sweep that happens to contain the
  same winner is a second look at the same spec and is refused — which is
  correct: the reserve was looked at for that spec.
- A null Verdict freezes the winner's hash too. Nothing trades on it; the
  hash records which cell came closest, so a later supersession can say
  what it changed.

## Considered options

- **Freeze the template's hash.** Simplest and it is what the M2 controls
  did implicitly. Rejected: it breaks D2 — the deployed spec would not be
  the measured one — and it would let a one-cell "sweep" and a nine-cell
  sweep with the same template look identical in the Register.
- **Freeze every cell's hash.** Most complete. Rejected: the Verdict is one
  resolution against one floor; the losing cells are search, and the
  search is recorded as its size and its refusals, not as verdicts.
- **Make the sweep part of the spec's identity.** Then the template's hash
  would be the winner's. Rejected: D4 says the hash is what the Strategy
  *is*, and a Strategy is one stop, not a set of candidate stops.
