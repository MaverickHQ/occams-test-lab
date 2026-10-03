# Programme conclusion — what three verdicts established

**Dated 2026-09-12. Adopted by the author on 2026-09-20**, after the second programme had run and its own conclusion was adopted; the body stands as drafted, and what changed between the drafting and the adoption is appended at the end. Written because
ADR-0033 committed to it, in advance, for exactly this outcome:

> A lab falsifier firing is a **result**: the premise that a detectable
> edge exists — in this instrument class, at this cost structure, reachable
> by this apparatus — has been measured and found wanting. It is the most
> valuable thing the lab can produce short of an edge, and it is the one
> outcome nobody builds a lab to hear.

That is where the programme is. Nothing here is new analysis. Every number
below is in the Register — the record number is given as `#n` — or, where
marked *log*, in the dated status log of `TASKS-v4.md`. The Register holds
**34 records**, chain-verified, head `c2706a09716b`, from
2026-09-11 18:28 UTC to 2026-09-12 10:45 UTC, when `LabClosed` was
appended (#33). No money appears in it and none appears here (ADR-0008,
S7).

## 1. The scoreboard

Three mechanism questions were registered by the author, measured on a
partition no one looked at before registration, and resolved by the
machine against a floor declared before the run. All three resolved
**null**. The lab's falsifier was declared as three (M0.18); it fired on
the third.

| | Q-003 | Q-004 | Q-005 |
|---|---|---|---|
| axis | regime | regime | price_daily |
| mechanism | breakout above the 20-bar high in the up regime of classifier `0434836a176a`, one-bar box | the same, three names, stop axis only, superseding Q-003 | reversal after three consecutive lower closes, held 3–5 bars, no regime gate |
| names | SPY, QQQ | SPY, QQQ, DIA | SPY, QQQ, DIA, IWM |
| engine | day-boxed | day-boxed | position-boxed |
| search space k | 4 | 2 | 4 |
| alpha spent | 0.04 (#2) | 0.02 (#10) | 0.04 (#23) |
| required / available N | 748 / 837 (#3) | 748 / 1,074 (#11) | 748 / 932 (#24) |
| trades measured | 1,391 (#5) | 2,088 (#13) | 893 (#26) |
| seed | 20260911 | 1 | 20260911 |
| EV per trade, net R, bounded costs | **−0.047** (#9) | **−0.045** (#21) | **+0.051** (#32) |
| trades per year, against 50 | 82.8 | 124.3 | 53.2 |
| beats-null | refused | refused, p 0.983 (#15) | **passed** |
| plateau | passed | refused, structural (#14) | **passed** |
| floor +0.15 net R | refused | refused (#16) | refused, +0.051 (#27) |
| leave-one-out | refused, structural (two names) | refused, carried by DIA (#17) | refused, carried by IWM (#28) |
| outcome | null (#9) | null (#21) | null (#32) |
| paths archived | 2,000 draws (#8) | 2,000 draws (#20) | 2,000 draws (#31) |

**Lab-level records.** The classifier: index-level on SPY, short 20, long
100, band 0.01, frozen on the definition partition 1993-01-29 to
2003-02-28, regime shares up 50.8 %, down 34.6 %, ranging 14.6 %,
persistence 0.974 (#1, superseding #0 after a calendar defect). The
calendar: 1993-01-29 to 2026-09-10, definition to 2003-03-01, measurement
to 2019-12-21, reserve after, split 0.3 / 0.5 / 0.2 (#22). Every question
consumed the same measurement span (#4, #12, #25). The reserve was never
looked at. Alpha spent: 0.06 of the 0.20 declared on regime, 0.04 of the
0.20 on price_daily; the 0.10 reserve untouched (*log*, M0.11).

**The archive.** Four liquid US index ETFs from one licensed source, no
bars in the repository: SPY from 1993, QQQ from 1999, DIA from 1998, IWM
from 2000, all to 2026-09-10 on the frozen calendar. Four of five hundred
monthly symbol requests used; **$0 spent on data** (*log*, M0.6, M0.14).

**The controls.** Before every verdict the same pipeline refused a dead
world and accepted a planted edge on both engines, and did so again on
every build of the console (S3, S10; `docs/console.html`).

## 2. What is established

**Breakout continuation inside the up regime, on liquid US index ETFs,
2003 to 2019, is worse than random entry in the same regime.** Twice,
on two and then three names, through the same one-bar box: −0.047 and
−0.045 net R per trade at bounded costs, and on the second run the null's
own mean was −0.034 with p(null ≥ winner) = 0.983 over 4,000 draws (#15).
The regime gate did not create an edge where the ungated breakout, run as
candidate C on the definition partition, had none either (*log*,
2026-09-12).

**Reversal after a three-day streak, on four index ETFs over the same
sixteen years, is better than random entry and positive after bounded
costs — and a third of the floor.** +0.051 net R per trade over 893
trades, 53 a year; beats-null passed, the plateau held (#32). Without IWM
the pooled effect is +0.014 (#28). It is the first positive result the
lab produced, it is small, and it lives mostly in the small-cap ETF.

**At the floor the author declared before any bar was read — 0.15 net R
per trade and 50 trades a year — no mechanism this apparatus can state on
this class reached it.** Six entry kinds on daily bars, three of them
added by decision after the first price_daily prepare showed the closed
enum's limit (ADR-0037); the best of them a third of the way there.

**The apparatus is trustworthy in the way that matters.** Every refusal
that stopped a question is in the Register with its evidence (#14–#17,
#27–#28). Three of the eight refusals across the programme were
*structural* — a gate that could never have passed on the set as
registered — and each was found, disclosed in the log the same day, and
turned into a guard that refuses before any alpha moves: a pooled set
below three names, a plateau larger than the sweep can hold, an
implementation child inheriting a plateau it could never show (*log*,
2026-09-11 and 2026-09-12). The nulls stand on the substantive checks in
every case.

## 3. What is not established

- **That the floor was the right floor.** It is the author's declaration
  (M0.15's headline, adopted for every question). At a lower floor Q-005
  would still have refused leave-one-out. Nothing here recommends a value.
- **Anything about the reserve.** Sealed, never looked at (ADR-0006). The
  Q-005 effect on 2019 to 2026 is unknown, and stays unknown until a look
  is spent — which a closed lab does not spend.
- **Anything about costs beyond the bounded model.** M5.0, the measured
  spread on the demo account, was never done. Every verdict is at
  *bounded* costs (#9, #21, #32); at measured costs the numbers move, and
  only one direction is plausible for a mechanism trading the open.
- **Obtainability in a forward window.** No Strategy passed MEASURED; the
  forward window, the proposal venue and the live gate (M9, M10) were
  built and never reached by a real question.
- **The regimes other than up, the short side, intraday horizons, other
  classes.** Not asked. The down and ranging regimes on the regime axis
  were never registered; the closed enum has no short-side capability
  (ADR-0037); the class was four index ETFs.
- **IWM alone.** That the Q-005 effect concentrates there is a reading of
  the leave-one-out evidence, not a registered question. It would be a
  new question on a one-name class, which the registration guard refuses.

## 4. The findings that outlast the questions

**A gate that cannot pass is decoration, and it costs alpha.** Three
times a check was structurally unpassable on the set as registered.
Each time the null was still a null on the other checks, but the alpha
behind the dead gate bought nothing. The lab now refuses at registration
what it used to discover at resolution.

**The calendar must be frozen, not derived.** Partitions cut from the
archive's live span move with its last bar — a weekend on the day it was
found, a week of the sealed reserve after a fortnight of ingests. The
span is a Register record now (#22, ADR-0038), and a cut that would move
a recorded boundary is refused by name.

**Pooling correlated instruments is not free, and the correction is not
an integer.** Same-day correlation of net R across index ETFs measured
0.43 on breakouts and 0.54 to 0.82 on reversals (*log*). A design effect
rounded to an integer cluster size erased a 12 % correction once; it is
computed with the real mean now.

**The definition partition may be read, and reading it honestly is the
point.** Every prepare on this lab showed the calibration set's cells
against an always-long baseline before the author spent anything. That
is how six candidates were declined at $0 and one was registered — and
it is why the third null was not a surprise.

**An entry kind is a family, added by decision.** The closed enum kept
"what did we search?" answerable; extending it took an ADR that states
the mechanism, the formula over prior bars, the geometry, the look-ahead
test, the Pine obligation and the auditor family (ADR-0037). Three kinds
were added that way in a day, and none was tuned into existence.

**The seed is part of the record.** One measurement ran on the loop's
default seed because the flag was not passed (#13, seed 1); the record
says 1 because that is what ran, and the next run passed it.

## 5. The decision

The lab is closed. What follows is the author's, and the Register does
not choose among these:

**A — Publish.** The Register is publishable by construction (ADR-0008);
the console renders it offline; the publication gate (M11.7, R7) is an
explicit recorded decision and its prepublish check — forbidden raw bars,
venue terms, credential shapes, money in the Register — is not yet built.
Publishing a lab that closed on its own declared threshold publishes the
count, the floors and every verdict with its evidence, which is the
negative result this apparatus was built to be able to produce honestly.

**B — A new programme at a re-declared floor.** The floor is one of the
author's numbers and is not recommended here. What the Register says
about it: at any floor, Q-005 would still refuse leave-one-out; and a
floor re-declared after three verdicts is a floor declared with knowledge
of them, which is the thing every gate in this lab exists to prevent. It
would be a new programme with its own M0, not a resumption.

**C — A new class or apparatus.** Measured costs (M5.0), a forward window
reached by a real question, instruments beyond four index ETFs, or a
short-side capability. Each is a different premise from the one this lab
tested, and would be registered under a new falsifier.

**D — Stop.** A defensible outcome, and the one the falsifier was declared
to produce. The programme spent no money on data, put none at risk, and
reached three verdicts on a sealed record in two days of running.

## 6. Was it worth doing?

Three mechanism verdicts, on sixteen years of four instruments, at bounded
costs, against a floor and a falsifier declared before the first bar was
read, with every refusal recorded beside its evidence and every defect in
the apparatus disclosed the day it was found. One of the three is a small
positive result that a less careful lab would have called an edge. The
closed programme's lessons — that pooling is not free, that a level is a
confound, that a number needs its provenance, that the machinery must be
able to refuse — were applied from the first commit rather than learned
again, and the one lesson this lab adds to them is that a gate must be
shown passable before alpha is spent behind it.

That is what a lab that can hear "no" is for.

---

## Adopted 2026-09-20 — what changed between the draft and the adoption

The body above is the draft of 2026-09-12, unedited. Between it and the
adoption the lab ran its second programme, and four sentences above have
been overtaken by records rather than by re-analysis:

- **§5 A.** The publication gate's check *is* built (M11.7, 2026-09-14):
  `tools/prepublish.py` runs in `make check` and CI on every committed
  page and Register, and on this document. Publishing itself stays a
  recorded decision (R7) and none has been recorded.
- **§3, obtainability.** Reproduction never skips (M11.5, M11.6,
  2026-09-18): Q-005 above is recreated exactly from the archive on the
  current tree and at its own commit; the public path proves the pipeline
  on synthetic fixtures and refuses an exact-historical claim.
- **§5 B and C.** The second programme (M12, 2026-09-12 to 2026-09-20)
  was the new programme under its own Register, floor, falsifier and
  alpha, with the same declared numbers; its conclusion,
  `docs/PROGRAMME-2-CONCLUSION.md`, is adopted. The execution host and the
  alerting subscription are deferred outside this lab (ADR-0044); no
  forward window opened.
- **§2, the apparatus.** Since this draft the checks are five (ADR-0043)
  and the surface a sweep optimises is the margin over always-long
  (ADR-0045); the verdicts above were reached under four checks and the
  EV rule and are not re-judged.

Nothing above is a verdict changed; the three nulls, the falsifier and the
closure stand as recorded.
