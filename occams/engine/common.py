"""What both simulators share and neither owns (M16.9; the review's F20): a bar restated
on another bar's basis, and the cost of one trade in R. They lived in ``day_boxed`` as
private names that ``position_boxed`` imported across the module boundary."""

from __future__ import annotations

from occams.data.actions import ActionSeries, rebase
from occams.data.bars import Bars


def on_basis(bars: Bars, i: int, basis_day_index: int, actions: ActionSeries):
    """Bar ``i``'s prices restated on the basis of bar ``basis_day_index``,
    so a split inside a lookback window is an action, not a level (M4.2)."""
    f = lambda p: rebase(p, name=bars.name, from_day=bars.day[i], to_day=bars.day[basis_day_index], series=actions)  # noqa: E731
    return f(bars.open[i]), f(bars.high[i]), f(bars.low[i]), f(bars.close[i])


def cost(costs, cost_in_r: float, entry_px: float, dist: float) -> float:
    """One trade's cost in R: the equity cost model's when one is given, else the declared figure."""
    if costs is None:
        return cost_in_r
    return costs.cost_in_r(entry_price=entry_px, stop_distance=dist)
