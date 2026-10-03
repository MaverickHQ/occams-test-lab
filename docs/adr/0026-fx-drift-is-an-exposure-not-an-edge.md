# FX drift is an exposure, not an edge

Net R was defined as "after all costs, converted to account currency", which
conflates two different things. A GBP account holding a USD stock for ten
days incurs an **FX cost** — the spread on converting in and out — and takes
an **FX position**: it is long USD for the duration, and nobody asked for
that.

Including drift in measured edge tests a joint bet, the strategy plus an
unhedged currency position. **That currency position has no declared
mechanism, no falsifier and no registered hypothesis** — it is an undeclared
information axis taken with real money, inside a system built to refuse
exactly that.

**Net R is measured in the instrument's currency, with FX conversion spread
included as a cost. FX drift is excluded from measured edge and reported as a
separate declared exposure with its own limit in configuration.**

## Considered options

- **Net R in account currency, drift included.** One number, no
  reconciliation, and it measures what is actually banked. Rejected: the same
  Strategy would receive a different verdict depending on the account's
  currency, and the currency component would never have been registered.
- **Hedge the exposure.** Cleanest conceptually — account-currency and
  instrument-currency net R become equal. Adds hedging cost to every trade,
  requires venue support for the hedge instrument, and is likely unavailable
  on a retail equity account.

## Consequences

Three quantities stay distinct that were previously one: what the Strategy
earned, what the currency contributed, and what was banked. Reported P&L will
therefore differ from measured edge, and that difference must be explained
wherever both appear rather than quietly reconciled.

Verdicts remain comparable across a universe spanning several currencies,
which a GBP-denominated net R would not be.
