# Every Strategy declares a stop, and R is planned risk

The detectable floor is declared in net R (ADR-0004 context: see the floor
decision), which requires the risk unit to be unambiguous. We fix **R =
`config.risk_per_trade`, a constant**, with position size derived as
`R / stop_distance` — the donor's sealed convention (`riskUsd = 175.0`,
`_sized(stop_dist, params, costs)`). **A `StrategySpec` without a stop fails
to compile.**

## Considered options

- **Volatility fallback (ATR x size) where no stop exists.** Rejected: it is
  a unit, not a bound. Losses stay unbounded per position, which is
  unacceptable when losses are not capped by an entry fee, and the
  entry-obtainability gap auditor would have nothing to audit.
- **Money for stopless specs.** Rejected: reintroduces the
  stranded-at-one-capital-level problem and splits verdicts into two
  incomparable kinds.

## Consequences

Regime-conditional strategies — the first proposer — carry a *disaster stop*
alongside their signal exit. The signal normally fires first; the stop exists
to define R and bound the loss. The disaster stop's width is therefore a
declared parameter subject to the same registration discipline as any other,
and must not be tuned after the fact.

**R is planned, not realised.** A position that gaps through its stop is
recorded honestly as (say) -2.7R rather than clipped to -1R. On equities this
is the difference between a truthful loss distribution and a flattering one.
