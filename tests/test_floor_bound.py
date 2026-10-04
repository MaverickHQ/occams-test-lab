"""M16.21 (ADR-0050 §1, §2, §5; the review's F05) — the floor is cleared by a lower confidence
bound, and power is planned against a declared alternative.

The floor was cleared by the winner's point estimate. The winner is the best of k cells, so
its estimate is biased upward, and an effect sitting exactly at the floor passed about half
the time. The power plan sized N to tell the floor from *zero*: nothing was sized to show an
EV *above* the floor. This is the one fix that changes what *supported* means."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from occams import inference
from occams.config import InformationAxis
from occams.guards import clears_floor, forward
from occams.guards import register as register_guard
from occams.hypothesis import Confirmation, Gates, Hypothesis, PowerPlan, Tier
from occams.measurement import Cell, Floor, Measurement, Trade


def _one_cell(values, days, *, se: float | None = None, years: float = 1.0) -> Measurement:
    trades = tuple(Trade(float(v), "ABC"[i % 3], int(d)) for i, (v, d) in enumerate(zip(values, days, strict=True)))
    if se is None:
        cal = np.arange(min(days), max(days) + 1)
        _m, se, _b = inference.mean_by_day(cal, days=list(days), values=list(values), hold=1)
    sd = float(np.std(values))
    stats = (("sd", sd), ("se_cluster", se), ("n_eff", min(len(values), (sd / se) ** 2) if se else float(len(values))))
    return Measurement(spec_hash="s", engine="t", engine_sha="e", seed=1, partition="measurement", years=years,
                       cells=(Cell((0,), (("stop", 1.0),), trades),), null_ev=(), winner_stats=stats)


def _exactly(mean: float, sd: float, n: int, seed: int = 4) -> np.ndarray:
    z = np.random.default_rng(seed).standard_normal(n)
    return mean + sd * (z - z.mean()) / z.std()


PLAN = PowerPlan(1.2, 0.01, 0.8, 1000, alternative_ev_net_r=0.25)      # declared after ADR-0050
BEFORE = PowerPlan(1.2, 0.01, 0.8, 1000)                                # registered before it: no alternative


def test_floor_refuses_when_lcb_below_floor():
    """The review's figures: EV 0.16 over a thousand trades at 1.2 R, a floor of 0.15, a corrected alpha of 0.01.
    The point estimate is over the floor and passed. The bound is 0.16 − 2.326 × 0.038 = 0.072."""
    m = _one_cell(_exactly(0.16, 1.2, 1000), range(1000))
    assert m.winner.ev == pytest.approx(0.16)
    r, seen = clears_floor.evaluate(m, Floor(0.15, 50), PLAN, 1)
    assert r is not None and r.reason == "floor: the lower confidence bound on EV is below the declared floor (ADR-0050)"
    assert seen["lcb_ev_net_r"] == pytest.approx(0.072, abs=0.004) and seen["rule"] == "lower confidence bound"
    assert seen["se_cluster"] == pytest.approx(1.2 / np.sqrt(1000), rel=0.05) and seen["alpha_corrected"] == 0.01
    strong = _one_cell(_exactly(0.30, 1.2, 1000), range(1000))
    assert clears_floor.check(strong, Floor(0.15, 50), PLAN, 1) is None          # 0.30 − 0.088 = 0.212
    # a sweep of nine cells: the bound is at alpha / 9, simultaneous over the cells, so it holds after choosing the winner
    r9, seen9 = clears_floor.evaluate(strong, Floor(0.15, 50), replace(PLAN, alpha=0.09), 9)
    assert seen9["alpha_corrected"] == pytest.approx(0.01) and seen9["lcb_ev_net_r"] == pytest.approx(seen["lcb_ev_net_r"] + 0.14, abs=0.01)


def test_a_question_registered_before_the_rule_is_judged_as_it_was_and_its_bound_recorded():
    """ADR-0050 §6: never backwards. A question with no declared alternative clears its floor by its point estimate,
    as it was registered to, and the bound is written beside it as a statistic."""
    m = _one_cell(_exactly(0.16, 1.2, 1000), range(1000))
    r, seen = clears_floor.evaluate(m, Floor(0.15, 50), BEFORE, 1)
    assert r is None and seen["rule"] == "point estimate (registered before ADR-0050)" and seen["lcb_ev_net_r"] == pytest.approx(0.072, abs=0.004)
    assert clears_floor.check(m, Floor(0.15, 50)) is None                         # and with no plan at all, the old signature
    # the re-score asks for the bound against the recorded floor (ADR-0047)
    r, seen = clears_floor.evaluate(m, Floor(0.15, 50), BEFORE, 1, bound=True)
    assert r is not None and "lower confidence bound" in r.reason


def test_floor_lcb_widens_under_date_clustering():
    """The same thousand values, once on a thousand dates and once packed ten to a date with each date's trades alike:
    the second's standard error is the dates', more than twice the first's, and only the first clears."""
    per_date = _exactly(0.27, 1.2, 100, seed=5)
    values = np.repeat(per_date, 10)
    spread = _one_cell(np.random.default_rng(6).permutation(values), range(1000))
    packed = _one_cell(values, np.repeat(np.arange(100), 10))
    assert spread.winner.ev == pytest.approx(packed.winner.ev)
    se_spread, se_packed = dict(spread.winner_stats)["se_cluster"], dict(packed.winner_stats)["se_cluster"]
    assert se_packed > 2.0 * se_spread
    assert clears_floor.check(spread, Floor(0.15, 50), PLAN, 1) is None
    assert clears_floor.check(packed, Floor(0.15, 50), PLAN, 1) is not None


def test_a_bound_with_no_standard_error_to_read_is_refused_by_name():
    m = replace(_one_cell(_exactly(0.5, 1.2, 1000), range(1000)), winner_stats=())
    r = clears_floor.check(m, Floor(0.15, 50), PLAN, 1)
    assert r is not None and "carries no standard error for the winner's EV" in r.reason


def test_the_frequency_half_of_the_floor_is_unchanged():
    m = _one_cell(_exactly(0.5, 1.2, 1000), range(1000), years=100.0)             # ten trades a year
    r = clears_floor.check(m, Floor(0.15, 50), PLAN, 1)
    assert r is not None and "frequency" in r.reason


def test_required_n_targets_the_alternative():
    """One-sided, against the gap between the alternative and the floor: ((z(0.99) + z(0.80)) × 1.2 / 0.10)² = 1,446 —
    the review's figure. Before the rule it was sized to tell the floor from nil: 714 at four cells, the M0.15 answer."""
    assert PLAN.required_n(Floor(0.15, 50), 1) == 1446
    assert replace(PLAN, sigma_r=2.22).required_n(Floor(0.15, 50), 1) == 4947
    assert replace(PLAN, alternative_ev_net_r=0.20).required_n(Floor(0.15, 50), 1) == 5781
    assert PowerPlan(1.2, 0.05, 0.8, 1000).required_n(Floor(0.15, 50), 4) == 714              # no alternative: the rule before
    assert inference.z(0.99) == pytest.approx(2.3263, abs=1e-4) and inference.one_sided_n(1.2, 0.10, alpha=0.01, power=0.8) == 1446


def _draft(plan: PowerPlan) -> Hypothesis:
    return Hypothesis(id="H", tier=Tier.MECHANISM, axis=InformationAxis.PRICE_DAILY, mechanism="m", if_true="t", if_false="f",
                      falsifier="x", floor=Floor(0.15, 50), power_plan=plan, gates=Gates(4, 0.10, 0.5, 50.0),
                      search_space_size=9, capability=True)


def test_alternative_has_no_default():
    """A registration that does not declare the EV it wants power at is refused, naming the key and no value; so is one
    whose alternative is not above its floor."""
    me = Confirmation("apparatus", False)
    r = register_guard.check(_draft(BEFORE), confirmation=me, parent=None)
    assert r is not None and "alternative_ev_net_r" in r.reason and "no default" in r.reason and not any(ch.isdigit() for ch in r.reason.split("(")[0])
    for not_above in (0.15, 0.10):
        r = register_guard.check(_draft(replace(PLAN, alternative_ev_net_r=not_above)), confirmation=me, parent=None)
        assert r is not None and "strictly above the floor" in r.reason
    assert register_guard.check(_draft(PLAN), confirmation=me, parent=None) is None
    assert PowerPlan(**{"sigma_r": 1.2, "alpha": 0.05, "power": 0.8, "available_n": 10}).alternative_ev_net_r is None   # an older queue record


def test_schema_prints_the_registration_keys_and_no_values():
    from occams import config

    s = config.schema()
    section = s[s.index("declared per question"):]
    for key in ("floor.ev_net_r", "floor.min_trades_per_year", "power.alternative_ev_net_r", "gates.plateau_slack_se"):
        assert key in section
    import re

    assert "<float>" in section and not re.search(r"=\s*[-+]?\d", section)          # a key and its type, never a value


def test_the_five_checks_take_the_floor_rule_from_the_question():
    from occams.engine import synthetic
    from tests.test_forward_refusals import hyp, measure

    m = measure(synthetic.flat(0.26))                                              # winner about 0.26 net of cost... over the floor by a hair
    old = hyp()
    new = replace(old, power_plan=replace(old.power_plan, alternative_ev_net_r=0.30))
    by_old = dict(zip(forward.CHECKS, forward.evaluations(m, old), strict=True))["clears_floor"]
    by_new = dict(zip(forward.CHECKS, forward.evaluations(m, new), strict=True))["clears_floor"]
    assert by_old[1]["rule"].startswith("point estimate") and by_new[1]["rule"] == "lower confidence bound"
    assert by_old[1]["lcb_ev_net_r"] == by_new[1]["lcb_ev_net_r"] < m.winner.ev
