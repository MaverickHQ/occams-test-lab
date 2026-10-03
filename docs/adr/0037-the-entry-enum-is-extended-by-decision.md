---
status: decided 2026-09-12 — adopted by the author with all three kinds; M3.9 opened the same day
---

# The entry enum is extended by decision, one mechanism at a time

`EntryKind` is a closed enum (M3.2, R4.2's sibling): a kind that is not a
member raises at construction. Six members exist — two apparatus kinds,
`ALWAYS` and `COIN_FLIP`, and four mechanism kinds, `BREAKOUT_HIGH`,
`BREAKOUT_LOW`, `CLOSE_ABOVE_MA`, `CLOSE_BELOW_MA`. Each is one branch of
`signal()` in `occams/engine/day_boxed.py`, which reads bars `[0, first)`
and never the box itself; one row in the compiler's `GEOMETRY` table, which
is what refuses a buy-stop below the market (M3.4, the v1.8 defect by
name); one row in `REQUIRED_PARAMS`; and one component of the spec hash
(D4, ADR-0007).

**The enum is closed so that the space of statable mechanisms is
enumerable.** That is what makes "what did we search?" answerable (N6) and
what the search correction can be honest about (R4.4): k counts cells
inside one kind, and the overlap gate (R4.9) sees every question on an
axis. A kind added on a whim is a family added to the search without a
record.

On 2026-09-12 the first price_daily prepare (DRAFT-004) showed the closed
enum's limit: every mechanism it can state on daily bars is at or below
zero gross on the definition partition against the declared floor, and
the best of them — a close below its moving average — fires on half the
days of a bear market and says little about *why* the next days should
revert. The floor is the author's declaration and is not this ADR's
subject. The enum is. The question is not whether to open it but **how a
kind is added so that the enumeration stays honest.**

## Decision (proposed)

### The rule

An entry kind is added only by an ADR that states, before any prepare on
it:

1. **The mechanism it exists to test**, in one sentence, with both
   interpretations — why prices alone would carry an edge after this
   signal, and what a null would mean.
2. **Its formula over bars `[0, first)`** and its integer or percentage
   parameters. Parameters belong to the Hypothesis (fixed in the template
   or swept as an axis); the kind is the family.
3. **Its geometry row**: whether it yields a level and where that level
   sits relative to the market at decision time, or whether it fires as a
   market entry (`NONE`). This is the row M3.4's refusal reads.
4. **Its look-ahead test**: a fixture on which the signal day's own bar
   would fire it and the prior bars would not, asserting it does not fire.
5. **Its Pine obligation**: `to_pine` (M11.1, cap-blocked) must derive it
   from the spec when that row opens. Until then the Python signal is the
   one source (R8); no kind may exist only in Pine (M11.3).
6. **Its auditor family** (added at adoption, found by building M3.9): a
   kind belongs to a family in `occams/costs/auditors.py` or its fills
   cannot be audited, and unaudited means refused (M5.7). The three kinds
   below form the *reversal* family and share the trend family's
   auditors: overnight gap, opening auction, halt.

A kind proposed after reading the measurement partition is refused (D13).
Reading the definition partition is permitted — it is the calibration set
— and this ADR was written after reading it; the kinds below are stated
as mechanisms with a prior reason, and their parameters are not chosen
here. **A kind is never tuned into existence.**

Every question on a new kind is a question on the same axis and the same
partition as the ones before it, so the overlap gate refuses it until it
states its distinction (R4.9). The distinction is the mechanism sentence
from point 1. That is the accounting for choosing among kinds: not a
Bonferroni term, but a recorded, refusable declaration per family.

### Three kinds this ADR adds, if adopted

All three are long-side market entries on the next open (`GEOMETRY` row
`NONE` for both sides), fire from bars `[0, first)` only, and carry a
time exit and a percentage stop like the existing moving-average kinds.

| kind | params | fires when | mechanism |
|---|---|---|---|
| `DOWN_RUN` | `runs` | each of the last `runs` closes is lower than the one before | **reversal after a streak**: consecutive declines exhaust short-horizon sellers and the next days correct; a streak is rarer and sharper than a close below an average |
| `RETURN_BELOW` | `lookback`, `percent` | close[first−1] / close[first−1−lookback] − 1 ≤ −percent/100 | **reversal after a decline of size**: a fall of a declared magnitude over a declared window over-corrects; the magnitude is the signal, not the position relative to an average |
| `PULLBACK_IN_TREND` | `short`, `long` (short < long) | close[first−1] below its `short`-bar average and above its `long`-bar average | **reversal conditioned on trend**: a dip inside an uptrend is bought back; the two existing averages combined into one statement |

Each is a conjunction the existing kinds cannot express: `DOWN_RUN` is
not a moving-average relation at all; `RETURN_BELOW` is a magnitude;
`PULLBACK_IN_TREND` needs two lookbacks in one entry, which `Entry` can
carry but no current kind reads. Their mirrors (`UP_RUN`, `RETURN_ABOVE`)
are *not* added: the persistence mechanism was prepared as candidate B on
2026-09-12 and was worse than random entry in every cell; a second
persistence family would be a family added without a reason.

### What does not change

- The two apparatus kinds stay two. The null for any new kind is the
  geometry-matched random entry the beats-null check already draws; a
  kind needs no control of its own.
- The spec hash covers the kind and its params as it covers the existing
  ones (D4). A question on a new kind is a new family with a new hash.
- `Side.SHORT` on these kinds is constructible but not tradeable here: no
  borrow capability exists in `Capability` (ADR-0018), so a short spec
  would be refused at compile for an undeclared capability the venue does
  not offer. Shorting is a capability decision, not an enum one.

## Consequences (if adopted)

- `occams/spec/spec.py`: three members. `occams/spec/compile.py`: three
  `GEOMETRY` rows and three `REQUIRED_PARAMS` rows; `to_engine` refuses
  `PULLBACK_IN_TREND` with `short >= long` by name.
- `occams/costs/auditors.py`: a *reversal* family; `family_of` refuses a
  kind with no family by name instead of failing on a lookup.
- `occams/engine/day_boxed.py` `signal()`: three branches, reading
  `_on_basis` rows as the moving-average kinds do so a split loads as an
  action. The position-boxed engine reuses `signal` unchanged.
- Tests: one look-ahead fixture per kind; a hash test that a new kind's
  spec differs from every existing kind's at equal params; the M3.4
  geometry test extended to assert a `NONE` row admits only market orders.
- `occams/proposers/price.py`: a mechanism sentence per kind, both
  interpretations, a falsifier — the text in the table above is the
  draft of it. `question prepare --entry` gains the three names.
- `TASKS-v4.md`: a row **M3.9 — entry kinds added by ADR-0037** under M3,
  done when the five points above are met for each kind; a note on M11.1
  that `to_pine` owes three derivations.
- `CONTEXT.md`: *entry kind* is a family; *mechanism* is what a kind
  exists to test; a kind is added, never discovered.

## Considered options

- **Keep the enum closed and change nothing.** The honest default, and
  the one the lab's own falsifier points at: two nulls, no promising
  third. Rejected only conditionally — if the author holds that the
  closed enum's four mechanisms are the whole of what daily bars can say,
  the lab should close on the third null rather than add families to
  avoid it. This ADR exists so that a third question, if there is one, is
  stated as a mechanism and not as a way around a verdict.
- **An open expression entry** — a formula string evaluated over bars.
  Rejected: the hash would cover free text, which is the free-text kind
  M3.2 refused; a formula language is a garden of forking paths with no
  enumeration and no per-family record; the look-ahead test cannot be
  written once for all formulas.
- **Add the usual indicator set at once** — RSI, MACD, Bollinger, rate of
  change, and their thresholds. Rejected: each is a family that will be
  searched; adding ten at once is adding ten searches with one ADR's
  worth of reasons. One mechanism, one kind, one reason.
- **Gap kinds** (`GAP_DOWN`, `GAP_UP`): open below the prior low, above
  the prior high. Rejected for now: the signal contract reads bars before
  the box and never the box's own open; a gap is known only at the box's
  open. Admitting it means a second signal contract ("at the open") with
  its own fill and look-ahead rules — a separate ADR if wanted.
- **Re-declare the floor instead.** The floor is the author's (M0.15,
  DRAFT-004); no value is proposed here, and changing it is a recorded
  decision of a different kind. This ADR is orthogonal to it: the kinds
  above would be worth stating at any floor.

## Adoption

Adopted 2026-09-12 by the author with all three kinds; M3.9 opened and
built the same day. A prepare on a new kind is a reading of DRAFT-004's
successor, and registration remains the human act.
