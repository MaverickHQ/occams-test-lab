---
status: confirmed by the author 2026-09-06 — real money is first at risk in the forward window
---

# The forward window executes for real, at minimum size

D22 states what the forward window is for: passing means **no implementation,
cost or obtainability defect was found**. Two of those three are properties of
actual fills. Whether the stop was reachable through the opening auction,
what the spread actually was at the moment of entry, whether the venue
accepted the order type at all — none of these are answerable by a simulator,
because a simulator answers with the very assumptions under test.

**A forward window run against `venues/paper.py` cannot do its stated job.**
It would compare the backtest's cost and obtainability assumptions against
themselves and report agreement. That is the vacuous pass, in the one stage
built to catch it.

**The forward window therefore executes real orders at minimum size on the
live venue, through the proposal path by default** — a card generated from the
spec, the order placed by hand. That path needs no credentials and is already
specified as first-class rather than a fallback (R1.7).

The paper venue and the venue's sandbox both keep jobs, and neither is this
one: **paper** satisfies the port contract test and keeps CI offline;
**sandbox** supplies dated capability-conformance evidence at `COMPILED`
(M10.11), which is exactly what it is good for — real order types, real
rejections, simulated fills.

**This puts real money at risk before `APPROVED`.** It is bounded — minimum
size, configured by the author, inside the portfolio envelope, which a
forward-window position counts against — and R2 already establishes that real
capital is at risk. But it crosses a boundary the state machine reads as
uncrossed until `LIVE`, so it is recorded as an author decision and confirmed
alongside M0.13 rather than assumed.

## Considered options

- **The paper venue.** Free, no risk, no credentials. Rejected above: the
  costs and obtainability it reports are the assumptions the backtest already
  made, so the defect class the stage exists to find is invisible by
  construction.
- **The venue's demo or sandbox account.** A real improvement — genuine order
  types, genuine rejections, genuine capability behaviour. Still insufficient
  here, because fills are simulated by the venue, typically without queue
  position and often at mid, so realised spread and slippage remain fiction.
  Retained for what it does establish, at M10.11.
- **Drop obtainability from the forward window and measure it after
  approval.** Coherent, and it moves the discovery to the moment the position
  is full-sized and the money is real — which is the failure D22 exists to
  prevent. The donor's slippage assumption came out 2x optimistic; finding
  that at full size is the expensive way.

## Consequences

**Sequencing changes.** The proposal path (M9.7) and at least one venue must
exist *before* the first forward window. As written, the forward runner is
M9.4 and every venue arrives at M10.8 — a milestone later — so the stage that
must place orders is built before anywhere to place them exists.

**Minimum size is configuration**, not a constant in code, on the same
reasoning as every other money parameter (R9).

**Realised costs measured in the forward window supersede the conservative
bound** by the D23 calibration route, registered at alpha 0. The window
therefore produces a cost measurement as a by-product, which is the cheapest
place it will ever be obtained.

**A forward-window position is a live exposure** for the purposes of D21: it
counts against the portfolio envelope, and a breach halts it like anything
else.

---

> **Confirmed 2026-09-06.** The author confirmed that the forward window
> places real money at risk before `APPROVED`, executed through the R1.7
> proposal path at minimum size. The frontmatter flag is cleared.
>
> One correction belongs in the record. The confirmation was sought on a
> framing that described this ADR as specifying *automated* execution. It
> never did — the proposal path, a card generated from the spec and the order
> placed by hand, is what the decision above states and is what was
> confirmed. What required the author's word was never the mechanism; it was
> that real capital is committed one state earlier than the state machine
> reads as the first commitment. That is the thing confirmed.
>
> **Consequence for M0.13.** The money parameters must now include a
> **minimum size** for the forward window, alongside capital, drawdown and
> risk per position. It is a money parameter and takes the R9 treatment: no
> default, no recommendation, refusal to start without it.
