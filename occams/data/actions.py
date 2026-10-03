"""Corporate actions as their own dated series (D9, F18.1). Prices stay
as-printed; the action explains the move. A move explained by an action is
not a gap and does not fire a stop.

``day`` is the ordinal of the first bar printed on the new basis — the
ex-date. A split with ratio 2.0 means one old share became two: the price
printed on ``day`` is half the prior close's basis. Delisting ``terms`` is
the price at which a position in the name closes (M4.3); no vendor supplies
it (M0.4), so it is a fixture or a declared convention with provenance.
"""

from __future__ import annotations

import enum
from bisect import bisect_right
from dataclasses import dataclass


class ActionKind(enum.Enum):
    SPLIT = "split"
    DIVIDEND = "dividend"
    DELISTING = "delisting"


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    name: str
    day: int
    ratio: float | None = None    # SPLIT: new shares per old share
    amount: float | None = None   # DIVIDEND: cash per share, in instrument currency
    terms: float | None = None    # DELISTING: closing price per share
    provenance: str = ""

    def __post_init__(self):
        if not isinstance(self.kind, ActionKind):
            raise TypeError("kind is a closed enum")
        if self.kind is ActionKind.SPLIT and not (self.ratio and self.ratio > 0):
            raise ValueError("a split needs a positive ratio")
        if self.kind is ActionKind.DIVIDEND and (self.amount is None or self.amount < 0):
            raise ValueError("a dividend needs a non-negative amount")
        if self.kind is ActionKind.DELISTING and (self.terms is None or self.terms < 0):
            raise ValueError("a delisting needs recorded terms — a price, possibly zero")


@dataclass(frozen=True)
class ActionSeries:
    actions: tuple[Action, ...] = ()

    def for_name(self, name: str) -> tuple[Action, ...]:
        return self._index().get(name, ((), None))[0]

    def on_day(self, name: str, day: int) -> tuple[Action, ...]:
        return tuple(a for a in self.for_name(name) if a.day == day)

    def _index(self) -> dict:
        """Per name, that name's actions in series order — exactly the
        actions a scan of the whole series would visit for that name, in the
        same order, so every product and sum below is bit-identical to the
        scan — with their days for bisection when they are non-decreasing.
        Built once, lazily (a survey rebases every lookback bar of every
        name against a series of thousands of actions, M12.3)."""
        idx = self.__dict__.get("_by_name")
        if idx is None:
            by: dict[str, list[Action]] = {}
            for a in self.actions:
                by.setdefault(a.name, []).append(a)
            idx = {}
            for n, acts in by.items():
                days = tuple(a.day for a in acts)
                sorted_days = all(days[i] <= days[i + 1] for i in range(len(days) - 1))
                idx[n] = (tuple(acts), days if sorted_days else None)
            object.__setattr__(self, "_by_name", idx)
        return idx

    def _window(self, name: str, from_day: int, to_day: int) -> tuple[Action, ...]:
        """The name's actions with ``from_day < day <= to_day``, in series order."""
        acts, days = self._index().get(name, ((), None))
        if not acts:
            return ()
        if days is None:
            return tuple(a for a in acts if from_day < a.day <= to_day)
        return acts[bisect_right(days, from_day):bisect_right(days, to_day)]

    def split_factor(self, name: str, from_day: int, to_day: int) -> float:
        """Cumulative split ratio for splits effective after ``from_day`` and
        on or before ``to_day``: a price printed on ``from_day`` is on
        ``to_day``'s basis once divided by this."""
        f = 1.0
        for a in self._window(name, from_day, to_day):
            if a.kind is ActionKind.SPLIT:
                f *= a.ratio
        return f

    def dividends_between(self, name: str, from_day: int, to_day: int) -> float:
        return sum(a.amount for a in self._window(name, from_day, to_day) if a.kind is ActionKind.DIVIDEND)

    def delisting(self, name: str) -> Action | None:
        for a in self.for_name(name):
            if a.kind is ActionKind.DELISTING:
                return a
        return None


def rebase(price: float, *, name: str, from_day: int, to_day: int, series: ActionSeries) -> float:
    """A price printed on ``from_day``, expressed on ``to_day``'s basis."""
    return price / series.split_factor(name, from_day, to_day) - series.dividends_between(name, from_day, to_day)


def explained_move(prev_close: float, *, name: str, prev_day: int, day: int, series: ActionSeries) -> float:
    """The prior close restated on this bar's basis. A gap is measured from
    here, never from the printed prior close."""
    return rebase(prev_close, name=name, from_day=prev_day, to_day=day, series=series)


def stop_fires(*, long: bool, stop_level: float, name: str, stop_day: int, day: int,
               bar_open: float, bar_low: float, bar_high: float, series: ActionSeries) -> bool:
    """Does a stop set on ``stop_day``'s basis fire on ``day``'s bar? The
    level is restated first, so the print of a split is not a breach."""
    level = rebase(stop_level, name=name, from_day=stop_day, to_day=day, series=series)
    if long:
        return bar_open <= level or bar_low <= level
    return bar_open >= level or bar_high >= level
