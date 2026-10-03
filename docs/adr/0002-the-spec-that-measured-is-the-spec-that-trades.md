# The spec that measured is the spec that trades

A Strategy may be built before its Hypothesis resolves — it is the apparatus
that measures it, and half the donor register asked questions that cannot be
posed without one (`Z04-ORB-OBTAINABLE`, `E2-OBJECTIVE`). Building is
therefore permitted pre-resolution, but deploying is not. To close the gap
between the two, **the `StrategySpec` hash is frozen into the Verdict at
resolution, and deployment asserts that the deployed hash equals the resolved
hash.**

## Consequences

Any edit to a resolved spec — a widened stop, a tuned threshold, one more
filter — produces a different hash and therefore requires a **new Hypothesis
and new alpha**. This is deliberate. Post-hoc tuning between the measurement
and the deployment is the most common way measured edge disappears in
practice, and it is invisible to every test that can be written unless the
identity is pinned. The freeze must be enforced by type, not by convention:
a deploy path that takes a spec rather than a resolved-hash-plus-spec is a
defect.
