# The retirement rule is declared at approval, not decided during drawdown

Watching a live Strategy and stopping it when it looks bad is sequential
testing with no correction: every strategy with real edge has drawdowns, so
stopping at the first bad patch kills good strategies, and never stopping
rides bad ones down. Deciding fresh puts the decision mid-drawdown with money
moving, which is the worst available moment for judgement. **The retirement
rule is therefore declared at approval, inside the signed approval record,
and evaluated mechanically.**

The rule is derived from the Strategy's **own measured distribution**: retire
when cumulative net R falls below a declared percentile of the Monte Carlo
path distribution its backtest produced at that trade count. The strategy is
tested against what it itself predicted. The percentile is configuration and
is the author's to set.

## Considered options

- **A fixed global threshold** in R or percent drawdown for every strategy.
  Simple and easy to reason about, but expected drawdown depends on a
  strategy's own variance and trade frequency, so one number is
  simultaneously too tight for one strategy and too loose for another.
- **Discretionary periodic review**, as the reference architecture does it.
  Rejected above.

## Consequences

The full Monte Carlo **path** distribution must be archived at resolution,
not merely the summary statistic — a change to what the register stores.

**Halting is always allowed; resuming is not.** Any human may halt anything
at any time, without justification: safety must be unilateral. A Strategy the
rule retired cannot simply be resumed — bringing it back requires a new
Hypothesis and new alpha. Panic is cheap, optimism is expensive.
