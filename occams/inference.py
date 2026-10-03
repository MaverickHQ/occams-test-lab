"""What the guards compute from a Monte Carlo distribution, and how one is drawn, in one
place (M16.8, M16.9; ADR-0048 §4; the review's F20). A guard, the survey's readiness table
and the size table all read a p from here, and both engines draw through here, so the
three cannot drift apart and a correction is made once.

Numerics only: no engine, no Register, no bars.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

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


# ---- ADR-0048: the winner against its reference, by calendar day ------------------------------------

BLOCK_HOLDS = 2           # a block is at least this many holds of consecutive calendar days (ADR-0048 §2, §3: the size table's choice)
MIN_BLOCKS = 4            # and never so long that fewer blocks than this remain to resample
BY_DAY = "calendar-day block bootstrap, studentised"
INDEPENDENT = "independent draws: the synthetic law has no dates"


def one_sided_p(z: float) -> float:
    """P(Z >= z) for a standard normal."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


@dataclass(frozen=True)
class DayComparison:
    """The winner's EV against a reference's, with what both depend on kept together."""

    n: int                      # the winner's trades: every draw is a mean at this count
    difference: float           # the winner's EV less the reference's
    reference: float            # the reference's EV per trade
    se: float                   # the standard error of the difference, blocks of days as clusters — the bootstrap's own scale
    se_cluster: float           # clustered by date, with a Bartlett correction across dates out to the block length
    block: int                  # consecutive calendar days per block
    days: int                   # calendar days resampled
    draws: tuple[float, ...]    # reference + se·t*: each compares with the winner's EV exactly as a guard compares a null draw

    @property
    def p_cluster(self) -> float:
        return one_sided_p(self.difference / self.se_cluster) if self.se_cluster > 0 else 1.0

    def stats(self, method: str = BY_DAY) -> tuple[tuple[str, float | int | str], ...]:
        """What a Measurement carries beside the draws, for the guard's cross-check and its evidence."""
        return (("method", method), ("reference", self.reference), ("se", self.se), ("se_cluster", self.se_cluster),
                ("block", self.block), ("days", self.days))


def by_day(calendar: np.ndarray, *, days, values, weight: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """(sum of outcomes, count of trades) on each day of ``calendar`` — a sorted array of every
    calendar day of the partition, traded or not. A trade is placed by its own day, never by a
    name's bar index."""
    calendar = np.asarray(calendar)
    days = np.asarray(days)
    at = np.searchsorted(calendar, days)
    if days.size and (at.max(initial=0) >= calendar.size or not np.array_equal(calendar[np.minimum(at, calendar.size - 1)], days)):
        raise ValueError("a trade falls on a day that is not in the calendar it is compared on")
    s = np.bincount(at, weights=np.asarray(values, dtype=float), minlength=calendar.size) if days.size else np.zeros(calendar.size)
    k = np.bincount(at, minlength=calendar.size).astype(float) if days.size else np.zeros(calendar.size)
    return weight * s, weight * k


def _block_sums(x: np.ndarray, block: int) -> np.ndarray:
    """The sum over every run of ``block`` consecutive days: one entry per possible start."""
    c = np.concatenate(([0.0], np.cumsum(x)))
    return c[block:] - c[:-block]


def compare_by_day(calendar, *, winner, reference, hold: int, draws: int, seed: int, stream: int = 48) -> DayComparison:
    """The winner's EV per trade against a reference's, both measured on the same resampled days.

    ``winner`` is ``(days, outcomes)``; ``reference`` is a list of ``(days, outcomes, weight)`` whose
    weighted pool is the passive alternative — a coin's side for beats-null (half the long
    outcome of every box, half the short), the winner's own side mix for the fifth check.

    Each is summed by calendar day. The statistic is the difference of the two per-trade means,
    ``T = S_w/K_w - S_r/K_r``. Blocks of consecutive calendar days are drawn with replacement —
    the same blocks for both — and the statistic is recomputed and **studentised** by its own
    blocks-as-clusters standard error in every draw (Götze & Künsch 1996), so a draw carries
    the noise of the variance estimate as well as of the mean. Trades that share a date stay
    together; positions that overlap stay together; the reference's sampling error is in the
    difference, and so is the winner's count, which varies from draw to draw as it would.

    A block is ``BLOCK_HOLDS`` holds long, or the vendored rule's length for the daily series
    if that is longer, and never so long that fewer than ``MIN_BLOCKS`` remain.
    """
    calendar = np.asarray(calendar)
    days_n = int(calendar.size)
    sw, kw = by_day(calendar, days=winner[0], values=winner[1])
    sr, kr = np.zeros(days_n), np.zeros(days_n)
    for r_days, r_values, weight in reference:
        s, k = by_day(calendar, days=r_days, values=r_values, weight=float(weight))
        sr, kr = sr + s, kr + k
    nw, nr = float(kw.sum()), float(kr.sum())
    if nw <= 0 or nr <= 0:
        raise ValueError("nothing to compare: the winner or its reference holds no trades")
    mw, mr = float(sw.sum()) / nw, float(sr.sum()) / nr
    t_obs = mw - mr
    u = (sw - mw * kw) / nw - (sr - mr * kr) / nr                    # each day's influence on the difference
    block = max(BLOCK_HOLDS * max(int(hold), 1), block_length(u))
    block = max(1, min(block, days_n // MIN_BLOCKS)) if days_n >= MIN_BLOCKS else 1
    n_blocks = -(-days_n // block)

    # the clustered standard error: by date, Bartlett across dates out to the block length
    v = float(u @ u)
    for lag in range(1, block):
        v += 2.0 * (1.0 - lag / block) * float(u[lag:] @ u[:-lag])
    se_cluster = math.sqrt(v) if v > 0 else 0.0

    b_sw, b_kw, b_sr, b_kr = (_block_sums(x, block) for x in (sw, kw, sr, kr))
    u_blocks = (b_sw - mw * b_kw) / nw - (b_sr - mr * b_kr) / nr
    se = math.sqrt(n_blocks * float(np.mean(u_blocks * u_blocks)))
    if not se > 0:                                                    # the winner *is* its reference: nothing to resample
        return DayComparison(int(round(nw)), t_obs, mr, 0.0, se_cluster, block, days_n, tuple([mr] * int(draws)))
    rng = np.random.default_rng([int(seed), int(stream)])
    t_star = np.empty(int(draws))
    chunk = max(1, min(int(draws), 2_000_000 // n_blocks))
    for lo in range(0, int(draws), chunk):
        starts = rng.integers(0, b_sw.size, size=(min(chunk, int(draws) - lo), n_blocks))
        r_sw, r_kw, r_sr, r_kr = b_sw[starts], b_kw[starts], b_sr[starts], b_kr[starts]
        n_w, n_r = r_kw.sum(axis=1), r_kr.sum(axis=1)
        ok = (n_w > 0) & (n_r > 0)
        m_w = np.divide(r_sw.sum(axis=1), n_w, out=np.zeros_like(n_w), where=ok)
        m_r = np.divide(r_sr.sum(axis=1), n_r, out=np.zeros_like(n_r), where=ok)
        safe_w, safe_r = np.where(ok, n_w, 1.0)[:, None], np.where(ok, n_r, 1.0)[:, None]
        u_star = (r_sw - m_w[:, None] * r_kw) / safe_w - (r_sr - m_r[:, None] * r_kr) / safe_r
        v_star = (u_star * u_star).sum(axis=1)
        ok &= v_star > 0
        t = np.divide(m_w - m_r - t_obs, np.sqrt(np.where(ok, v_star, 1.0)), out=np.zeros_like(n_w), where=ok)
        # a draw with no winner trade in it, or no spread, says nothing against the winner: it is counted as reaching it
        t_star[lo:lo + t.size] = np.where(ok, t, max(t_obs / se, 0.0) + 1.0)
    return DayComparison(int(round(nw)), t_obs, mr, se, se_cluster, block, days_n, tuple(float(mr + se * x) for x in t_star))


def beside(stats, winner) -> dict:
    """What a Monte Carlo guard records beside its p (ADR-0048 §5, §6): the winner's count and
    dispersion, the reference's EV, the clustered standard error and the p it gives, the method.
    ``p_cluster`` is absent when the measurement carries no standard error to compute it from."""
    stats = dict(stats or ())
    out = {"n": winner.n, "sd": float(np.std([t.net_r for t in winner.trades])) if winner.trades else None}
    out.update({k: stats[k] for k in ("method", "reference", "se", "se_cluster", "block", "days") if k in stats})
    se, ref = stats.get("se_cluster"), stats.get("reference")
    out["p_cluster"] = one_sided_p((winner.ev - ref) / se) if se and se > 0 and ref is not None else None
    return out


def guard_p(p_monte_carlo: float, stats, winner) -> float:
    """The p a Monte Carlo guard acts on: it passes only when the bootstrap and the clustered
    standard error both say so, which is the larger of their two p-values. What the size table measures."""
    p_cluster = beside(stats, winner)["p_cluster"]
    return 1.0 if p_cluster is None else max(p_monte_carlo, p_cluster)
