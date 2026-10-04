"""M16.16 (ADR-0051, ADR-0050 §3 and §4; the review's F07 and F06).

**The plateau.** The neighbourhood's median included the winner, which with four cells is
one of the two middle values and pulls the median toward itself; and the slack was 0.10 R
for every question, whatever the winner's own sampling error. The median is now the
neighbours', and a registration declares a slack in the winner's standard errors as well.

**Power.** A question planned at one cell's dispersion while any cell of its sweep could
win: Q2-001 planned at 2.22 R on its hold-5 cell and won at hold 20, where its ungated
sibling measures 4.09 R. A survey registration now plans on its widest cell, and at
measurement a winner too dispersed for its count is refused on the question's own formula."""

from __future__ import annotations

from dataclasses import replace

import pytest

from occams.config import InformationAxis
from occams.engine import synthetic
from occams.guards import measure as measure_guard
from occams.guards import plateau
from occams.guards import register as register_guard
from occams.hypothesis import Confirmation, Gates, Hypothesis, HypothesisState, PowerPlan, Tier
from occams.measurement import Cell, Floor, Measurement, Trade
from tests.test_forward_refusals import measure


def _surface(scores: dict[tuple[int, int], float], *, se: float | None = None) -> Measurement:
    """A 2 × 2 sweep with the given EV in each cell and no baseline: the surface is EV."""
    cells = tuple(Cell(idx, (("stop", float(idx[0])), ("hold", float(idx[1]))), tuple(Trade(ev, g, i) for i, g in enumerate("ABC" * 4)))
                  for idx, ev in scores.items())
    stats = () if se is None else (("sd", 0.0), ("se_cluster", se), ("n_eff", 12.0))
    return Measurement(spec_hash="s", engine="t", engine_sha="e", seed=1, partition="measurement", years=1.0, cells=cells, null_ev=(),
                       winner_stats=stats)


FOUR = {(0, 0): 0.30, (0, 1): 0.22, (1, 0): 0.18, (1, 1): 0.05}


def test_plateau_excludes_winner_from_median():
    """The review's figures: 0.30, 0.22, 0.18, 0.05 with a slack of 0.10. With the winner in it the median is 0.20 and
    the gap exactly 0.10, which is not over the slack: it passed. The neighbours' median is 0.18 and the gap 0.12."""
    m = _surface(FOUR)
    r, seen = plateau.evaluate(m, Gates(4, 0.10, 0.5))
    assert r is not None and r.reason.startswith("plateau: lone spike")
    assert seen["neighbourhood_median"] == pytest.approx(0.18) and seen["gap"] == pytest.approx(0.12) and seen["neighbourhood"] == 4
    assert plateau.check(m, Gates(4, 0.13, 0.5)) is None                 # the size is still counted with the winner in it


def test_plateau_slack_in_standard_errors():
    """A gap of 0.05 R is inside an absolute slack of 0.10 and five of the winner's standard errors of 0.01."""
    m = _surface({(0, 0): 0.30, (0, 1): 0.25, (1, 0): 0.25, (1, 1): 0.25}, se=0.01)
    assert plateau.check(m, Gates(4, 0.10, 0.5)) is None                 # a question registered before ADR-0051: the half is absent
    seen = plateau.evaluate(m, Gates(4, 0.10, 0.5))[1]
    assert seen["gap_se"] == pytest.approx(5.0) and "plateau_slack_se" not in seen     # recorded as evidence, not judged
    r, seen = plateau.evaluate(m, Gates(4, 0.10, 0.5, plateau_slack_se=2.0))
    assert r is not None and r.reason == ("plateau: lone spike — the winner exceeds its neighbours' median by more than plateau_slack_se "
                                          "of its own standard errors (ADR-0051)")
    assert seen["gap_se"] == pytest.approx(5.0) and seen["plateau_slack_se"] == 2.0
    assert plateau.check(m, Gates(4, 0.10, 0.5, plateau_slack_se=6.0)) is None
    # the two slacks together can only refuse more: a gap inside the standard-error slack and over the absolute one is refused
    assert plateau.check(m, Gates(4, 0.04, 0.5, plateau_slack_se=6.0)) is not None


def test_a_declared_slack_with_no_standard_error_to_read_is_refused_by_name():
    m = _surface({(0, 0): 0.30, (0, 1): 0.25, (1, 0): 0.25, (1, 1): 0.25})
    r = plateau.check(m, Gates(4, 0.10, 0.5, plateau_slack_se=2.0))
    assert r is not None and "carries no standard error for the winner's score" in r.reason


def test_on_the_margin_surface_the_standard_error_is_the_margins():
    m = measure(synthetic.flat(0.35))
    seen = plateau.evaluate(m, Gates(4, 0.10, 0.5, plateau_slack_se=50.0))[1]
    assert m.surface == "margin" and seen["se_score"] == pytest.approx(dict(m.baseline_stats)["se_cluster"])


def _draft(gates: Gates) -> Hypothesis:
    return Hypothesis(id="H", tier=Tier.MECHANISM, axis=InformationAxis.PRICE_DAILY, mechanism="m", if_true="t", if_false="f",
                      falsifier="x", floor=Floor(0.15, 50), power_plan=PowerPlan(1.2, 0.05, 0.8, 1000), gates=gates,
                      search_space_size=9, capability=True)


def test_a_new_registration_declares_its_slack_in_standard_errors():
    """ADR-0051 §2: it has no default. A registration without it is refused by name; one read back from before the
    rule carries none, and for it the half is absent."""
    me = Confirmation("apparatus", False)
    r = register_guard.check(_draft(Gates(4, 0.10, 0.5)), confirmation=me, parent=None)
    assert r is not None and "plateau_slack_se" in r.reason and "no default" in r.reason
    assert register_guard.check(_draft(Gates(4, 0.10, 0.5, plateau_slack_se=3.0)), confirmation=me, parent=None) is None
    r = register_guard.check(_draft(Gates(4, 0.10, 0.5, plateau_slack_se=0.0)), confirmation=me, parent=None)
    assert r is not None and "positive" in r.reason
    assert Gates(**{"plateau_cells": 4, "plateau_slack": 0.1, "loo_min_fraction": 0.5}).plateau_slack_se is None   # an older queue record


def _registered(plan: PowerPlan, k: int = 1) -> Hypothesis:
    return replace(_draft(Gates(1, 10.0, 0.5, plateau_slack_se=50.0)), power_plan=plan, search_space_size=k, state=HypothesisState.REGISTERED,
                   floor=Floor(0.10, 5))


def test_measure_refuses_when_winner_sigma_exceeds_plan():
    """The review's figures: a plan at 1.0 R needing about a thousand trades, and a winner of 1,100 trades whose own
    dispersion is 2.0 R. The count the plan asked for is there; the power it promised is not."""
    plan = PowerPlan(1.0, 0.05, 0.8, 1100)
    h = _registered(plan)
    need = h.required_n
    m = synthetic.measure(spec_hash="s", seed=3, axes={"stop": [1.0]}, groups=list("ABCDE"), years=10, trades_per_group_year=22,
                          sigma_r=2.0, cost_in_r=0.0, effect=synthetic.flat(0.3), null_draws=100)
    stats = dict(m.winner_stats)
    assert m.winner.n == 1100 >= need and 1.9 < stats["sd"] < 2.1
    r = measure_guard.check(h, m)
    assert r is not None and r.reason == "underpowered at the winning cell's own dispersion (ADR-0050)"
    assert r.evidence["required_n_at_winner_sd"] > 3.5 * need and r.evidence["n_eff"] == pytest.approx(stats["n_eff"])
    calm = synthetic.measure(spec_hash="s", seed=3, axes={"stop": [1.0]}, groups=list("ABCDE"), years=10, trades_per_group_year=22,
                             sigma_r=0.9, cost_in_r=0.0, effect=synthetic.flat(0.3), null_draws=100)
    assert measure_guard.check(h, calm) is None


def test_a_winner_whose_trades_cluster_is_counted_at_its_effective_count():
    """ADR-0050 §4: the winner's *effective* count. Trades that share their dates are fewer observations than trades."""
    plan = PowerPlan(1.0, 0.05, 0.8, 1100)
    h = _registered(plan)
    m = synthetic.measure(spec_hash="s", seed=3, axes={"stop": [1.0]}, groups=list("ABCDE"), years=10, trades_per_group_year=22,
                          sigma_r=0.9, cost_in_r=0.0, effect=synthetic.flat(0.3), null_draws=100)
    stats = dict(m.winner_stats)
    clustered = replace(m, winner_stats=tuple({**stats, "n_eff": 200.0}.items()))
    r = measure_guard.check(h, clustered)
    assert r is not None and "own dispersion" in r.reason and r.evidence["n"] == 1100 and r.evidence["n_eff"] == 200.0


def test_registration_sigma_is_the_widest_cell():
    """ADR-0050 §3 (the review's F06): a question registered from a survey planned on the chosen cell's dispersion while
    any cell of its sweep could win. It plans on the widest cell of the family, and says which."""
    from occams.survey.candidates import widest_sigma

    row = {"cell": "aaaa", "sigma_net": 1.5, "trades": 400, "hold": 5.0, "stop": 2.0}
    kin = [row, {"cell": "bbbb", "sigma_net": 3.0, "trades": 300, "hold": 20.0, "stop": 2.0},
           {"cell": "cccc", "sigma_net": 9.0, "trades": 50, "hold": 20.0, "stop": 5.0, "refused": "overnight gap"},
           {"cell": "dddd", "sigma_net": None, "trades": 1, "hold": 1.0, "stop": 2.0}]
    sigma, wide = widest_sigma(row, kin)
    assert sigma == 3.0 and wide["cell"] == "bbbb"                       # the refused cell and the cell with no dispersion are not candidates
    assert widest_sigma(row, [row]) == (1.5, row) and widest_sigma(row, []) == (1.5, row)


def test_a_survey_registration_plans_on_the_widest_cell_and_names_it(tmp_path, capsys):
    import json

    import tests.test_survey_candidates as fixture
    from occams.ledger.alpha_budget import AlphaBudget
    from occams.question import main as question_main
    from occams.survey.candidates import candidates
    from occams.whatif import config_sha

    a, cfg, cfg_path, reg, reg_path, grid, grid_path, out = fixture.survey(tmp_path)
    index = json.loads((out / "survey.json").read_text())
    top = candidates(index, grid, budget=AlphaBudget(cfg, reg, config_sha=config_sha(cfg)))[0]
    kin = [r for r in index["cells"] if not r.get("refused") and r.get("sigma_net") and r["universe"] == top["row"]["universe"]
           and r["regime"] == top["row"]["regime"] and r["kind"] == top["row"]["kind"] and r["params"] == top["row"]["params"]
           and bool(r["target"]) == bool(top["row"]["target"]) and r["stop_kind"] == top["row"]["stop_kind"]]
    widest = max(kin, key=lambda r: r["sigma_net"])
    assert len(kin) > 1
    cid = top["cell"]
    common = ["--from-survey", str(out), "--grid", str(grid_path), "--archive", str(tmp_path / "archive"), "--register", str(reg_path),
              "--config", str(cfg_path), "--floor-ev", "0.15", "--floor-frequency", "1", "--seed", "3",
              "--id-prefix", "Q2-"]
    assert question_main(["prepare", *common, "--ids", cid, "--plateau-slack-se", "50"]) in (0, 1)
    text = capsys.readouterr().out
    assert f"σ {widest['sigma_net']:.4f}" in text and "the family's widest cell" in text and widest["cell"] in text
    # and without the slack in standard errors nothing is registrable: the key is named, no value suggested
    assert question_main(["prepare", *common, "--ids", cid]) == 1
    assert "plateau_slack_se" in capsys.readouterr().out
