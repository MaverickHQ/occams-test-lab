# The execution host is a durable process, and it is priced before M1

R11 requires research and execution to be separate hosts. N4 requires cloud.
N2 requires local operation at $0. **Nothing says what the execution host
is**, and the safety requirements cannot be satisfied by an arbitrary answer.

Three requirements decide the shape between them. R1.6 reconciles **each
heartbeat**. R1.5 lists **heartbeat timeout** as a kill path. R1.4 halts on
an **unreconciled `ORDER_INTENT` at startup**. Together these require a
process whose continued liveness is itself the signal — and whose *absence*
is detectable as an event rather than as silence.

**The execution host is therefore a single long-lived process on a small
always-on instance**, awake at least through the venue's trading hours,
holding the credentials and the write-ahead log. **The research host is the
author's own machine**, which reads the internet, runs the proposer and
carries no credentials. Approvals cross as **signed files over a one-way
transport that requires no inbound network path to the research host**.
Neither host mounts the other.

The instance is a recurring cost charged against the N5 cap, which does not
reset. **The specification and its price are an M0 line (M0.17), and M0.14
cannot close without it** — M0.14 blocks M1, so this is upstream of every
build task.

## Considered options

- **Scheduled invocation — cron, or a serverless function.** Cheapest by far
  and scales to zero. Rejected on safety: **a missed run and a dead host are
  indistinguishable**, so the heartbeat-timeout kill path would fire on its
  own scheduling gaps and be tuned off within a week — the classic route by
  which a safety check becomes decorative. An unreconciled intent also needs
  a process that notices *at startup*, not at whatever time the next tick
  happens to land.
- **Run execution on the research laptop.** Free, and it violates R11
  outright. The internet-reading proposer and the order-submitting adapter
  would share a machine, a filesystem and a keychain, restoring precisely the
  injection path the host split was created to close.
- **Always-on 24/7 irrespective of venue hours.** Simplest to reason about
  and pays for hours in which no order can be placed. Rejected on N5, with
  one consequence retained: restart-time reconciliation must be correct
  regardless, which R1.4 already requires.
- **Broker-side or managed automation.** Would move the human gate outside
  the system, where it cannot be enforced by a signature.

## Consequences

**The heartbeat becomes a declared design object** — a configured period,
against which the R1.5 timeout is calibrated. It is not an implementation
detail of whatever scheduler happens to be used.

**M11.8's IaC has something concrete to parameterise.** Until now it asked
for a parameterised deployment of an unspecified thing.

**The approval transport needs a named mechanism** at M10.16, satisfying
one-way flow with no inbound path to the research host. This ADR fixes the
property, not the product.

**Only the execution host carries recurring cost.** The research host is the
author's machine and stays inside N2 — local, $0, no credentials. That keeps
the recurring line as small as the safety requirements permit, which matters
against a cap with little headroom.
