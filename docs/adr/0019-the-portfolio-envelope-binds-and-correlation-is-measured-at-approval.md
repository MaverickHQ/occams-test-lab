# The portfolio envelope binds, and correlation is measured at approval

Per-Strategy retirement rules (ADR-0010) do not compose. Three Strategies can
each sit inside their own envelope while the account is down more than any
envelope permits, with nothing fired. The problem is sharper here than
generic portfolio risk because regime-conditional Strategies **share the
regime**: their drawdowns are correlated by construction and they go wrong
together by design.

**Configuration declares two drawdown numbers, per-Strategy and portfolio.**
Breaching the portfolio limit **halts everything and retires nothing** — a
portfolio drawdown is evidence of correlation, not evidence that any
individual Strategy is broken, and retiring them all would destroy that
information. A human then decides what resumes.

**Approving Strategy N+1 requires measuring its correlation to the live set**
and refusing the approval if the combined envelope would breach under the
measured value. This is the portfolio-level analogue of the detectable floor:
the limit is stated before running and the new thing is checked against it,
rather than the breach being discovered afterwards. The donor programme
asserted an intra-cluster correlation of 0.9 and measured 0.38; the lesson
applies at portfolio level too.

## Considered options

- **Per-Strategy envelopes only.** Simplest, and approval never depends on
  what else is running. Rejected: the account can breach any chosen figure
  while every individual rule reports healthy.
- **Capital partitioned per Strategy.** Independent by construction and
  trivially correct arithmetic, at the cost of fragmenting capital so every
  Strategy trades smaller while idle allocations sit unused.

## Consequences

Approval becomes dependent on what is currently live, so the same Strategy
may be approvable today and refused next month. That is a real operational
constraint and it is the correct one.
