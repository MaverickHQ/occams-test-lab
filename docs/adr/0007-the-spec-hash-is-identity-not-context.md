---
status: amended by ADR-0018 and ADR-0025
---

# The spec hash is identity, not measurement context

Two rules key on the spec hash: deployment must match the resolved hash
(ADR-0002), and the reserve permits one look per hash (ADR-0006). What sits
inside the hash therefore defines how the rules could be gamed. **The hash
covers only what the strategy is** — entries, exits, stop, sizing, order
type, horizon, the point-in-time `UniverseRule`, required capabilities, and
the frozen classifier it references. What it was measured *under* — data
window, seed, `engine_sha`, cost-model version, and target venue — is recorded
in the Verdict as context.

## Considered options

- **Hash the full measurement context.** Maximum reproducibility precision:
  two identical hashes guarantee identical results. Rejected because every
  engine bump or one-day window nudge would mint a new identity and with it a
  fresh look at the sealed reserve — farming looks would be trivial and
  invisible.
- **Hash identity plus `engine_sha`.** Closes the date-nudging loophole but
  still grants a reserve look on every engine change, cosmetic ones included.

## Consequences

Changing the `UniverseRule` changes the spec, so it is a new hash, a new
Hypothesis and new alpha. This is intended: widening or otherwise changing
the eligible universe is a real search and should cost. The dated membership
resolved from an unchanged rule is measurement context, not identity.

An engine fix that invalidates an existing verdict is handled by **explicit
supersession**, not by a new identity. The donor register already carries a
`supersedes` field and used it (`H4-ORDERFLOW` -> `H4-ORDERFLOW-v2`). A lazy
operator could abuse supersession the same way, but supersession is visible
in the register and a silent hash bump is not.
