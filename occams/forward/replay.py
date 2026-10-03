"""``ReplaySource`` — unseen data replayed deterministically (M9.4): bars
arrive one day at a time, and acknowledgements come from a declared fill
policy instead of a human, so a forward run can be replayed identically
twice and the runner's own logic tested without a venue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator

from occams.cards import Acknowledgement, Decision
from occams.data.bars import Bars


def _prefix(b: Bars, upto_day: int) -> Bars:
    idx = [i for i, d in enumerate(b.day) if d <= upto_day]
    pick = lambda t: tuple(t[i] for i in idx)  # noqa: E731
    return Bars(b.name, pick(b.open), pick(b.high), pick(b.low), pick(b.close), pick(b.volume), pick(b.day),
                close_at=None if b.close_at is None else pick(b.close_at))


@dataclass
class ReplaySource:
    bars_by_name: dict[str, Bars]
    fill_at: Callable[[Decision, Bars], float | None]  # the declared fill policy
    by: str = "replay"

    def days(self) -> list[int]:
        return sorted({d for b in self.bars_by_name.values() for d in b.day})

    def feed(self) -> Iterator[tuple[int, dict[str, Bars]]]:
        """Yields (day, bars known through that day) in order — never a bar
        from the future."""
        for d in self.days():
            yield d, {n: _prefix(b, d) for n, b in self.bars_by_name.items() if d in b.day}

    def acknowledge(self, decision: Decision, bars_now: Bars, at: str) -> Acknowledgement | None:
        px = self.fill_at(decision, bars_now)
        return Acknowledgement(decision.card_id, self.by, px, at)


def fill_at_open(decision: Decision, bars_now: Bars) -> float | None:
    """The declared replay policy for a market card: the box's open."""
    i = bars_now.day.index(decision.box_day)
    if decision.level is None:
        return bars_now.open[i]
    hit = bars_now.high[i] >= decision.level if decision.side.value == "long" else bars_now.low[i] <= decision.level
    return decision.level if hit else None
