"""M16.14 (ADR-0048; the review's F01 and F02) — the null is drawn at the winner's count, by
calendar date.

The review's two fixes — resample the random-entry pool at the winner's count, and in date
clusters shaped like the winner's — were measured and are ADR-0048's rejected options. What
is built: the winner and its reference are summed by calendar day and the same resampled
blocks of days are used for both, so trades that share a date stay together, positions that
overlap stay together, and the reference's own sampling error is in the comparison. The
size of the result is `tests/test_apparatus_size.py`'s to judge; these are its parts."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from occams import inference
from occams.calibrate import _measure
from occams.engine import synthetic
from occams.guards import beats_null
from occams.hypothesis import PowerPlan
from tests.test_forward_refusals import measure

PLAN = PowerPlan(1.2, 0.05, 0.8, 1000)


@pytest.mark.slow
@pytest.mark.parametrize("world", ["position_boxed:martingale-rho0.0", "day_boxed:martingale-rho0.5"])
def test_null_is_drawn_at_winner_n(world):
    """F01: the multi-day engine resampled its random-entry pool to the pool's own length, about three times the winner's."""
    m = _measure(world, 3)
    stats = dict(m.null_stats)
    assert m.null_n == m.winner.n > 0
    assert stats["method"] == "calendar-day block bootstrap, studentised" and stats["block"] >= (10 if "position" in world else 2)
    assert stats["se_cluster"] > 0 and stats["days"] == 1260
    assert abs(stats["reference"]) < 0.05                       # a coin's side on a martingale: nil, by symmetry


def test_guards_refuse_a_null_not_at_winner_n():
    m = measure(synthetic.flat(0.5))
    assert m.null_n == m.winner.n and beats_null.check(m, PLAN, 9) is None
    for wrong in (2 * m.winner.n, 0):
        r, seen = beats_null.evaluate(replace(m, null_n=wrong), PLAN, 9)
        assert r is not None and r.reason == "beats-null: the null was not drawn at the winner's count (ADR-0048)"
        assert seen["null_n"] == wrong and seen["n"] == m.winner.n and "p_null" not in seen


def _days(n: int) -> np.ndarray:
    return np.arange(1000, 1000 + n)


def test_trades_are_placed_by_calendar_day_not_bar_index():
    """F02: the multi-day engine ordered its blocks by each name's own bar index. Two names whose
    histories start a hundred days apart share a calendar, not an index."""
    calendar = _days(300)
    s, k = inference.by_day(calendar, days=[1000, 1100, 1100, 1299], values=[1.0, 2.0, 3.0, 4.0])
    assert s.shape == k.shape == (300,) and s.sum() == 10.0 and k.sum() == 4
    assert (s[0], k[0]) == (1.0, 1) and (s[100], k[100]) == (5.0, 2) and (s[299], k[299]) == (4.0, 1)
    with pytest.raises(ValueError, match="calendar"):
        inference.by_day(calendar, days=[999], values=[1.0])


def test_same_date_trades_are_resampled_together():
    """Ten trades a day that all carry the day's shock: two thousand trades, two hundred observations.
    The standard error is the days', three times the one independent trades would give."""
    rng = np.random.default_rng(5)
    n_days, per_day = 200, 10
    shock = rng.standard_normal(n_days)
    calendar = _days(n_days)
    days = np.repeat(calendar, per_day)
    cmp = inference.compare_by_day(calendar, winner=(days, np.repeat(shock, per_day)),
                                   reference=[(days, np.zeros(n_days * per_day), 1.0)], hold=1, draws=2000, seed=1)
    by_days, by_trades = shock.std() / np.sqrt(n_days), shock.std() / np.sqrt(n_days * per_day)
    assert cmp.n == 2000 and cmp.days == 200 and cmp.reference == 0.0 and cmp.difference == pytest.approx(shock.mean())
    assert 0.8 * by_days < cmp.se_cluster < 1.25 * by_days and cmp.se_cluster > 2.5 * by_trades
    spread = np.std(np.asarray(cmp.draws) - cmp.reference)
    assert 0.8 * by_days < spread < 1.3 * by_days and len(cmp.draws) == 2000


def test_the_references_own_sampling_error_is_in_the_comparison():
    """A reference measured on the same days as the winner moves with it: when the two share the
    day's shock the difference is far steadier than either, and the comparison knows it."""
    rng = np.random.default_rng(6)
    n_days = 400
    shock, own = rng.standard_normal(n_days), 0.1 * rng.standard_normal(n_days)
    calendar = _days(n_days)
    paired = inference.compare_by_day(calendar, winner=(calendar, shock + own), reference=[(calendar, shock, 1.0)], hold=1, draws=1000, seed=2)
    alone = inference.compare_by_day(calendar, winner=(calendar, shock + own), reference=[(calendar, np.zeros(n_days), 1.0)], hold=1,
                                     draws=1000, seed=2)
    assert paired.se_cluster < 0.2 * alone.se_cluster


def test_overlapping_positions_widen_the_standard_error():
    """Positions entered on neighbouring days hold the same days: a block shorter than the hold
    would cut exactly the dependence that matters, so a block is never shorter than the hold."""
    rng = np.random.default_rng(7)
    n_days, hold = 600, 5
    daily = rng.standard_normal(n_days + hold)
    held = np.array([daily[d:d + hold].sum() for d in range(n_days)])          # one position a day, each holding five days
    calendar = _days(n_days)
    cmp = inference.compare_by_day(calendar, winner=(calendar, held), reference=[(calendar, np.zeros(n_days), 1.0)], hold=hold,
                                   draws=1000, seed=3)
    independent = held.std() / np.sqrt(n_days)
    assert cmp.block >= 2 * hold and cmp.se_cluster > 1.6 * independent


def test_the_guard_refuses_when_bootstrap_and_standard_error_disagree():
    """ADR-0048 §5: two answers to one question. A verdict does not rest on the one that agrees."""
    m = measure(synthetic.flat(0.5))
    stats = dict(m.null_stats)
    assert beats_null.evaluate(m, PLAN, 9)[1]["p_cluster"] < 0.05 / 9
    wide = replace(m, null_stats=tuple({**stats, "se_cluster": 10.0}.items()))
    r, seen = beats_null.evaluate(wide, PLAN, 9)
    assert r is not None and r.reason == "beats-null: the bootstrap and the clustered standard error disagree at the corrected alpha (ADR-0048)"
    assert seen["p_null"] <= seen["alpha_corrected"] < seen["p_cluster"]
    bare = replace(m, null_stats=())
    r, _ = beats_null.evaluate(bare, PLAN, 9)
    assert r is not None and "carries no clustered standard error" in r.reason


def test_the_synthetic_engine_keeps_an_independent_null_and_says_so():
    m = measure(synthetic.flat(0.35))
    stats = dict(m.null_stats)
    assert stats["method"] == "independent draws: the synthetic law has no dates" and m.null_n == m.winner.n
    assert stats["se_cluster"] == pytest.approx(1.2 / np.sqrt(m.winner.n)) and stats["reference"] == pytest.approx(-0.05)
