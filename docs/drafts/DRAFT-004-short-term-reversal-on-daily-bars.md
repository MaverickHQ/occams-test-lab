---
status: Draft — prepared 2026-09-12 on the real archive, nothing registered, nothing spent (CONTEXT: Draft)
tier: mechanism (ADR-0027)
axis: price_daily — runnable; budget declared 2026-09-10 (M0.11); 0.20 of 0.20 remains
relates_to: "TASKS-v4.md M7.6 M8.1 M8.2 · docs/drafts/DRAFT-003 · docs/adr/0006 · docs/adr/0027 · docs/M0-ANSWERS.md §M0.7 §M0.15"
---

# DRAFT-004 — Short-term reversal on daily bars

A **Draft**, in the sense `CONTEXT.md` gives the word: a proposed Hypothesis
carrying a mechanism and a falsifier, with **no standing until a human
confirms its registration**, which is the act that spends alpha. Nothing
here has been measured on the measurement partition. Nothing here has cost
anything.

It is the `PriceProposer`'s draft (`occams/proposers/price.py`), the first
question on the price_daily axis, written down after the author asked for
one to be prepared. **It is prepared and powered, and it is not recommended
for registration as it stands** — the reason is in the last section, and
the decision is the author's.

## Read this first — the standing when this was written

The lab falsifier stands at **two of three**: Q-003 and Q-004 both resolved
null on the regime axis. The next null mechanism verdict, on any axis,
closes the lab (ADR-0033). This is the question to be surest about.

## Mechanism

After a close below its 10-bar moving average, a liquid US index ETF
carries positive EV in net R over the next three to five bars because
short-horizon selling overshoots and is corrected: **short-term reversal**.
Long only. Market order on the next open. Protective stop as a percentage
of entry. Time exit. No regime gate.

Stated on the closed enum (`EntryKind.CLOSE_BELOW_MA`), through the
position-boxed engine (`Horizon.MULTI_DAY`, D6), on the M0.7 class as
archived: SPY, QQQ, DIA.

## Both interpretations

- **If true:** the winner cell clears the declared floor and beats random
  entry at the corrected alpha — the reversal is real after costs.
- **If false:** the days after a close below the average are not
  distinguishable from random entry after costs — there is no reversal to
  trade on this class at this horizon.

## Falsifier

The winner cell's EV in net R at or below the null's corrected quantile,
or below the floor. Either refuses at MEASURED → FORWARD, and the
resolution says null.

## Declared floor

The pair the lab has used since M0.15: **0.15 net R per trade** and **50
trades per year** pooled. σ of R per trade 1.2 by the M0.15 convention,
superseded by the definition-period measurement at registration.

## Search space — declared, enumerated, and closed

stop ∈ {3, 5} % × hold ∈ {3, 5} bars — **k = 4**, Bonferroni. Plateau of
4 cells fits a 2 × 2 sweep exactly. Both axes bite on the definition
partition: stop 95.1 %, hold 98.4 % of trades change along them.

## Prepared 2026-09-12 against the real archive

`python -m occams question prepare --axis price_daily --entry
close_below_ma --lookback 10 --hold 3 --holds 3,5 --stops 3,5 …`, definition
partition only (1993-01-29 to 2003-03-01), nothing on the measurement
partition touched:

| | |
|---|---|
| definition signals | 1,008 at 0.2089 per name-day |
| available_n on measurement | 2,654 → effective **2,070** at measured ρ 0.655 (same-day, index level) |
| required_n per cell | 748 at α 0.01 |
| verdict of the gates | **POWERED**, supportable (three names), plateau fits, no inert axis, no overlap (new axis) |
| would spend | 0.04 of 0.20 on price_daily |

ρ of 0.655 is the highest the lab has measured: three index ETFs falling
below their averages on the same days are close to one observation.

## What the definition partition says — the reason this is not recommended

The definition partition is the calibration set and may be read. Mean
**gross** R per trade by cell, against the always-long baseline with the
same stop and hold (every box, one position at a time), which is what
random entry under the same geometry looks like:

| stop | hold | reversal cells | always-long | difference |
|---|---|---|---|---|
| 3 % | 3 | −0.050 | −0.058 | +0.008 |
| 3 % | 5 | −0.027 | −0.057 | +0.030 |
| 5 % | 3 | −0.016 | −0.027 | +0.011 |
| 5 % | 5 | −0.003 | −0.026 | +0.023 |

The mechanism beats the unconditional baseline in every cell, so
**beats-null could pass**. But every cell is at or below zero gross, before
bounded costs, against a declared floor of **+0.15 net R** — the floor
would refuse on the definition partition by a margin of the floor itself.
The two other candidates prepared the same day are worse:

| candidate | gates | definition cells, gross R | against always-long |
|---|---|---|---|
| **B** trend: close above 50-MA, hold {10, 20}, stop {3, 5} | POWERED at 982, ρ 0.000 | −0.047 to −0.102 | worse in every cell |
| **C** ungated breakout: 20-bar high, hold {5, 10}, stop {2, 3} | **UNDERPOWERED** (733 < 748) | −0.108 to −0.250 | far worse |

Two facts should be read together. The definition partition is the 1993 to
2003 window and is unkind to long-only entries at every geometry: the
always-long baseline is negative throughout. And a floor of 0.15 net R per
trade on a three-to-five-day index ETF position is a large number — at a
5 % stop it is 0.75 % per trade on average, and no entry on the closed
enum comes within an order of magnitude of it on the definition data.

**The floor is the author's declaration and is not recommended here.** What
this Draft records is that, at the floor as declared, the best price_daily
question the closed enum can state is one the definition partition already
answers, and its verdict would close the lab.

## Required capabilities

`NATIVE_STOP` only: the entry is a market order, the exit is by time, the
stop is native. Nothing rests.

## Tier and its child

Mechanism. Its implementation child (M8.4) would carry the winner cell's
spec alone, plateau of one cell, on the same axis.

## What would make a null uninformative

Fewer than three names (refused at registration). A plateau the sweep
cannot hold (refused at registration). A measurement seed not recorded
(the loop records what ran; pass `--seed`).
