---
status: REGISTERED as Q-003 on 2026-09-11 by the author and RESOLVED NULL the same day; RE-REGISTERED as Q-004 on 2026-09-12 over three names, stop axis only, superseding Q-003, and RESOLVED NULL the same day (EV −0.045 net R over 2,088 trades, all four checks refused). See the Register and the status log
tier: mechanism (ADR-0027)
axis: regime — runnable; budget declared 2026-09-10 (M0.11)
relates_to: "TASKS-v4.md M8.1 · docs/adr/0005 · docs/adr/0027 · docs/adr/0036 · docs/M0-ANSWERS.md §M0.7 §M0.15"
---

# DRAFT-003 — Within-regime continuation on the confirmed class

A **Draft**, in the sense `CONTEXT.md` gives the word: a proposed Hypothesis
carrying a mechanism and a falsifier, with **no standing until a human
confirms its registration**, which is the act that spends alpha. Nothing
here has been measured. Nothing here has cost anything.

The author agreed on 2026-09-11 that this is the first question to register.
It is the `RegimeProposer`'s draft, written down so the registration is a
reading and not a reconstruction.

> **Prepared 2026-09-11 against the real archive** (`python -m occams question
> prepare`): the classifier frozen at `0434836a176a`; 350 signals on the
> definition partition at 0.0989 per name-day, ρ 0.000; `available_n` 837
> on the measurement partition against `required_n` 748 per cell at the
> configured rate — **powered**, by a thin margin. Nothing registered.
>
> **Re-prepared 2026-09-11 on three names (SPY, QQQ, DIA) as Q-004**, after
> Q-003 resolved NULL on two: 458 definition signals at 0.0949 per name-day;
> `available_n` 1206, effective 1074 at measured ρ 0.434; `required_n` 748
> per cell — **powered and supportable**. Refused by the overlap gate: 67% of
> the observations were consumed by Q-003, above the 50% threshold; the
> author must supersede or distinguish (R4.9). Target-axis sensitivity 0.4%
> on the definition partition. Nothing registered, nothing spent.
>
> **Registered as Q-004 on 2026-09-12** by the author with `--supersedes
> Q-003` and the target axis dropped: k = 2, 0.02 alpha, `available_n` 1074
> effective against 748 required. Queued for the loop.
>
> **Resolved NULL on 2026-09-12**: 2,088 trades on the measurement
> partition, EV −0.0451 net R at bounded costs, *p*(null ≥ winner) 0.983.
> The same answer as Q-003, on a set where leave-one-out could run. The
> plateau refusal was structural (a two-cell sweep against a four-cell
> plateau) and is now refused at registration. The lab falsifier stands at
> two of three.

## Read this first — what must exist before it can be registered

1. **Real bars in the archive.** Registration computes `available_n` from
   the measurement partition (M8.2), and the archive holds nothing until
   the M0.7 class is ingested — `python -m occams ingest`. No bars, no
   registration.
2. **The classifier, frozen first** (ADR-0005, M7.6). `calibrate` runs on the
   definition partition of the same archive and the frozen hash goes into
   the mechanism statement below. Calibration is a priori and happens once.
3. **A human registration** through `register_question`, with the
   accountant, at the regime axis's configured mechanism rate.

## Mechanism

In the *up* regime as labelled by the frozen classifier (index-level),
breakout entries carry positive EV in net R because participants
under-react to continuation within an established regime: a breakout that
occurs while the medium-term average is above the long-term average is
more often followed through than faded. The claim is about the instrument's
own dynamics on the confirmed class — currently-listed, liquid US-listed
ETFs and large caps on daily bars — not about selection from a universe.

## Both interpretations

- **If true:** the winner cell clears the declared floor, beats random
  entry under the same stop and exits at the corrected alpha, holds a
  plateau across neighbouring stops and targets, and survives leave-one-out
  over names.
- **If false:** within-regime continuation is not distinguishable from
  random entry after costs; the regime label carries no information the
  price already lacks.

## Falsifier

The winner cell's EV in net R at or below the null's corrected quantile, or
below the floor, or a plateau that fails, or an effect carried by one name.
Any one refuses; the Verdict is then null with the refusals named.

## Declared floor

The pair: **0.15R net per trade** and **50 trades a year** over the pooled
names. The M0.15 convention; declared here, before running.

## Search space — declared, enumerated, and closed

Stop ∈ {2 %, 3 %} × target ∈ {2R, 3R}: **four cells**. Entries are the
breakout of the prior 20-day high on a stop order, in the up regime only;
the time exit is one bar (day-boxed, `INTRADAY` horizon). `search_space_size
= 4`; spend at the configured regime mechanism rate is `rate × 4`.

## Power

`sigma_r` declared at 1.2R with provenance *M0.15 convention; superseded by
the definition-period measurement*. Required N per cell at the configured
rate is computed at registration by the vendored calculator; `available_n`
is `names × years × trades per name-year` on the measurement partition, then
corrected by the measured intra-cluster correlation (M7.7) before the
power check. An underpowered question is refused at registration (M8.2).

## Required capabilities

Native stop, resting orders (the entry is a stop order).

## Tier and its child

Mechanism. On a supported Verdict, the implementation child for the winner
cell registers from the same axis at the implementation rate (M8.4).

## What would make a null uninformative

Fewer than three names in the pooled set (leave-one-out cannot run); a
measurement partition shorter than the classifier's longest lookback; a
classifier calibrated on anything but the definition partition.
