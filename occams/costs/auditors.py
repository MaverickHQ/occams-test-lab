"""Obtainability auditors (F4, M5.5-M5.7): could the fill the engine booked
have been obtained? Three refusals adapted to daily equities — the
overnight gap, the opening auction, the halt — each reading a ``Fill``
whose signature carries the prior close and the next open by type (M5.6),
so the gap auditor has its data or the fill cannot be constructed.

Auditors are per strategy *family*, not per venue (M5.7), and the registry
is default-deny as the donor's was: a family with no auditor fails, because
unknown families passing silently is how a verdict was once sealed on a
fill no order could produce.

The audit is exhaustive and an unobtainable fill is a missed trade
(ADR-0041): every fill the engine books is checked, ``audit`` returns one
sentence per fill — empty when obtainable — and the engine drops the trade
the sentence names and records it as ``missed``. Nothing here raises for a
fill it can name; only a family with no auditor is refused.
"""

from __future__ import annotations

from dataclasses import dataclass

from occams.data.actions import ActionSeries, explained_move
from occams.spec.spec import EntryKind, Side


@dataclass(frozen=True)
class Fill:
    price: float
    bar_index: int
    order_kind: str          # market | limit | stop
    side: Side
    level: float | None
    prior_close: float       # the last print before the bar (D9-aware: raw)
    bar_open: float
    bar_high: float
    bar_low: float
    bar_volume: float
    next_open: float | None  # None on the last bar
    name: str = ""
    prior_day: int = 0
    day: int = 0


class UnauditedFamily(ValueError):
    pass


def overnight_gap(fill: Fill, actions: ActionSeries = ActionSeries()) -> str | None:
    """A level inside an overnight gap was never traded: the only obtainable
    fill is the open or worse. The gap is measured from the prior close
    restated for any action, never from the printed prior close."""
    if fill.order_kind == "market" or fill.level is None:
        return None
    if abs(fill.price - fill.bar_open) < 1e-9:
        return None   # a fill at the open is the auction print, obtainable whatever the level (ADR-0040)
    ref = explained_move(fill.prior_close, name=fill.name, prev_day=fill.prior_day, day=fill.day, series=actions)
    lo, hi = sorted((ref, fill.bar_open))
    if lo < fill.level < hi and abs(fill.price - fill.level) < 1e-12:
        return (f"fill booked at level {fill.level} inside the overnight gap {ref} -> {fill.bar_open}; "
                f"nothing traded there — the obtainable fill is the open")
    return None


def opening_auction(fill: Fill) -> str | None:
    """A market order placed before the open fills at the auction print —
    the bar's open — not at the decision price."""
    if fill.order_kind != "market":
        return None
    if abs(fill.price - fill.bar_open) > 1e-9:
        return (f"market fill booked at {fill.price}, but the opening auction printed {fill.bar_open}; "
                f"a market order placed before the open takes the auction price")
    return None


def halt(fill: Fill) -> str | None:
    """Nothing fills in a bar that did not trade."""
    if fill.bar_volume <= 0 or (fill.bar_high == fill.bar_low == fill.bar_open):
        return f"bar {fill.bar_index} did not trade (volume {fill.bar_volume}); no fill is obtainable in a halt"
    return None


FAMILY_OF: dict[EntryKind, str] = {
    EntryKind.BREAKOUT_HIGH: "breakout", EntryKind.BREAKOUT_LOW: "breakout",
    EntryKind.CLOSE_ABOVE_MA: "trend", EntryKind.CLOSE_BELOW_MA: "trend",
    EntryKind.ALWAYS: "apparatus", EntryKind.COIN_FLIP: "apparatus",
    # ADR-0037: market entries on the next open, reversal family; the same fills a trend entry makes
    EntryKind.DOWN_RUN: "reversal", EntryKind.RETURN_BELOW: "reversal", EntryKind.PULLBACK_IN_TREND: "reversal",
}

# One set per family: the budget line M5.7 names. A new proposer adds its
# family here or its fills cannot be audited, and unaudited means refused.
FAMILY_AUDITORS: dict[str, tuple] = {
    "breakout": (overnight_gap, opening_auction, halt),
    "trend": (overnight_gap, opening_auction, halt),
    "reversal": (overnight_gap, opening_auction, halt),
    "apparatus": (opening_auction, halt),
}


def family_of(spec) -> str:
    unknown = [e.kind.value for e in spec.entries if e.kind not in FAMILY_OF]
    if unknown:   # default-deny, by name: a kind with no family cannot be audited, and unaudited means refused
        raise UnauditedFamily(f"entry kind(s) {unknown} belong to no auditor family; add them to FAMILY_OF (M5.7, ADR-0037)")
    fams = {FAMILY_OF[e.kind] for e in spec.entries}
    if len(fams) != 1:
        raise UnauditedFamily(f"a spec mixes families {sorted(fams)}; audit one family at a time")
    return fams.pop()


def _auditors(family: str) -> tuple:
    auditors = FAMILY_AUDITORS.get(family)
    if auditors is None:
        raise UnauditedFamily(f"family {family!r} has no auditors; an unaudited family cannot be measured — "
                              f"add its set to FAMILY_AUDITORS (M5.7)")
    return auditors


def check_fill(family: str, fill: Fill, actions: ActionSeries = ActionSeries()) -> str:
    """The first auditor's sentence against one fill, or "" when every auditor
    of the family passes it. Default-deny by family (M5.7)."""
    for a in _auditors(family):
        msg = a(fill, actions) if a is overnight_gap else a(fill)
        if msg:
            return f"bar {fill.bar_index} {fill.name}: {msg}"
    return ""


def audit(family: str, fills: tuple[Fill, ...], actions: ActionSeries = ActionSeries()) -> tuple[str, ...]:
    """Exhaustive (ADR-0041): one sentence per fill, "" when obtainable.
    Raises only for a family with no auditors."""
    _auditors(family)
    return tuple(check_fill(family, f, actions) for f in fills)
