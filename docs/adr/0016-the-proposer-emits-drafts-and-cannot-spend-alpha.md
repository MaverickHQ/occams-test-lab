# The proposer emits drafts and cannot spend alpha

The proposer reads adversarial public text by design, so its blast radius
under injection is a real question. Most of it is already closed: the
Register is publishable by construction so there is nothing to steal
(ADR-0008), orders need a signature the proposer cannot produce (ADR-0009),
and specs are declarative, schema-validated and gated by a human before live.

One path was open. **If registration were automatic, injected content could
drain an axis's alpha budget** — and because exhaustion is terminal until new
data arrives (ADR-0011), a cheap injection would permanently close a research
axis. No money would be lost and the programme would be dead. That asymmetry
is the thing to design against: the proposer cannot cost money, but it could
cost the thing money cannot buy back.

**The proposer is therefore a draft emitter with no authority.** Read-only
Register, write access to a draft queue and nothing else, no credentials of
any kind, no Operations access, allowlisted outbound network, output
validated against a schema. **Registration — the act that spends alpha —
requires a human confirmation.**

## Considered options

- **Automatic registration with a per-axis rate limit.** Keeps the loop
  autonomous, which is the reference architecture's whole appeal, and caps
  damage per incident. Rejected because it trades a permanent risk for
  convenience on an act that should be rare anyway.
- **Automatic registration bounded only by the budget.** Fully autonomous,
  and one successful injection closes an axis for good.

## Consequences

The pipeline is not autonomous end to end. Someone confirms each question
before it is asked, which matches what registration is: a deliberate
scientific act, and there should not be many of them.
