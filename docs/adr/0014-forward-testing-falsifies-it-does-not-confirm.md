---
status: amended by ADR-0023 (the window is declared in trades and time)
---

# Forward testing falsifies; it does not confirm

`FORWARD -> APPROVED` needs a stopping rule, or it becomes optional stopping:
check continuously, approve the first time the result looks acceptable, and
approvals land on lucky streaks. The obvious remedy — run until the power
plan's n — turns out to cost one to two years per Strategy. At 0.5 trades per
day against a 0.25R effect with roughly 1R trade-level SD, an independent
confirmation needs about 125 trades at alpha 0.05 and about 265 once the
search correction is applied.

**The forward stage is therefore a pre-declared falsification window with a
rejection boundary, evaluated once at the end.** Passing means no
implementation, cost or obtainability defect was detected. It is explicitly
**not** confirmation of edge, and the Register records it in those words.

## Why this is the honest framing

Both defects the donor programme caught at this stage were implementation
failures, not edge questions: `Z-ENTRY-IMPLEMENTABLE` found the fade's +0.1R
did not exist because the engine booked unobtainable entries, and
AMENDMENT-4a found the entry was a limit rather than a stop, at the cost of
two of the campaign's first three setups. That is what forward testing is
good at, and claiming more for it would be the same overreach the reference
architecture makes when it draws the stage as a loop with no stated duration.

## Considered options

- **Powered confirmation.** Statistically the strongest option and it makes
  forward capacity the binding constraint on the entire programme — perhaps
  two strategies ever reach live.
- **Group-sequential design with an alpha-spending boundary.** Valid early
  stopping, so good strategies reach live sooner and bad ones die faster.
  Deferred rather than rejected: more machinery, and the boundaries must be
  declared before the first look. Worth revisiting if forward capacity
  becomes the bottleneck.

## Consequences

A Strategy goes live with its edge never independently confirmed. That must
be stated plainly wherever approval is recorded, not glossed — the whole
value of this stage is that nobody mistakes "nothing broke" for "it works".
