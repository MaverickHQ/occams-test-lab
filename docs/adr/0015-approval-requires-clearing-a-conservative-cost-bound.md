# Approval requires clearing a conservative cost bound

Costs must be measured rather than assumed, but the only way to measure fill
quality is to trade, and nothing may be traded before it is approved.
Commission and FX markup are published; spread needs quote data that daily
bars do not carry; slippage and queue position are observable only from your
own fills.

**A Strategy is approved only if it clears its declared floor under
worst-case costs.** The property that matters is directional: a cost surprise
can then only be favourable. Approving on a point estimate means a surprise
silently invalidates the approval and is discovered with money on — and the
donor programme's slippage assumption came out **2x optimistic on one of two
instruments** (`E3-COSTS`: "cost assumption tightened, not overturned").

Measured costs replace the bound later, obtained from a small **calibration
campaign** — minimum size, traded purely to measure fills. That is a
capability question rather than a market question, so it registers at **alpha
0** and costs a little money and no budget. The replacement is a recorded
context change, not a new identity (ADR-0007).

## Considered options

- **Require measured costs before any approval.** True numbers and no
  spurious refusals, but it puts real money at risk before any Strategy has
  been approved, and the calibration campaign's instrument coverage would
  then bound what could ever be approved.
- **Published schedules, flagged as assumed.** Free and immediate, and
  exactly the assumption that came out 2x optimistic last time.

## Consequences

Genuinely viable strategies will be refused for failing under pessimistic
assumptions. That is the intended direction of error, and the calibration
campaign is the route to reversing an individual refusal honestly.
