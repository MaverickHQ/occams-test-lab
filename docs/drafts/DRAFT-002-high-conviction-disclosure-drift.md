---
status: Draft — carries no standing and has spent no alpha (CONTEXT: Draft)
tier: mechanism (ADR-0027)
axis: cross_sectional — **allocated 0** by ADR-0028 via ADR-0017, so this is **not registrable today**
relates_to: "TASKS-v4.md M8.1 · docs/drafts/DRAFT-001 · docs/adr/0004 · docs/adr/0014 · docs/adr/0017 · docs/adr/0025 · docs/adr/0027 · docs/adr/0028"
---

# DRAFT-002 — High-conviction disclosure drift

A **Draft**. No standing, no alpha spent, nothing measured.

It trades **the disclosure, not the purchase** — and the whole document turns
on that distinction, so the failed version is written out first.

## Why the obvious version fails

The natural formulation is: *use 13F to find when funds bought, map those
dates to the chart, learn the pattern that precedes a large institutional
buy.* It is intuitive, it is the version most people build, and it cannot
work. Three independent reasons, each sufficient.

### 1. 13F carries no timing

A 13F is a **quarterly snapshot of holdings**, not a transaction record, filed
within **45 days of quarter end**.

```
purchase        2 January
quarter ends    31 March     +88 days
filing due      15 May       +133 days
```

What the filing discloses is that the position on 31 March differed from the
position on 31 December. **When it changed is not in the document.** There is
a 90-day ambiguity window inside up to 135 days of latency, and the position
may have been bought, sold and rebought within it.

So a signal that fires *before* a large institutional buy is unobtainable
from this source by construction. The buy is already four months old. The
only thing left to be early to is other people's reaction to a public
document that is machine-parsed within seconds of reaching EDGAR.

Three further gaps, each of which quietly inverts the signal:

- **Long positions only.** A manager long $50m and short $80m of the same
  name files as a holder.
- **A vanished position is ambiguous** — sold, or fell below the filing
  threshold, or ceased to be a 13(f) security.
- **13F/A amendments restate.** Reading today's amended figure is reading a
  document that did not exist at the time — ADR-0004's back-adjustment trap
  wearing different clothes.

### 2. Inferring the buy date from price is circular

Since the purchase date is unobserved, the only way to recover it is to infer
it — and the evidence available is price and volume. Which produces:

1. Infer the buy date from price and volume.
2. Search for price and volume features that predict the inferred date.
3. Find them.
4. Conclude the chart predicts institutional buying.

**The chart was used twice.** The label was manufactured from the features
that then predict it. This is label leakage, and it is not a risk to be
managed — it is a guarantee. The backtest will look excellent and will be
measuring its own construction.

It is the **vacuous pass** in its most persuasive disguise, because the output
is populated with real funds, real companies and real charts.

### 3. The search space cannot be declared

*"Look for features that build a signal"* is unbounded — any indicator, any
lookback, any threshold, any combination, and news features on top. DESIGN-v4
D13 already names this failure: *a search that `search_space_size` never
counts*.

It is also mechanically fatal rather than merely unwise. **M6.4** computes
spend as `configured_test_alpha x search_space_size`. There is no number to
declare, so registration is refused before anything is spent — correctly.
What that formulation describes is **feature discovery**, a legitimate
activity requiring a validation regime this lab does not implement (nested
cross-validation, deflated Sharpe, probability of backtest overfitting), and
which ADR-0014's forward window cannot retrofit.

**News is excluded from this Draft** for the same family of reasons: coverage
is endogenous to price, so "news predicts moves" usually runs backwards; and
free archives cannot supply a reliable `Known-at instant`, which the glossary
requires.

## The mechanism, stated honestly

Entry is the **filing timestamp** — EDGAR's acceptance datetime, a genuine
known-at instant. No timing is inferred, so the circularity is gone.

The claim is **slow information diffusion under limited attention**.
Thousands of filings land in a two-day cluster at the deadline. Attention is
finite. Positions held by less-followed managers, in less-covered names,
diffuse into price over days to weeks rather than instantly, and a
high-conviction position — one that is a large share of the manager's own
portfolio — carries more information than an incremental add.

**This mechanism is weaker than DRAFT-001's, and the difference should not be
glossed.** DRAFT-001 rests on **compulsion**: an index fund *must* sell. This
rests on **inattention**, which is a real and documented phenomenon
(post-earnings-announcement drift is the canonical case) but has nobody
forced to be on the other side. Compulsion is the stronger prior. If only one
of these can be afforded, that asymmetry should decide it.

**Prior evidence cuts against.** Holdings-cloning ETFs were launched
commercially in the 2010s and broadly underperformed or closed. That is not
proof the effect is absent, but it is strong evidence the obvious form is
arbitraged, and it should be weighed **before** alpha is spent, not after.

## Both interpretations

**If real.** Some managers hold persistent skill, and disclosure of their
high-conviction positions is processed slowly enough for a retail participant
to act. The effect should be **larger** in less-covered names and among
less-followed managers — a directional prediction, declared here, tested as a
pre-declared subgroup.

**If not**, four distinct worlds, and they are not equally interesting:

1. **No skill to disclose.** The positions do not outperform in the first
   place.
2. **Skill decays inside the lag.** Real, but stale by 135 days — a finding
   about how fast edges decay, which is worth knowing.
3. **Disclosure is efficiently priced.** Thousands of machines parse EDGAR on
   arrival; there is no drift to capture.
4. **Real, and not obtainable** — the drift exists and costs consume it.
   Resolves at the **implementation** child (ADR-0027), never here.

## Falsifier

> **EV per trade in net R fails to exceed the declared floor, or realised
> trade frequency falls below the declared minimum**, measured over the
> measurement partition on the rules below and no others.

## The control

Funds buy stocks that have been rising. Without a control this measures
momentum with a 13F sticker on it.

Each disclosed name is matched to non-disclosed names on **trailing return
over the disclosure lag, market capitalisation, sector and liquidity**, and
**the hypothesis is about the difference**.

The matched control does **double duty here**, which matters for the
independence problem below: it removes the momentum confound *and* strips out
most of the common market factor shared by names entered on the same filing
date.

## The independence problem — and it is the likely killer

**13F filings cluster on the deadline.** Entries therefore fall on roughly
four dates a year, and positions are held simultaneously with overlapping
horizons. **Trades entered together are not independent observations.**

With `k` trades sharing a date and cross-sectional correlation `rho`, the
effective count is:

```
N_eff  =  k / (1 + (k - 1) * rho)
```

At `k = 60` and `rho = 0.30`, sixty trades supply **about three** independent
observations. At `rho = 0.10`, about nine.

Over fifteen years at four dates a year — sixty filing dates — effective N
lands somewhere near **180 to 540** against the **817** the table below asks
for at a 0.15R floor. **That is marginal at best and insufficient at worst,
and it turns entirely on `rho`**, which is measurable on the definition
period and must not be assumed.

Naive trade counting would report several thousand trades here and be wrong
by an order of magnitude. Matching removes most of the shared market factor,
which is the main thing standing between this Draft and arithmetic that does
not work — so the control is not a robustness nicety, it is load-bearing
twice over.

## Search space — declared, enumerated, closed

`search_space_size = 8`

| Parameter | Declared values |
|---|---|
| Conviction threshold | top 5% · top 10% of the manager's own portfolio weight |
| Position type | new position only · new or materially increased |
| Holding period | 60 sessions · 120 sessions |
| Manager universe | one set, fixed in advance, not searched |
| Matching rule | one, fixed in advance |

Any parameter added later re-registers at the larger size.

## Power

`N = ((z_alpha + z_beta) * sigma / effect)^2`. At 8 cells: alpha 0.00625
two-sided, `z_alpha ~ 2.73`; at 80% power `z_beta = 0.84`.

Trades required, at a **provisional** `sigma = 1.2R`:

| Floor (EV per trade, net R) | N required | vs. DRAFT-001 (4 cells) |
|---|---|---|
| 0.10R | 1,838 | 1,606 |
| 0.15R | 817 | 714 |
| 0.20R | 460 | 402 |
| 0.25R | 294 | 257 |

**These are counts of independent observations, not of trades.** Apply the
`N_eff` deflation above before comparing to anything. `sigma = 1.2R` remains
a placeholder to be estimated on the **definition period**.

## Data — and the part that is free

**13F filings are free.** SEC EDGAR, structured XML for recent history,
filings back to the late 1990s, with acceptance timestamps.

And a second-order consequence worth more than the price: **a 13F filing is
self-point-in-time.** It is a dated document stating what was true on a date.
For a universe defined as *names appearing in 13F filings*, the survivorship
problem ADR-0025 exists to catch is **solved at zero cost** — the filings
*are* the constituent history, and no point-in-time universe licence is
needed to construct it.

That answers the constituent half of **M0.5** for free. It does not answer
the rest:

| Dependency | Why | Cost |
|---|---|---|
| **M0.20** | EDGAR coverage, structured-data depth, as-filed vs amended retrieval, acceptance timestamps, bulk-access rights and rate limits | the lookup itself is free |
| **M0.3** | As-printed OHLC for held names **and matched controls**, including names that later delisted | **unpriced** |
| **M0.4** | Corporate actions on the same set | **unpriced** |
| **M0.2** | `c`, the round-trip cost | free lookup |
| **M0.16** | admissible band, hence the floor's lower bound | derived |
| **M0.11 / M0.14** | `cross_sectional` is at 0 | the author's |

The price series remains the expensive half, and delisted names are exactly
where it is dearest — which is also exactly where survivorship bias lives, so
it cannot be skipped.

## Tier and its child

**Mechanism**: does disclosed high conviction predict abnormal returns net of
the matched control? Carries the large alpha.

Its **implementation** child, once resolved in favour: does a specific
StrategySpec clear its floor net of costs and obtainability? World 4 resolves
there.

## What would make a null uninformative

- **The control is omitted or specified after seeing results** — then the
  verdict cannot separate disclosure drift from momentum.
- **`rho` is assumed rather than measured**, and effective N is overstated by
  an order of magnitude.
- **Amended filings are used in place of as-filed** — a look-ahead aimed
  directly at the variable under test.
- **Delisted names are dropped** because their prices were unaffordable,
  reintroducing survivorship into a design whose universe was survivorship-
  free for free.
