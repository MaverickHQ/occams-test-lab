---
status: decided 2026-09-13 — adopted by the author the day it was drafted; the rule is in both engines (`limit_through_the_open`) with a test on a gapped bar in each, the vendored module untouched; `breakout_low` is measurable from the next grid (M12.9 closed)
---

# A resting limit that the bar opens through fills at the open

The fill is derived, never declared (M3.7): an order is placed against
the bars, and `occams/core/execution.py` says where it filled. That
module is the donor's, vendored at a recorded commit (`PROVENANCE.json`,
2026-09-10) and never edited here. Its `fill()` has two rules for a
resting order:

- **A stop that the bar opens through fills at the open.** `opens[i] >=
  lvl` for a buy stop is `gapped`, and the fill is `opens[i]` — the
  worse-case rule M3.8 names: a gap through a protective stop records
  worse than −1R.
- **A limit fills at its level whenever the bar's range reaches it.**
  `lows[i] <= lvl` for a buy limit returns `(i, lvl)` with no look at the
  open. The donor's comment: *a limit does not slip in your favour, and
  cannot slip against you past its own level.*

The second rule is right inside a session and wrong across one. A buy
limit resting at 102.6 overnight, on a bar that opens at 102.4, is
filled by the opening auction at 102.4: nothing printed at 102.6 that
morning. The obtainability auditor (M5.5, `overnight_gap`) says exactly
this — it refuses a fill booked *at its level* when the level lies
strictly between the action-restated prior close and the open — and the
engine's contract refuses the whole run on the first five such fills.

**What the first survey showed.** `grid-001` runs `breakout_low` as a buy
limit at the lookback low (`price_template`: `OrderType.LIMIT` for a
breakout other than `BREAKOUT_HIGH`; `signal()` returns the minimum low of
the lookback as the level). Every one of its **6,528 cells** — 1,632 in
each of four universes, four lookbacks, both horizons, every regime and
geometry — was refused by the overnight-gap auditor, the first problem in
the words *"bar 424 DIA: fill booked at level 102.6 inside the overnight
gap 102.7 → 102.4; nothing traded there — the obtainable fill is the
open."* The kind that ADR-0037 admitted to the enum is unmeasurable as
the engine stands. The same auditor also refused 112 `breakout_high`
cells on the Dow, every one on the same CVX bar: a stop fill booked at
its level inside a gap measured from the prior close restated for an
action, where the raw prior close was on the other side of it. The rule
below is stated on the restated basis so that it covers this case too;
the bar is to be looked at when the rule is implemented.

**The direction of the correction.** For a buy limit that the bar gaps
*down* through, the open is *below* the level: the obtainable fill is a
better entry than the booked one. This correction is not the worse-case
rule; it is the obtainable-price rule. What it does to a cell's EV is the
measurement's to say. What it does to the engine is make its fills the
ones a venue with an opening auction would have given, which is the only
standard the auditor holds (F4).

## Decision (adopted 2026-09-13)

**A resting limit order that the bar opens through fills at the open;
otherwise at its level.** On the fill bar `i`, a buy limit fills at
`min(opens[i], level)` and a sell limit at `max(opens[i], level)` — the
mirror of the stop rule the module already has — with the open taken on
the same basis the level was stated on (the box's basis after actions,
ADR-0021).

Where the rule lives: **in the engines, not in `core`.**
`occams/engine/day_boxed.py` and `occams/engine/position_boxed.py` own
the `Fill` signature (M5.6: prior close, open, high, low, volume, next
open) and already restate the market for the placement check; they apply
the rule to what `ex.fill` returns. The vendored module is untouched — a
change to it is a re-vendor with a new PROVENANCE, and the donor is a
read-only reference.

The auditor is unchanged. It remains the check that the rule is right:
the corrected fill passes it, and the fixture that carries the old fill
is refused by name.

## Consequences

- **Engine change with a test on a gapped bar**, in both engines: a bar
  that opens below a resting buy limit fills at the open; a bar that opens
  above it and trades down to it fills at the level; a sell limit mirrors
  both; the overnight-gap auditor passes the first and would have refused
  the fill the old rule booked. `make null` still refuses and `make
  signal` still accepts (S3, S10): neither control places a limit.
- **`engine_code_sha` changes.** Every survey cell carries the hash of the
  engine files it was computed by; cells computed after the change are
  distinguishable from record #9's by construction, and #9 is not
  recomputed — the Register appends, never overwrites.
- **`breakout_low` becomes measurable from the next grid.** `grid-001` is
  never edited (M12.2); a grid that supersedes it carries the kind on the
  corrected engine, and the 6,528 refused cells are then computed for the
  first time. Nothing registered moves: programme 1 is closed (ADR-0033)
  and programme 2 has registered nothing (M12.5 has not run).
- The `Fill` signature already carries what the rule needs; no record
  format changes.
- **The 112 CVX cells, looked at on implementation (2026-09-13):** a
  rounding artefact, not a fill defect. The stop was booked at the open,
  86.29, as M3.8 says; the level, restated for an action, was
  86.28999…, within 1e-14 of it, so the auditor's "price equals level"
  test fired on a fill that was at the open. The overnight-gap auditor
  now treats a fill at the open as obtainable whatever the level, which
  is the rule's own statement.

## Considered options

- **Cancel the limit when the bar opens through it, and fill nothing.**
  Rejected: a resting order at a venue with an opening auction is filled
  by the auction, not cancelled. Filling nothing would omit precisely the
  days the market opened with the worst news, which is the optimistic
  omission the auditor exists to catch.
- **Keep the level fill and exempt limit orders from the gap auditor.**
  Rejected: it measures a price no one printed. The auditor is the
  standard; the engine meets it or the kind is not measured.
- **Fix the vendored module.** Not available here: `occams/core/` is the
  donor's code at a recorded hash and is never edited in this repository;
  the donor is read-only for us, and a re-vendor waits on a change there.
  The engines own the fill signature and the restated basis, so the rule
  belongs with them anyway.
- **Leave `breakout_low` refused and remove it from the enum.** Rejected
  as the standing default, which is what refusing it forever would be: the
  kind was added by decision with its mechanism sentence (ADR-0037);
  refusing it because the engine cannot yet fill it correctly is a fact
  about the engine, recorded here, not a verdict on the mechanism.
