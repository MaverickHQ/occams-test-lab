---
status: REGISTERED as Q-005 on 2026-09-12 by the author and RESOLVED NULL the same day — EV +0.051 net R over 893 trades, beats-null and plateau passed, the floor and leave-one-out refused; the third null: THE LAB CLOSED (ADR-0033). See the Register and the status log
tier: mechanism (ADR-0027)
axis: price_daily — runnable; budget declared 2026-09-10 (M0.11); 0.20 of 0.20 remains
relates_to: "TASKS-v4.md M3.9 M8.1 M8.2 · docs/drafts/DRAFT-004 · docs/adr/0037 · docs/adr/0027 · docs/M0-ANSWERS.md §M0.7"
---

# DRAFT-005 — Reversal after a streak

A **Draft**: a proposed Hypothesis carrying a mechanism and a falsifier,
with **no standing until a human confirms its registration**, which is the
act that spends alpha. Nothing here has been measured on the measurement
partition. Nothing here has cost anything.

The first draft on an entry kind added by ADR-0037. Written down after the
author adopted the ADR and opened M3.9, so that a registration is a reading
and not a reconstruction. The lab falsifier stands at two of three.

## Mechanism

After three consecutive lower closes, a liquid US index ETF carries
positive EV in net R over the next three to five bars because a streak of
declines exhausts short-horizon sellers and the next days correct:
**reversal after a streak** (`EntryKind.DOWN_RUN`, `runs = 3`). Long only.
Market order on the next open. Percentage stop. Time exit. No regime gate.
Position-boxed engine (`Horizon.MULTI_DAY`, D6). SPY, QQQ, DIA as archived.

`runs = 3` was declared before any bars were read: three down days is the
streak the reversal literature names. It is not the product of a search.

## Both interpretations

- **If true:** the winner cell clears the declared floor and beats random
  entry at the corrected alpha — the streak reversal is real after costs.
- **If false:** the days after a streak of declines are not
  distinguishable from random entry after costs — streaks carry no
  reversal to trade on this class at this horizon.

## Falsifier

The winner cell's EV in net R at or below the null's corrected quantile,
or below the floor.

## Declared floor and search space

The pair in use since M0.15: **0.15 net R per trade**, **50 trades per
year** pooled; σ 1.2 by convention, superseded by the definition-period
measurement at registration. Sweep stop ∈ {3, 5} % × hold ∈ {3, 5} bars,
**k = 4**; a plateau of 4 fits it exactly; both axes bite (stop 95.6 %,
hold 96.8 % of definition trades change along them).

## Prepared 2026-09-12 — the gates

| | |
|---|---|
| definition signals | 341 at 0.0707 per name-day |
| available_n on measurement | 898 → effective **739** at measured ρ 0.540 |
| required_n per cell | 748 at α 0.01 |
| verdict of the gates | **UNDERPOWERED by nine effective trades**; registration would be refused (M8.2) |

## What the definition partition says

Mean gross R per trade by cell against the always-long baseline at the
same geometry (every box, one position at a time):

| stop | hold | streak cells | always-long | difference |
|---|---|---|---|---|
| 3 % | 3 | −0.017 | −0.058 | +0.041 |
| 3 % | 5 | **+0.093** | −0.057 | **+0.151** |
| 5 % | 3 | +0.014 | −0.027 | +0.041 |
| 5 % | 5 | **+0.081** | −0.026 | **+0.107** |

This is the first mechanism the lab has prepared whose definition-partition
cells are **positive gross**, and the margin over random entry at a
five-bar hold is of the floor's own size. Net of bounded costs the five-bar
cells would sit below +0.15, so the floor is still the binding check — but
by a fraction of itself, not by an order of magnitude as every earlier
candidate was. Beats-null would very likely pass.

The two other kinds ADR-0037 added, prepared the same day with declared
parameters: `RETURN_BELOW(5 bars, 3 %)` — powered at 848 effective, ρ
0.798; cells −0.076 to +0.018 gross, mixed against the baseline.
`PULLBACK_IN_TREND(5, 50)` — powered at 1,026 effective, ρ 0.820; cells
−0.023 to +0.001 gross, +0.016 to +0.048 over the baseline. Neither is
near the floor.

## Re-prepared on four names, 2026-09-12

The author widened the class: **IWM** (the Russell 2000 ETF, listed
2000-05-26, 6,612 bars, 106 actions, one request at $0) joined SPY, QQQ
and DIA. No parameter, mechanism or floor was touched.

| | |
|---|---|
| definition signals | 391 at 0.0709 per name-day (IWM contributes 691 definition bars, 2000-05 to 2003-03) |
| available_n on measurement | 1,201 → effective **933** at measured ρ 0.557 |
| required_n per cell | 748 at α 0.01 |
| verdict of the gates | **POWERED**, supportable (four names), plateau fits, both axes bite (stop 96.4 %, hold 97.2 %), no overlap on the axis |
| would spend | 0.04 of 0.20 on price_daily |

The definition cells on four names, gross R against always-long at the
same geometry:

| stop | hold | streak cells | always-long | difference |
|---|---|---|---|---|
| 3 % | 3 | −0.036 | −0.061 | +0.025 |
| 3 % | 5 | **+0.056** | −0.064 | **+0.120** |
| 5 % | 3 | −0.002 | −0.028 | +0.026 |
| 5 % | 5 | **+0.055** | −0.030 | **+0.084** |

IWM's definition years are 2000 to 2003, a bear, and its fifty-odd
signals pull the five-bar cells from +0.09 to +0.06 gross. The shape is
unchanged: positive gross at a five-bar hold, a margin over random entry
of roughly the floor's size, and an absolute level that bounded costs
would leave below +0.15 net. **Beats-null is likely to pass; the floor is
likely to refuse.** The third null closes the lab. Registration is the
author's act and nothing here recommends it.

**A calendar note, found by this ingest.** IWM's last bar is 2026-09-11,
one day later than the other three, and the partition boundaries are cut
from the archive's live common span, so all three moved: the definition
end from 2003-03-01 to 03-02, the measurement end from 2019-12-21 to
12-23. Both moves fell on weekends and no bar changed partition — checked
name by name. But the mechanism is a slow leak: every trading day added
at the end moves the measurement boundary about 0.8 of a day into the
sealed reserve. Recorded in the status log with the fix proposed: freeze
the calendar as a Register record and cut every partition from it.

## Registered as Q-005 on 2026-09-12

After the calendar was frozen (ADR-0038; pinned to 1993-01-29 →
2026-09-10, the span the classifier freeze and Q-003/Q-004 already used),
the author registered this Draft with `--by MaverickHQ --yes`: 391
definition signals, `available_n` 1,200 → effective **932** at ρ 0.557
against 748, k = 4, **0.04 alpha** on price_daily (0.16 remains). Queued
for the loop; not yet measured. Pass `--seed` to the loop.

## Resolved NULL on 2026-09-12 — and the lab closed

The loop ran with seed 20260911 on the frozen calendar. Measurement
partition 2003-03-01 to 2019-12-21, four names, position-boxed engine at
`e05a659`: **893 trades, EV +0.0513 net R at bounded costs**, 53.2 trades
a year against the 50 declared. The winner cell was stop 5 %, hold 3
bars. **Beats-null passed. Plateau passed.** Refused by two checks, each
with its evidence in the Register: **floor** — +0.051 against +0.15; and
**leave-one-out** — the pooled effect is carried by IWM: without it
+0.014 net R. Paths archived, 2,000 draws.

Read plainly: after three lower closes, buying the open and holding three
to five days on these four index ETFs over sixteen years earned about a
twentieth of a stop per trade after bounded costs — real relative to
random entry, a third of the floor declared before the run, and mostly
in the small-cap ETF. That is a result, and it is the first positive one
the lab produced. It is not the edge the floor asked for.

It was the third resolved mechanism verdict with the falsifier's outcome.
**`LabClosed` was appended: the lab is closed** (ADR-0033). Nothing
registers after that record.

## What made this registrable without touching a parameter

The three-name refusal was power, not substance: nine effective trades
short of 748 at ρ 0.54. A fourth name of the M0.7 class raised the pooled
count by a third without changing the mechanism, the parameters or the
floor — the same lever the lab pulled between Q-003 and Q-004, and not a
search. Changing `runs` to 2 would also have raised the count, and would
have been a different question; it was not proposed and was not done.

## What would make a null uninformative

Fewer than three names (refused at registration). A plateau the sweep
cannot hold (refused at registration). A measurement seed not passed to
the loop (its default is 1; pass `--seed`).
