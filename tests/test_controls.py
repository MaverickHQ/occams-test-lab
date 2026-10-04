"""M2.7 / M2.7b — `make null` is REFUSED naming which refusal fired;
`make signal` is ACCEPTED naming that all five checks passed. Both through
the same pipeline, at a sample size the plan requires. S3 and S10."""
from __future__ import annotations

import pytest


from occams.controls import load_controls, main, run

CFG = load_controls()


def test_null_is_refused_naming_which_refusals_fired(tmp_path):
    o = run("null", CFG, tmp_path)
    assert o.accepted is False
    assert any(r.startswith("beats-null") for r in o.refusals)
    assert any(r.startswith("floor") for r in o.refusals)
    assert o.n >= o.required_n


def test_signal_is_accepted_naming_all_five_passes(tmp_path):
    o = run("signal", CFG, tmp_path)
    assert o.accepted is True
    assert o.passes == ("plateau", "beats_null", "clears_floor", "leave_one_out", "beats_always_long")
    assert o.n >= o.required_n


def test_the_signal_plants_at_the_apparatus_alternative_and_nowhere_else():
    """ADR-0050 §5: S10 is *a planted effect at the alternative is accepted*. The alternative is declared once, in the
    control's power plan, strictly above its floor; there is no second planted figure to drift from it."""
    floor, alternative = CFG["floor"]["ev_net_r"], CFG["power"]["alternative_ev_net_r"]
    assert floor < alternative <= 2 * floor and "signal" not in CFG
    d = CFG["day_boxed"]
    assert d["planted_return_daily"] == pytest.approx((alternative + d["cost_in_r"]) * 0.05)


def test_sample_size_is_computed_not_typed(tmp_path):
    o = run("signal", CFG, tmp_path)
    from occams import inference
    k = len(CFG["sweep"]["stop"]) * len(CFG["sweep"]["hold"])
    expect = inference.one_sided_n(CFG["power"]["sigma_r"], CFG["power"]["alternative_ev_net_r"] - CFG["floor"]["ev_net_r"],
                                   alpha=CFG["power"]["alpha"] / k, power=CFG["power"]["power"])
    assert o.required_n == expect == 732


@pytest.mark.slow
def test_boundary_sensitivity_across_seeds(tmp_path):
    """ADR-0029: the probe measures sensitivity at the boundary. The signal
    sits just above the floor, so it is not expected to pass every seed —
    but a pipeline that accepts fewer than half of them at 80 % planned
    power has drifted, and a null that ever passes is a stop."""
    seeds = range(1, 21)
    sig = sum(run("signal", CFG, tmp_path / f"s{i}", seed=i).accepted for i in seeds) / len(seeds)
    nul = sum(run("null", CFG, tmp_path / f"n{i}", seed=i).accepted for i in seeds)
    assert nul == 0
    assert sig >= 0.5, sig


def test_controls_register_at_alpha_zero(tmp_path):
    o = run("signal", CFG, tmp_path)
    from occams.register import Register
    rows = Register(tmp_path / "register.jsonl").records()
    reg = [r for r in rows if r["type"] == "HypothesisRegistered"][0]
    assert reg["alpha_spent"] == 0.0 and reg["registered_by"] == "apparatus"
    assert o.hypothesis_id == "CONTROL-SIGNAL"


def test_cli_exit_codes(tmp_path, capsys):
    assert main(["null", str(tmp_path / "n")]) == 0
    assert "REFUSED at MEASURED -> FORWARD" in capsys.readouterr().out
    assert main(["signal", str(tmp_path / "s")]) == 0
    assert "all five checks passed" in capsys.readouterr().out
