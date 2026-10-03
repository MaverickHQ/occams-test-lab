---
status: requires the author's number at M0.18 — the rule is decided here, the threshold is not
---

# The lab has its own falsifier

Every Hypothesis this lab registers must state, before it runs, the result
that would refute it (R3). **The lab itself states no such result.** It has
three gates that can stop it before M1 — data unusable (M0.6), programme
unaffordable in money (M0.14), unaffordable in trades (M0.15) — and once
those close, nothing. There is no condition under which a built, running lab
concludes that its own premise was wrong.

That is the discipline applied to every question except the one that paid for
the apparatus.

**The lab therefore declares a falsifier before its first Hypothesis
resolves**: a count of resolved mechanism verdicts, and an outcome, at which
the lab closes. It is recorded in configuration, evaluated mechanically
against the Register, and never judged in the moment — the same construction
as a Strategy's retirement rule, for the same reason.

## This is not alpha exhaustion

The two stops look alike and are opposites.

| | Alpha exhaustion | Lab falsifier |
|---|---|---|
| Stops | the **search** | the **enterprise** |
| Says | "no budget left to look" | "looking here was the wrong idea" |
| Repaired by | new data — replenishment accrues against unconsumed observations *(ADR-0011)* | nothing |
| Status | terminal **until new data** | terminal |

Alpha exhaustion is a resource running out. A lab falsifier firing is a
**result**: the premise that a detectable edge exists — in this instrument
class, at this cost structure, reachable by this apparatus — has been
measured and found wanting. It is the most valuable thing the lab can produce
short of an edge, and it is the one outcome nobody builds a lab to hear.

## Why it must be declared before the first verdict

A threshold set once results are in is a threshold set with knowledge of the
results. The lab would be doing to itself precisely what the sealed reserve,
the spec hash and the pre-declared floor exist to stop it doing to a
Hypothesis. **M0.18 therefore sits inside M0**, beside the alpha split
(M0.11) and the money (M0.13), and the number is the author's on the same
grounds: a default is a recommendation, and no one else's threshold for
abandoning this is meaningful.

## Considered options

- **No falsifier; stop when it feels wrong.** The status quo. Rejected on the
  design's own argument against judged retirement (ADR-0010): the moment of
  deciding is the moment least able to decide, and sunk cost is at its
  maximum exactly when the evidence against is strongest.
- **Alpha exhaustion is the stopping rule.** Rejected by ADR-0011's own
  mechanism — exhaustion is repaired by new data, so it stops nothing
  permanently. A lab that replenishes each quarter runs forever by
  construction.
- **A time box — stop after N months.** Measures effort, not evidence. It
  fires on a lab that is working slowly and spares one that is failing fast,
  which is backwards.
- **A money box — stop at the cap.** Already exists as N5, and does useful
  work, but it stops the *spending*, not the *believing*. A lab can run at
  near-zero marginal cost on data already bought and still be wrong.

## Consequences

**The count is over resolved hypotheses, including superseded ones.**
Supersession is the obvious escape hatch: a null approaching the threshold
could be relabelled superseded and the count reset. A resolved Hypothesis
counts against the falsifier permanently, whatever later happens to it.

**Both tiers count, and not equally.** A null mechanism hypothesis
*(ADR-0027)* says the effect is not there. A null implementation hypothesis
says one apparatus could not reach an effect that may be. The threshold is
stated over **mechanism** verdicts; implementation nulls are recorded and not
counted, unless the author states otherwise at M0.18.

**The lab refuses to start without it**, on the R9 pattern. A missing
falsifier is not a default of infinity; it is a refusal.

**Firing it is a publication, not a deletion.** The Register is publishable
as it stands *(ADR-0008)*. A lab closing on its own declared threshold
publishes the count, the floors and every verdict — the negative result this
apparatus was built to be able to produce honestly.
