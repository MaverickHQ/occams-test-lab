"""The synthetic outcome engine — apparatus for the controls (ADR-0029).

It does not simulate bars. It draws per-trade outcomes in net R from a
declared law: ``net_r = effect(cell, group) - cost_in_r + sigma_r * z``,
with ``effect`` zero for random entry and a planted size for the positive
control. Cells of the sweep are independent draws of that law, so at M2 the
plateau check tests the composition of the five refusals, not parameter
sensitivity — the day-boxed engine supplies the real surface at M3.

Every number it needs is passed in; it holds no constants of its own.
"""

from __future__ import annotations

from itertools import product
from typing import Callable

import numpy as np

from occams.measurement import Cell, Measurement, Trade

NAME = "synthetic"

Effect = Callable[[tuple[int, ...], str], float]


def flat(size: float) -> Effect:
    """The same planted effect everywhere: a plateau by construction."""
    return lambda cell, group: size


def spike(size: float, at: tuple[int, ...]) -> Effect:
    """The effect in exactly one cell — what the plateau rule must refuse."""
    return lambda cell, group: size if tuple(cell) == tuple(at) else 0.0


def carried_by(size: float, group_name: str, n_groups: int) -> Effect:
    """All of the effect in one group, scaled so the pool still shows it —
    what leave-one-out must refuse."""
    return lambda cell, group: size * n_groups if group == group_name else 0.0


def engine_sha() -> str:
    from occams.core.archive import engine_sha as _sha

    return _sha()


def measure(*, spec_hash: str, seed: int, axes: dict[str, list[float]], groups: list[str],
            years: float, trades_per_group_year: float, sigma_r: float, cost_in_r: float,
            effect: Effect, null_draws: int, partition: str = "measurement") -> Measurement:
    rng = np.random.default_rng(seed)
    names = list(axes)
    n_per_group = int(round(years * trades_per_group_year))
    days = int(round(years * 252))
    cells = []
    for idx in product(*(range(len(axes[a])) for a in names)):
        params = tuple((a, float(axes[a][i])) for a, i in zip(names, idx))
        trades = []
        by_group = []
        for g in groups:
            z = rng.standard_normal(n_per_group)
            when = rng.integers(0, days, size=n_per_group)
            e = effect(idx, g) - cost_in_r
            trades.extend(Trade(float(e + sigma_r * zi), g, int(d)) for zi, d in zip(z, when))
            # ADR-0045: always-long at the same geometry under the law is its expectation — no effect, the spread paid —
            # per group; the law has no bars to probe, and the fifth check's Monte Carlo below carries the sampling noise
            by_group.append((g, float(-cost_in_r), n_per_group))
        base_ev = float(-cost_in_r)
        cells.append(Cell(tuple(idx), params, tuple(trades), baseline_ev=base_ev, baseline_by_group=tuple(by_group)))
    n_total = n_per_group * len(groups)
    # random entry under the same costs and geometry: the mean of n_total
    # draws of (-cost + sigma * z), null_draws times
    null = (-cost_in_r + sigma_r * rng.standard_normal((null_draws, n_total)).mean(axis=1))
    # ADR-0043: always-long at the same geometry — under a driftless law it is the null's own distribution, drawn again
    baseline = (-cost_in_r + sigma_r * rng.standard_normal((null_draws, n_total)).mean(axis=1))
    return Measurement(spec_hash=spec_hash, engine=NAME, engine_sha=engine_sha(), seed=seed,
                       partition=partition, years=float(years), cells=tuple(cells),
                       null_ev=tuple(float(x) for x in null), baseline_ev=tuple(float(x) for x in baseline))
