"""M16.15 (ADR-0049; the review's F04) — the fifth check is side-matched and dependence-aware.

ADR-0043 made beating always-long the fifth check so that a supported verdict would attest
the entry, not the gate and the side. As built the baseline was always *long*, whatever
side the winner took: on a market that falls a coin flip beats it by being short half the
time, and passed. The baseline now takes the winner's own side mix, is resampled with the
winner by calendar day (ADR-0048), and the margin is recorded in its two parts."""

from __future__ import annotations

from dataclasses import replace

import pytest

from occams.calibrate import _measure
from occams.controls import _day_boxed_measurement, load_controls
from occams.engine import synthetic
from occams.guards import beats_always_long
from occams.hypothesis import PowerPlan
from tests.test_forward_refusals import measure

PLAN = PowerPlan(1.2, 0.05, 0.8, 1000)


@pytest.mark.slow
def test_the_null_controls_coin_flip_is_refused_by_the_fifth_check():
    """The review's probe A3: `make null --engine=day_boxed` printed *checks that passed: plateau,
    leave_one_out, beats_always_long* from the day the check was added."""
    cfg = load_controls()
    m = _day_boxed_measurement("null", cfg, int(cfg["day_boxed"]["seed"]), None, None, None)[1]
    r, seen = beats_always_long.evaluate(m, PowerPlan(float(cfg["day_boxed"]["sigma_r"]), 0.05, 0.8, 1000), m.search_space_size)
    assert r is not None and r.reason.startswith("beats-always-long: the passive alternative at the same geometry, gate and side mix does as well")
    assert 0.4 < seen["long_share"] < 0.6 and m.winner.baseline_rule == "side_matched"
    assert abs(seen["reference"] - dict(m.null_stats)["reference"]) < 0.02           # a coin's baseline is the coin's own expectation


@pytest.mark.slow
def test_a_coin_flip_on_a_falling_market_no_longer_beats_being_long():
    m = _measure("day_boxed:downdrift-rho0.0:coin", 3)
    stats = dict(m.baseline_stats)
    assert beats_always_long.evaluate(m, PowerPlan(1.2, 0.05, 0.8, 1000), 1)[0] is not None
    assert abs(m.winner.margin) < 0.02 and stats["reference"] == pytest.approx(m.winner.baseline_ev)   # the surface and the guard: one number


@pytest.mark.slow
@pytest.mark.parametrize("world", ["day_boxed:updrift-rho0.5", "position_boxed:martingale-rho0.0"])
def test_matched_side_equals_always_long_for_long_only(world):
    """A long-only entry's side-matched baseline is always-long, as before: the same EV per cell, per group."""
    from occams.engine import day_boxed, position_boxed

    m = _measure(world, 3)
    w = m.winner
    stats = dict(m.baseline_stats)
    assert w.long_share == 1.0 and w.baseline_rule == "side_matched" and stats["long_share"] == 1.0
    assert m.baseline_n == w.n and stats["method"] == "calendar-day block bootstrap, studentised"
    assert stats["reference"] == pytest.approx(w.baseline_ev) and stats["reference"] + stats["selection"] + stats["execution"] == pytest.approx(w.ev)
    engine = position_boxed if world.startswith("position") else day_boxed
    assert m.engine == engine.NAME


@pytest.mark.slow
def test_market_entry_execution_component_is_zero():
    """A market entry on a box *is* the passive trade on that box: the whole margin is which boxes it chose."""
    m = _measure("position_boxed:martingale-rho0.0", 3)
    stats = dict(m.baseline_stats)
    assert stats["execution"] == 0.0 and stats["selection"] == pytest.approx(m.winner.margin)


def test_guards_refuse_a_baseline_not_at_winner_n():
    m = measure(synthetic.flat(0.5))
    assert m.baseline_n == m.winner.n and beats_always_long.check(m, PLAN, 9) is None
    r, seen = beats_always_long.evaluate(replace(m, baseline_n=3 * m.winner.n), PLAN, 9)
    assert r is not None and r.reason == "beats-always-long: the baseline was not drawn at the winner's count (ADR-0048)"
    assert seen["baseline_n"] == 3 * m.winner.n and "p_baseline" not in seen


def test_the_fifth_check_refuses_when_bootstrap_and_standard_error_disagree():
    m = measure(synthetic.flat(0.5))
    wide = replace(m, baseline_stats=tuple({**dict(m.baseline_stats), "se_cluster": 10.0}.items()))
    r, seen = beats_always_long.evaluate(wide, PLAN, 9)
    assert r is not None and "the bootstrap and the clustered standard error disagree" in r.reason
    assert seen["p_baseline"] <= seen["alpha_corrected"] < seen["p_cluster"]
