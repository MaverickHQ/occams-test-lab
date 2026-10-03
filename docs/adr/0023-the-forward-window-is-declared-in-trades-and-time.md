---
status: amends ADR-0014
---

# The forward window is declared in trades and in time

ADR-0014 made the forward stage a "fixed window" without saying fixed in
what, and the gap reproduces this programme's named recurring failure. A
regime-conditional Strategy trades only in its regime; given a calendar
window, the regime may not occur, the window closes with **zero trades**, the
rejection boundary is never triggered, and the Strategy passes. That is a
guard passing because it was given nothing to look for.

**The window is declared as a pair — minimum trades and maximum duration —
and resolves three ways:**

| outcome | meaning |
|---|---|
| >= min trades, no rejection | pass: no defect detected |
| >= min trades, rejection triggered | refused: forward behaviour inconsistent with the backtest |
| < min trades at max duration | refused: declared frequency not met |

The third outcome needs no new concept. The detectable floor is already a
pair — EV per trade in net R **and** a minimum frequency — so a forward
window producing too few trades is simply the frequency half of that floor
failing, measured forward instead of back.

## Considered options

- **Trade count only, running until N trades.** Always produces enough data
  and never punishes a quiet period, with unbounded duration: a rare-regime
  Strategy could occupy forward testing indefinitely.
- **Calendar only**, as ADR-0014 read. Predictable cadence, and a zero-trade
  window passes.

## Consequences

A Strategy whose regime simply did not occur is refused, and re-registering
it with an honestly lower declared frequency costs alpha. That is the correct
price: a strategy that trades a fifth as often as it claimed is a different
proposition, not the same one having a quiet spell.
