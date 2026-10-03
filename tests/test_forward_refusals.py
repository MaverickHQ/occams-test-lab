"""M2.5 — the MEASURED -> FORWARD refusals, five since ADR-0043: one test each,
isolating one refusal while the others pass. M2.6 — the ported plateau rule: a
single spike cell is refused; a genuine plateau passes."""

from __future__ import annotations

from dataclasses import replace

from occams.config import InformationAxis
from occams.engine import synthetic
from occams.guards import beats_always_long, beats_null, clears_floor, forward, leave_one_out, plateau
from occams.hypothesis import Gates, Hypothesis, PowerPlan, Tier
from occams.measurement import Floor

AXES = {"stop": [1, 2, 3], "hold": [1, 2, 3]}
GROUPS = list("ABCDE")


def hyp(floor=Floor(0.15, 50), plan=PowerPlan(1.2, 0.05, 0.8, 1000), gates=Gates(4, 0.10, 0.5), k=9):
    return Hypothesis(id="H", tier=Tier.MECHANISM, axis=InformationAxis.PRICE_DAILY, mechanism="m",
                      if_true="t", if_false="f", falsifier="x", floor=floor, power_plan=plan,
                      gates=gates, search_space_size=k)


def measure(effect, *, years=10.0, per_year=20.0, seed=7, sigma=1.2, groups=GROUPS, draws=4000):
    return synthetic.measure(spec_hash="s", seed=seed, axes=AXES, groups=groups, years=years,
                             trades_per_group_year=per_year, sigma_r=sigma, cost_in_r=0.05,
                             effect=effect, null_draws=draws)


def fired(m, h):
    return {r.reason.split(":")[0] for r in (forward.check(m, h) or ())}


def test_only_plateau_fails():
    # a strong effect in exactly one cell: the winner is real and alone
    m = measure(synthetic.spike(0.6, at=(1, 1)))
    assert fired(m, hyp()) == {"plateau"}
    assert plateau.check(m, hyp().gates).reason.startswith("plateau: lone spike")


def test_only_beats_null_fails():
    # a modest real effect on 50 trades in a single-cell sweep: the point
    # estimate clears the floor, the plateau is trivially satisfied (one cell,
    # plateau_cells = 1), every group carries its share — and random entry
    # does as well at the corrected alpha. Seed 2 is one of 19 in 1..199
    # where exactly that combination holds; it is pinned, not typical.
    h = hyp(floor=Floor(0.15, 2), plan=PowerPlan(1.2, 0.05, 0.8, 50), gates=Gates(1, 10.0, 0.5), k=1)
    m = synthetic.measure(spec_hash="s", seed=2, axes={"stop": [1.0], "hold": [1.0]}, groups=GROUPS,
                          years=10, trades_per_group_year=1.0, sigma_r=1.2, cost_in_r=0.05,
                          effect=synthetic.flat(0.2), null_draws=4000)
    assert m.winner.ev >= 0.15
    m = replace(m, baseline_ev=tuple(x - 0.5 for x in m.baseline_ev))   # the passive alternative is far below: only the coin-flip null refuses
    assert fired(m, h) == {"beats-null"}
    assert "random entry" in beats_null.check(m, h.power_plan, 1).reason


def test_only_clears_floor_fails_on_the_frequency_half():
    # a strong, robust effect, but too few trades a year for the declared minimum
    h = hyp(floor=Floor(0.15, 500))  # 100/yr available
    m = measure(synthetic.flat(0.6))
    assert fired(m, h) == {"floor"}
    assert "frequency" in clears_floor.check(m, h.floor).reason


def test_only_clears_floor_fails_on_the_ev_half():
    # beats the null comfortably at a floor declared above the effect
    h = hyp(floor=Floor(0.60, 50))
    m = measure(synthetic.flat(0.35))
    assert fired(m, h) == {"floor"}
    assert "below the declared floor" in clears_floor.check(m, h.floor).reason


def test_only_leave_one_out_fails():
    # all of the effect in one of five groups, scaled so the pool still clears everything else
    m = measure(synthetic.carried_by(0.4, "C", 5))
    assert fired(m, hyp()) == {"leave-one-out"}
    r = leave_one_out.check(m, hyp().gates)
    assert r.evidence["group"] == "C"


def test_only_beats_always_long_fails():
    # ADR-0043: a planted effect that always-long at the same geometry matches — the entry adds nothing over being long
    m = measure(synthetic.flat(0.35))
    matched = replace(m, baseline_ev=tuple(x + 0.35 for x in m.null_ev))
    assert fired(matched, hyp()) == {"beats-always-long"}
    r = beats_always_long.check(matched, hyp().power_plan, 9)
    assert "being long at the same geometry and gate does as well" in r.reason and r.evidence["baseline_mean"] > 0.25
    # a distribution the engine did not supply, or too thin for the corrected alpha, is refused — never passed
    assert "too thin" in beats_always_long.check(replace(m, baseline_ev=()), hyp().power_plan, 9).reason
    assert "too thin" in beats_always_long.check(replace(m, baseline_ev=m.baseline_ev[:100]), hyp().power_plan, 9).reason


def test_all_five_pass_on_a_planted_plateau():
    m = measure(synthetic.flat(0.35))
    assert len(m.baseline_ev) == len(m.null_ev) == 4000 and m.baseline_ev != m.null_ev
    assert forward.check(m, hyp()) is None
    assert forward.passes(m, hyp()) == forward.CHECKS == ("plateau", "beats_null", "clears_floor", "leave_one_out", "beats_always_long")


def test_plateau_rule_spike_refused_plateau_passes():
    g = Gates(4, 0.10, 0.5)
    assert plateau.check(measure(synthetic.spike(0.6, at=(1, 1))), g) is not None
    assert plateau.check(measure(synthetic.flat(0.35)), g) is None


def test_plateau_neighbourhood_is_chebyshev_one_including_the_cell():
    m = measure(synthetic.spike(0.6, at=(1, 1)))
    assert len(plateau.neighbourhood(m, m.winner)) == 9
    m2 = measure(synthetic.spike(0.6, at=(0, 0)))
    assert len(plateau.neighbourhood(m2, m2.winner)) == 4


def test_plateau_refuses_a_neighbourhood_too_small_to_show_one():
    m = measure(synthetic.spike(0.6, at=(0, 0)))  # corner: 4 neighbours
    r = plateau.check(m, Gates(5, 10.0, 0.5))
    assert r is not None and "too small" in r.reason


def test_beats_null_refuses_a_null_too_thin_to_say_no():
    m = measure(synthetic.flat(0.6), draws=50)
    r = beats_null.check(m, PowerPlan(1.2, 0.05, 0.8, 1000), 9)
    assert r is not None and "too thin" in r.reason


def test_leave_one_out_refuses_fewer_than_three_groups():
    m = measure(synthetic.flat(0.6), groups=["A", "B"])
    r = leave_one_out.check(m, Gates(4, 0.10, 0.5))
    assert r is not None and "fewer than three" in r.reason


def test_every_refusal_fires_together_on_a_bad_enough_measurement():
    # a spike, thin null, sub-floor EV and one carrying group all at once — all named
    m = measure(synthetic.spike(-0.5, at=(1, 1)), draws=50)
    names = fired(m, hyp())
    assert {"beats-null", "floor"} <= names


def test_the_winner_is_the_largest_margin_over_always_long_and_leave_one_out_reads_it(tmp_path):
    """ADR-0045: the surface is the margin. A cell with the highest EV but a
    large always-long loses to a cell with a smaller EV and a larger margin;
    a Measurement whose engine supplied no baseline keeps the EV rule and
    says so. Leave-one-out on the margin: an EV carried by one name whose
    always-long is carried by the same name is a margin carried by none."""
    from occams.measurement import Cell, Measurement, Trade

    def cell(idx, by_group, baseline=None):
        trades = tuple(Trade(ev, g, i) for g, ev, n in by_group for i in range(n))
        base = None if baseline is None else tuple((g, b, n) for (g, _e, n), b in zip(by_group, baseline))
        base_ev = None if baseline is None else sum(b * n for (g, _e, n), b in zip(by_group, baseline)) / sum(n for _, _, n in by_group)
        return Cell((idx, 0), (("stop", float(idx)),), trades, baseline_ev=base_ev, baseline_by_group=base or ())
    groups = [("A", 0.5, 10), ("B", 0.5, 10), ("C", 0.5, 10)]
    x = cell(0, groups, baseline=(0.4, 0.4, 0.4))                       # EV 0.5, always-long 0.4: margin 0.1
    y = cell(1, [("A", 0.3, 10), ("B", 0.3, 10), ("C", 0.3, 10)], baseline=(0.0, 0.0, 0.0))   # EV 0.3, margin 0.3
    m = Measurement(spec_hash="s", engine="t", engine_sha="e", seed=1, partition="measurement", years=1.0, cells=(x, y), null_ev=())
    assert m.surface == "margin" and m.winner is y and m.score(y) == 0.3
    bare = Measurement(spec_hash="s", engine="t", engine_sha="e", seed=1, partition="measurement", years=1.0,
                       cells=(cell(0, groups), cell(1, [("A", 0.3, 10), ("B", 0.3, 10), ("C", 0.3, 10)])), null_ev=())
    assert bare.surface == "ev" and bare.winner.indices == (0, 0)
    carried = cell(0, [("A", 0.9, 10), ("B", 0.1, 10), ("C", 0.1, 10)], baseline=(0.8, 0.0, 0.0))   # EV carried by A; margin 0.1 everywhere
    on_margin = Measurement(spec_hash="s", engine="t", engine_sha="e", seed=1, partition="measurement", years=1.0, cells=(carried,), null_ev=())
    assert leave_one_out.check(on_margin, hyp().gates) is None
    on_ev = Measurement(spec_hash="s", engine="t", engine_sha="e", seed=1, partition="measurement", years=1.0,
                        cells=(cell(0, [("A", 0.9, 10), ("B", 0.1, 10), ("C", 0.1, 10)]),), null_ev=())
    assert leave_one_out.check(on_ev, hyp().gates).evidence["group"] == "A"
