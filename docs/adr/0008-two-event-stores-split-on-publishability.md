# Two event stores, split on publishability

The repository may eventually be published, which makes the event-log
boundary a safety boundary rather than a filing preference. We keep **two
append-only stores**. The **Register** holds the scientific record —
hypotheses, mechanisms, declared floors, verdicts in net R, refusals, alpha
spend, spec hashes and reserve looks. The **Operations** store holds orders,
fills, sizes in account currency, position state, reconciliation and broker
responses. They join on spec hash and hypothesis id.

**The Register is publishable by construction.** Because verdicts are stated
in net R and R is scale-free, the scientific record reveals nothing about
account size. No code path writes account currency into the Register, and
that is enforced by type rather than by review.

## Considered options

- **One store, redacted at publish time.** Simplest joins, one reconciliation
  path. Rejected because redaction is a filter that must be correct on every
  future schema change, and a filter that passes because it was given nothing
  to look for is this programme's named recurring failure.
- **One store, never published.** Simplest and safest, but abandons the
  public research record, which was the closed programme's main external
  output.

## Consequences

The donor's `privacy.py` forbidden-term scanner is vendored and still
required, but it is not sufficient on its own: it catches a broker's name in
prose, not a fills file whose position sizes imply the account size. The
scanner is the lexical guard; the store boundary is the structural one, and
both are needed.
