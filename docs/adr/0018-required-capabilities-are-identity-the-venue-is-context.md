# Required capabilities are identity; the venue is context

A venue changes how a Strategy behaves. Without a native stop you poll and
send a market order on breach, which is a different fill distribution.
Without GTC, orders cannot rest. With whole shares only, sizing rounding
error is bounded by `stop_distance / R` — with R at 100 and a stop distance
of 30, a single share is 30% of R, and planned risk stops being fixed, which
is ADR-0003's entire premise.

That makes the venue look like identity, but putting it in the spec hash
would force re-registration of everything on a broker change and defeat the
swappable-venue requirement. **So the spec declares the capabilities it
requires — native stop, GTC, share-granularity tolerance — and that
capability set is part of the hash. The specific venue is context.** Venues
are interchangeable only when their adapter declarations carry current
conformance evidence for those capabilities.

The `COMPILED` guard checks the target venue's declared capabilities, their
dated conformance evidence, and **refuses at compile time**, the
rounding-tolerance check included. Missing, failed, or stale evidence is the
same as a missing capability.

## Considered options

- **Venue in the spec hash.** Most precise, nothing about behaviour hides in
  context, and swapping brokers would re-register everything and spend alpha
  again.
- **Capability checked at submission.** Thinnest adapters and no capability
  modelling, with the discovery arriving on an approved strategy with real
  money on — the stage this design exists to move failures away from.

## Consequences

Every venue adapter must declare its capabilities honestly, and a wrong
declaration otherwise fails quietly. Adapter declarations therefore need
dated contract evidence against the official sandbox/live venue or a
human-approved minimum-size calibration campaign, tied to adapter version.
Self-declaration and unit tests alone are insufficient.

A Strategy needing client-side stop simulation is a genuinely different
Strategy from one using native stops, and costs new alpha. That is correct.
