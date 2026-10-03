---
status: Draft — carries no standing and has spent no alpha (CONTEXT: Draft)
tier: mechanism (ADR-0027)
axis: cross_sectional — **allocated 0** by ADR-0028 via ADR-0017, so this is **not registrable today**
relates_to: "REQUIREMENTS-v4.md · TASKS-v4.md M8.1 · docs/adr/0017 · docs/adr/0025 · docs/adr/0027 · docs/adr/0028"
---

# DRAFT-001 — Forced selling at index deletion

A **Draft**, in the sense `CONTEXT.md` gives the word: a proposed Hypothesis
carrying a mechanism and a falsifier, with **no standing until a human
confirms its registration**, which is the act that spends alpha. Nothing here
has been measured. Nothing here has cost anything.

It exists to make one thing concrete: what a hypothesis looks like when the
search space is small **because the mechanism is sharp**, rather than small
because someone trimmed it to lower the correction.

## Read this first — it cannot be registered today

The information axis is `cross_sectional`. **ADR-0028 allocated that axis 0**,
and ADR-0017 is unambiguous about what a zero-budget axis accepts. This Draft
is therefore evidence for the amendment note appended to ADR-0028 on
2026-09-06 — the axis set to zero is the one where the retail structural
advantage lives — and it is not a request to register anything.

It becomes registrable only if **M0.19** finds the narrow event data
affordably, and **M0.14** leaves room to move the axis off 0.

## Mechanism

Funds tracking an index **must** sell a deleted constituent on or about the
effective date. That selling is **price-insensitive**: it is not a view, it is
a mandate, and it happens whatever the price.

If stocks were perfect substitutes, this would not matter — arbitrage capital
would absorb the supply at fair value and the demand curve for any single
name would be flat. The claim under test is that it is **not** flat
(Shleifer 1986; Harris and Gurel 1986): price-insensitive supply meeting a
finite pool of absorbing capital pushes the price temporarily below fair
value, and whoever provides that liquidity is paid for it as the price
recovers.

The prediction follows directly and has a sign: deleted names are **pushed
down into the effective date and recover afterwards**. The trade is to buy
once the forced supply is exhausted and hold through the recovery.

Two properties make this worth asking rather than the version it replaces
(*"detect institutional accumulation on a chart"*):

- **The forcing is disclosed, not inferred.** The index provider publishes
  which names, and when. There is no proxy standing between the hypothesis
  and the event, so a null verdict means something.
- **Nobody is hiding it.** Execution algorithms exist to conceal
  discretionary accumulation. An index fund's mandate cannot be concealed —
  it is published in advance, by design.

## Both interpretations

**If the effect is real.** Demand curves for individual equities slope
downward at the horizons that matter, and the compensation for absorbing
forced supply survives in names too small for the arbitrage capital that
would otherwise flatten it. The effect should be **larger** where index-fund
ownership is a larger fraction of float, and where the absorbing capital is
thinnest — a directional prediction, stated here, testable as a pre-declared
subgroup rather than discovered afterwards.

**If it is not.** Three distinct worlds, and they are not equally
interesting:

1. **Demand curves are flat.** Substitutes are close enough that arbitrage
   equalises price. The mechanism is wrong.
2. **It existed and has been arbitraged away.** Both source papers are from
   1986 and the effect is documented as having decayed. This is the modal
   outcome and it is a real result — a dated effect is a finding about
   markets, not a failure of the apparatus.
3. **It is real and not obtainable.** The raw effect survives but the spread
   on names small enough to exhibit it consumes all of it. **This is the most
   likely "false" and the most important to separate**, because it is a
   verdict about *your* cost structure rather than about the world — and it
   is exactly what the mechanism/implementation split in ADR-0027 exists to
   keep apart. A mechanism verdict must not be allowed to absorb it.

## Falsifier

Measured over the measurement partition, on the entry and exit rules declared
below and no others:

> **EV per trade in net R fails to exceed the declared floor, or realised
> trade frequency falls below the declared minimum.**

Either half alone falsifies. The floor is a pair and both halves bind
(`CONTEXT`: Detectable floor).

## The control that makes this a real hypothesis

**Deletions are not random.** A stock is deleted because it fell. Buying
deletions is therefore, by construction, also a bet on reversal in beaten-down
small caps — a well-known and heavily-mined effect that has nothing to do
with index flow.

Without a control, a positive result here is uninterpretable: it would be
consistent with the mechanism being entirely false and the returns coming
from a factor already in the literature.

**Declared before running, not after:** each deleted name is matched to
non-deleted names in the same universe on trailing drawdown, market
capitalisation and liquidity over the same window. **The hypothesis is about
the difference**, not the raw return. If matched non-deleted names show the
same recovery, the mechanism is false however profitable the raw trade looks.

This is the single most important line in this document. A version of this
hypothesis without the matched control is a repackaged reversal factor
wearing an index-flow costume, and it would spend mechanism alpha to learn
nothing.

## Declared exclusions

- **Deletions caused by merger or acquisition are excluded.** The price is
  pinned to deal terms, there is no liquidity vacuum, and the return
  distribution is a different object entirely. Requires reason codes or a
  corporate-actions series (**M0.4**).
- **Deletions caused by delisting or insolvency are excluded** on the same
  grounds and with the same dependency.
- Only deletions at **scheduled reviews** are in scope. Ad-hoc intra-review
  removals have a different announcement-to-effective interval.

## Search space — declared, enumerated, and closed

`search_space_size = 4`

| Parameter | Declared values |
|---|---|
| Entry | effective-date close · effective date + 1 session |
| Holding period | 20 sessions · 60 sessions |
| Universe | one pooled index family set, fixed in advance |
| Matching rule | one, fixed in advance |

Index families are **pooled into a single test**, not tested separately.
Testing them one at a time multiplies the search space by the number of
families and buys nothing the pooled test does not already answer.

**Any parameter added later re-registers the hypothesis at the larger search
space.** The correction is a measurement of how much was looked at, not a fee
to be minimised — and four cells is honest here only because the mechanism
admits four. It is not a trimmed version of a larger sweep.

## Power

Per the corrected M0.15 formula, `N = ((z_alpha + z_beta) * sigma / effect)^2`.
At `search_space_size = 4`: alpha 0.0125 two-sided, `z_alpha ~ 2.50`; at 80%
power, `z_beta = 0.84`.

Trades required, at a **provisional** `sigma = 1.2R`:

| Floor (EV per trade, net R) | N required (4 cells) | N required (200 cells, for contrast) |
|---|---|---|
| 0.10R | 1,606 | 2,916 |
| 0.15R | 714 | 1,296 |
| 0.20R | 402 | 729 |
| 0.25R | 257 | 467 |

**`sigma = 1.2R` is a placeholder and must not be used.** M0.15 now requires
`sigma` to be a declared parameter with recorded provenance, and this
hypothesis is a case where assuming it would matter: a wide stop on a name
that has just been dumped produces a fat-tailed outcome distribution, and
`sigma` above 1.5R would move every row in that table by more than a third.
It is estimated on the **definition period**, which is what the definition
period is for — never on the measurement partition, which would consume the
observations the hypothesis is about.

**Trades available** is `deletions_per_year x years_in_measurement_partition`,
after the exclusions above remove the M&A and insolvency cases — which may be
a large fraction. Both terms are M0 lookups. The arithmetic runs in minutes
once M0.19 supplies the first.

## Detectable floor — derived, then the author's

Not chosen freely. The lower bound is set by cost:

```
floor  >  cost_in_R  =  c / s
```

where `c` is round-trip cost as a fraction of notional and `s` is stop
distance. **M0.16** produces the admissible band, **M0.2** produces `c`. On
small-capitalisation names `c` is large, so a viable `s` is wide, and a wide
`s` interacts with the stop question below.

The author sets the floor within that band and declares the minimum trade
frequency alongside it, before anything runs. The number is not recommended
here and no default appears anywhere.

## Required capabilities

Small-capitalisation cash equity at the venue · share granularity fine enough
that a minimum-size position is possible in a low-priced name · a native stop
· sufficient depth that a minimum-size order does not itself move the price.

**A live tension for the implementation child.** The StrategySpec mandates a
stop, and a stop placed on a name that has just been force-sold into a
liquidity vacuum is standing exactly where the volatility is. If the stop is
tight it will be hit by the tail of the very selling the hypothesis is about;
if it is wide, `cost_in_R` falls but position size falls with it. This is an
implementation question, not a mechanism one, and it belongs to the child.

## Tier and its child

**Mechanism** hypothesis (ADR-0027): does the effect exist, net of the
matched control? Carries the large alpha.

Its **implementation** child, which cannot exist until this resolves in
favour: *does a specific StrategySpec — one entry, one exit, one stop, one
sizing rule — clear its floor net of costs and obtainability?* World 3 above
resolves there, not here.

## What must close first

| Dependency | Why |
|---|---|
| **M0.19** | Scheduled-review deletion events with dates and reason codes. **The narrow question, not M0.5's full point-in-time constituent licence** |
| **M0.4** | Corporate actions, to execute the M&A and insolvency exclusions |
| **M0.3** | As-printed OHLC bars for the deleted names and their matched controls |
| **M0.2** | `c`, the round-trip cost on names this small |
| **M0.16** | The admissible stop-distance band, hence the floor's lower bound |
| **M0.15** | Trades available against the table above, at a real `sigma` |
| **M0.11 / M0.14** | `cross_sectional` is at 0. It moves only if the budget allows |

## What would make a null uninformative

Recorded now, because a null costs mechanism alpha **and** counts permanently
against the lab falsifier (ADR-0033), and a null that teaches nothing is the
most expensive outcome available.

- **The matched control is omitted or specified after seeing results.** Then
  neither verdict distinguishes index flow from ordinary reversal.
- **`sigma` is assumed rather than measured**, and N is set from a number
  that flatters the design.
- **The exclusions are not executed** because the reason codes were
  unaffordable, leaving acquisition arbitrage mixed into the sample.
- **The universe is not point-in-time** (ADR-0025). Reconstructing "which
  names were in the index then" from today's membership is a survivorship
  error aimed directly at the variable under test.

If any of these holds at registration time, the honest action is to refuse
the registration rather than spend the alpha.

---

> **Correction, 2026-09-10 — the independence problem applies here too.**
>
> Found while drafting DRAFT-002 and it belongs here as much as there.
> **Scheduled index reviews are quarterly**, so deletions cluster on roughly
> four effective dates a year and the resulting positions are held
> simultaneously over overlapping horizons. **Trades entered together are not
> independent observations**, and the power table above counts trades as
> though they were.
>
> With `k` trades sharing a date and cross-sectional correlation `rho`, the
> effective count is `N_eff = k / (1 + (k - 1) * rho)`. At `k = 30` and
> `rho = 0.30`, thirty trades supply about **three** independent
> observations.
>
> Every row of the power table must therefore be read as **independent
> observations required, not trades required**, and `deletions_per_year` from
> M0.19 must be deflated by a `rho` **measured on the definition period**
> before M0.15's arithmetic means anything. Naive trade counting overstates
> power here by roughly an order of magnitude.
>
> **The matched control partly rescues this.** By measuring the difference
> against matched non-deleted names it strips out most of the common market
> factor that drives `rho`, so the residual correlation after matching is far
> below the raw figure. That makes the control load-bearing twice over — once
> against the reversal confound, once against this — and it makes measuring
> the *post-matching* `rho` the number that actually decides whether this
> hypothesis is affordable.
