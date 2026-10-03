"""What the guards compute from a Monte Carlo distribution, and how one is drawn, in one
place (M16.8, M16.9; ADR-0048 §4; the review's F20). A guard, the survey's readiness table
and the size table all read a p from here, and both engines draw through here, so the
three cannot drift apart and a correction is made once.

Numerics only: no engine, no Register, no bars.
"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np

DRAWS_PER_ALPHA = 20      # a distribution must hold at least this many expected exceedances at the corrected alpha to say no


def monte_carlo_p(draws: Iterable[float], value: float) -> float:
    """The one-sided Monte Carlo p of ``value`` against ``draws``, counted plus one:
    ``(1 + #{draw >= value}) / (1 + len(draws))``. The observed value is itself one draw
    under the hypothesis tested, so the estimate is never zero and never anti-conservative
    (Davison & Hinkley 1997, §4.2; Phipson & Smyth 2010) — `no draw reached it` says
    `at most one in draws + 1`, not `impossible`."""
    draws = tuple(draws)
    return (1 + sum(1 for x in draws if x >= value)) / (1 + len(draws))


def format_p(p: float) -> str:
    """A p for a page: four places where that shows it, scientific where four places
    would print nought. A Monte Carlo p is never zero and is never printed as zero."""
    return f"{p:.4f}" if p >= 0.00005 else f"{p:.1e}"


def draws_needed(alpha_corrected: float) -> int:
    """The fewest draws that can resolve ``alpha_corrected``: fewer cannot say no, and a
    guard that cannot say no is refused, never passed."""
    return math.ceil(DRAWS_PER_ALPHA / alpha_corrected) if alpha_corrected > 0 else 10 ** 12


def exceedance(dist: Iterable[float], value: float, alpha_corrected: float) -> tuple[str, float | None, int]:
    """(``thin`` | ``pass`` | ``refuse``, p or None, draws needed): the one test both Monte
    Carlo guards and the survey's readiness table apply. ``thin`` — too few draws to
    resolve the corrected alpha — carries no p."""
    dist = tuple(dist)
    need = draws_needed(alpha_corrected)
    if len(dist) < need:
        return "thin", None, need
    p = monte_carlo_p(dist, value)
    return ("pass" if p <= alpha_corrected else "refuse"), p, need


# ---- how a distribution is drawn -------------------------------------------------------------------

def coin_sided_means(longs: np.ndarray, shorts: np.ndarray, *, n: int, draws: int, seed: int) -> tuple[float, ...]:
    """``draws`` means of ``n`` outcomes, each a box drawn independently with replacement and
    its long or short outcome by a fair coin."""
    rng = np.random.default_rng([int(seed), 7])
    idx = rng.integers(0, longs.size, size=(draws, n))
    side = rng.random((draws, n)) < 0.5
    picked = np.where(side, longs[idx], shorts[idx])
    return tuple(float(x) for x in picked.mean(axis=1))


def resampled_means(x: np.ndarray, *, n: int, draws: int, seed: int) -> tuple[float, ...]:
    """``draws`` means of ``n`` outcomes drawn independently with replacement."""
    rng = np.random.default_rng([int(seed), 11])
    idx = rng.integers(0, x.size, size=(draws, n))
    return tuple(float(v) for v in x[idx].mean(axis=1))


def block_bootstrap_means(x: np.ndarray, *, block: int, draws: int, seed: int) -> np.ndarray:
    """Moving-block bootstrap of the mean (M9.2). Blocks of ``block``
    consecutive observations are drawn with replacement and concatenated to
    the original length, so dependence inside a block survives resampling."""
    x = np.asarray(x, dtype=float)
    n = x.size
    if n == 0:
        raise ValueError("nothing to resample")
    block = max(1, min(int(block), n))
    rng = np.random.default_rng([int(seed), 11])
    n_blocks = -(-n // block)
    starts = rng.integers(0, n - block + 1, size=(draws, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(draws, -1)[:, :n]
    return x[idx].mean(axis=1)


def block_length(x: np.ndarray) -> int:
    """The vendored rule (``stats.optimal_block_length``): grows with the
    series' serial dependence and stays within sane bounds — the donor
    pinned both properties by test."""
    from occams.core import stats

    return int(stats.optimal_block_length(np.asarray(x, dtype=float)))
