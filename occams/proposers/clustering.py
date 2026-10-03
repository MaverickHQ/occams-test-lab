"""Index-level vs per-instrument is a declared parameter; the resulting
intra-cluster correlation is measured, never asserted (F11, M7.7). The
power plan consumes the measurement: ``available_n`` becomes the effective
N under the vendored design-effect correction.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import fmean
from typing import Iterable

from occams.core import power as _power
from occams.proposers.regime import ClusterLevel


@dataclass(frozen=True)
class ClusterMeasurement:
    rho: float
    cluster_size: float
    n_clusters: int
    n: int
    level: ClusterLevel
    provenance: str

    def __post_init__(self):
        if not str(self.provenance).strip():
            raise ValueError("a cluster measurement carries its provenance")
        if self.n_clusters < 2:
            raise ValueError("fewer than two clusters cannot measure a correlation")
        if not (-1.0 <= self.rho <= 1.0):
            raise ValueError("rho is a correlation")

    @property
    def effective_n(self) -> int:
        return _power.effective_n(self.n, cluster_size=max(1, int(round(self.cluster_size))), intra_r=max(0.0, self.rho))


def measure_clustering(trades: Iterable, *, level: ClusterLevel, provenance: str) -> ClusterMeasurement:
    """ICC(1) by one-way ANOVA over same-day clusters of net R. Clipped at
    zero: negative within-day correlation is not a design effect."""
    by_day: dict[int, list[float]] = defaultdict(list)
    for t in trades:
        by_day[t.day].append(t.net_r)
    groups = [v for v in by_day.values() if len(v) >= 1]
    n = sum(len(g) for g in groups)
    k = len(groups)
    if k < 2 or n < 3:
        raise ValueError("not enough clusters to measure")
    grand = fmean(x for g in groups for x in g)
    ssb = sum(len(g) * (fmean(g) - grand) ** 2 for g in groups)
    ssw = sum((x - fmean(g)) ** 2 for g in groups for x in g)
    msb = ssb / (k - 1)
    dfw = n - k
    msw = ssw / dfw if dfw > 0 else 0.0
    k0 = (n - sum(len(g) ** 2 for g in groups) / n) / (k - 1)
    rho = (msb - msw) / (msb + (k0 - 1) * msw) if (msb + (k0 - 1) * msw) > 0 else 0.0
    return ClusterMeasurement(max(0.0, min(1.0, rho)), n / k, k, n, level, provenance)
