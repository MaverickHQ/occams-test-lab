"""What a measurement *is* — the contract between an engine and the guards.

An engine (synthetic at M2, day-boxed at M3, position-boxed at M9) turns a
Strategy and a partition of history into a ``Measurement``: the declared
sweep as cells of trades in net R, the null distribution of the same
geometry under random entry, and the distribution of always-long at the
same geometry and gate (ADR-0043). The guards read nothing else, so the guards
cannot know which engine produced the numbers — which is the point.

Every trade carries a ``group``: the pooling unit the engine declares — the
instrument name for a universe, a calendar block for a single instrument —
so leave-one-out (ADR-0012) has something to leave out either way.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean


@dataclass(frozen=True)
class Floor:
    """The detectable floor: a pair, declared before anything runs (R3, D5)."""

    ev_net_r: float
    min_trades_per_year: float


@dataclass(frozen=True)
class Trade:
    net_r: float
    group: str
    day: int  # ordinal within the partition; instants arrive with M4 (D10)


@dataclass(frozen=True)
class Cell:
    """One point of the declared sweep — and, since ADR-0045, always-long at
    the same geometry and gate beside it: the cell's EV less always-long's
    is its *margin*, the surface the sweep optimises."""

    indices: tuple[int, ...]
    params: tuple[tuple[str, float], ...]
    trades: tuple[Trade, ...]
    spec_hash: str | None = None  # the cell's own spec (M3); the winner's is what a Verdict freezes
    baseline_ev: float | None = None                                  # always-long at this geometry and gate, net R per trade (ADR-0045)
    baseline_by_group: tuple[tuple[str, float, int], ...] = ()        # (group, always-long EV, trades) — for leave-one-out on the margin
    # ADR-0049: the passive alternative takes the cell's own side mix — "side_matched" — and for a long-only cell that is
    # always-long, as before; a cell measured before the rule reads "always_long"
    baseline_rule: str = "always_long"
    long_share: float | None = None                                   # the share of the cell's trades that are long

    @property
    def margin(self) -> float | None:
        """EV less always-long at the same geometry and gate; None when the engine supplied no baseline."""
        return None if self.baseline_ev is None or not self.trades else self.ev - self.baseline_ev

    def baseline_without(self, group: str) -> float | None:
        rest = [(ev, n) for g, ev, n in self.baseline_by_group if g != group and n > 0]
        total = sum(n for _, n in rest)
        return sum(ev * n for ev, n in rest) / total if total else None

    def margin_without(self, group: str) -> float:
        base = self.baseline_without(group)
        return self.ev_without(group) - (base if base is not None else (self.baseline_ev or 0.0))

    @property
    def n(self) -> int:
        return len(self.trades)

    @property
    def ev(self) -> float:
        return fmean(t.net_r for t in self.trades) if self.trades else float("nan")

    @property
    def groups(self) -> tuple[str, ...]:
        return tuple(sorted({t.group for t in self.trades}))

    def ev_without(self, group: str) -> float:
        rest = [t.net_r for t in self.trades if t.group != group]
        return fmean(rest) if rest else float("nan")


@dataclass(frozen=True)
class Measurement:
    spec_hash: str
    engine: str  # which engine, by name — the synthetic one says so
    engine_sha: str
    seed: int
    partition: str
    years: float  # span of the partition, so frequency has a denominator
    cells: tuple[Cell, ...]
    null_ev: tuple[float, ...]  # Monte Carlo EVs of random entry, same N, costs, geometry
    partition_bounds: tuple[int, int] | None = None   # [start_day, end_day) the bars came from (M4.6)
    split: tuple[float, float, float] | None = None   # the configured definition/measurement/reserve
    cost_basis: str = "declared"  # declared | bounded | measured (D23, M5.2) — approval needs bounded or measured
    # ADR-0043: Monte Carlo EVs of always-long at the same geometry and gate; empty is refused by the fifth check, never passed
    baseline_ev: tuple[float, ...] = ()
    engine_code_sha: str = ""             # ADR-0055: the content hash of what measured it — the import closure of the modules that measure
    # ADR-0048: the count each distribution's draws are means at — both Monte Carlo guards refuse one drawn at any other than the
    # winner's — and what was drawn beside the draws: the method, the reference's EV, the standard errors, the block, the days
    null_n: int = 0
    baseline_n: int = 0
    null_stats: tuple[tuple[str, float | int | str], ...] = ()
    baseline_stats: tuple[tuple[str, float | int | str], ...] = ()
    # ADR-0050, ADR-0051: the winner's own dispersion, the standard error of its EV clustered by date, and the count of
    # independent trades that standard error is worth
    winner_stats: tuple[tuple[str, float | int | str], ...] = ()

    @property
    def surface(self) -> str:
        """What the sweep optimises: ``margin`` over always-long when every
        cell carries a baseline (ADR-0045), else ``ev`` — the rule four
        verdicts were reached under, kept for a Measurement without one."""
        return "margin" if self.cells and all(c.baseline_ev is not None for c in self.cells) else "ev"

    def score(self, c: Cell) -> float:
        if not c.trades:
            return float("-inf")
        return c.margin if self.surface == "margin" else c.ev

    def score_without(self, c: Cell, group: str) -> float:
        return c.margin_without(group) if self.surface == "margin" else c.ev_without(group)

    @property
    def winner(self) -> Cell:
        """The cell with the largest score on the surface — the margin over
        always-long (ADR-0045), or EV when no baseline was supplied; ties go
        to the lowest indices, deterministically."""
        return max(self.cells, key=lambda c: (self.score(c), tuple(-i for i in c.indices)))

    @property
    def search_space_size(self) -> int:
        return len(self.cells)
