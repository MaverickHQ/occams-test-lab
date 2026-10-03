---
status: amended by ADR-0027 (hypotheses come in two tiers)
---

# Hypothesis and Strategy are separate aggregates

The v2 design draft moved a single `Candidate` object through one state
machine from proposal to live trading. That conflated two things with
genuinely different lifecycles: a **Hypothesis** is a question about the
world that resolves once and costs alpha, while a **Strategy** is a
deployable artifact that costs money and has an operating life of pause,
resume and retire. We split them, and made the join a hard rule: **a Strategy
may only become deployable by citing a resolved Hypothesis whose verdict
supports it.**

## Considered options

- **One `Candidate`.** Simpler, one event log. Rejected because alpha cost
  becomes ad hoc exactly where it matters: instrument variants of a confirmed
  effect, resuming a paused strategy, and strategies resting on more than one
  question. Ad hoc alpha accounting is how the donor programme reached a
  search-size-corrected 1.70.
- **Strategy only, no register.** Closest to the reference architecture we
  are modelling. Rejected because pre-registration is the donor repository's
  entire value, and without it the pipeline is a machine for generating
  overfit strategies at industrial scale.

## Consequences

The deploy gate stops being a judgement call and becomes a lookup. A
Hypothesis that resolves null is still valuable and is kept; only the
Strategy that rested on it is retired. Two state machines and a join must be
maintained instead of one.
