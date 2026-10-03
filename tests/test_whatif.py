"""``python -m occams whatif`` — the consequence surface of a config, on
paper. Fixture values are the absurd config fixture; nothing here is a
value to copy."""

from __future__ import annotations

from pathlib import Path

import pytest

from occams.config import load
from occams.whatif import derive, main, report
from tests.test_config import FIXTURE


# The shared config fixture's alpha rates are absurd enough that a four-cell
# question costs more than an axis budget, so its falsifier can never fire and
# the report refuses it — correctly. These rates are still absurd (a four-cell
# question spends most of an axis) but affordable, so the "ok" case is ok.
AFFORDABLE_AXES = {
    "regime": {"budget": 0.5, "mechanism_test_alpha": 0.1, "implementation_test_alpha": 0.05},
    "price_daily": {"budget": 0.25, "mechanism_test_alpha": 0.1, "implementation_test_alpha": 0.05},
    "cross_sectional": {"budget": 0.0, "mechanism_test_alpha": 0.0, "implementation_test_alpha": 0.0},
    "fundamental": {"budget": 0.0, "mechanism_test_alpha": 0.0, "implementation_test_alpha": 0.0},
}


def write(tmp_path: Path, name: str, **capital) -> Path:
    raw = {k: (dict(v) if isinstance(v, dict) else v) for k, v in FIXTURE.items()}
    raw["capital"] = {**FIXTURE["capital"], **capital}
    lines = []
    for sec in ("capital", "lab", "partitions"):
        lines.append(f"[{sec}]")
        lines += [f'{k} = "{v}"' if isinstance(v, str) else f"{k} = {v}" for k, v in raw[sec].items()]
    lines.append("[alpha]")
    lines += [f'{k} = "{v}"' if isinstance(v, str) else f"{k} = {v}" for k, v in FIXTURE["alpha"].items() if k != "axes"]
    for ax, body in AFFORDABLE_AXES.items():
        lines.append(f"[alpha.axes.{ax}]")
        lines += [f"{k} = {v}" for k, v in body.items()]
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n")
    return p


def test_derive_covers_every_consequence_shown_by_hand(tmp_path):
    d = derive(load(write(tmp_path, "a.toml", currency="USD")))
    for k in ("breadth", "notional", "halt_strategy_R", "false_halt_strategy", "cost_in_r_us", "fx_per_trade",
              "axes", "verdicts_affordable", "falsifier_count", "p_all_null_with_edge", "partitions", "flags", "sha"):
        assert k in d
    assert set(d["axes"]) == {"regime", "price_daily"}  # the two runnable axes only
    assert d["fx_per_trade"] == pytest.approx(0.0000206, abs=1e-6)  # USD account: no FX legs on US names


def test_flags_fire_on_a_gbp_account_with_a_small_fx_limit_and_not_on_usd(tmp_path):
    gbp = derive(load(write(tmp_path, "g.toml", currency="GBP", fx_exposure_limit=0.01)))
    assert any(f.severity == "refuse" and "would be refused at M10" in f.text for f in gbp["flags"])
    assert any("FX legs" in f.text for f in gbp["flags"])
    usd = derive(load(write(tmp_path, "u.toml", currency="USD")))
    assert not any("refused at M10" in f.text or "FX legs" in f.text for f in usd["flags"])


def test_falsifier_affordability_flag(tmp_path):
    p = write(tmp_path, "f.toml", currency="USD")
    assert not any("never fire" in f.text for f in derive(load(p))["flags"])
    p.write_text(p.read_text().replace("falsifier_count = 1", "falsifier_count = 500"))
    d = derive(load(p))
    assert any(f.severity == "refuse" and "can never fire" in f.text for f in d["flags"])


def test_the_report_prints_configs_side_by_side(tmp_path):
    a = write(tmp_path, "a.toml", currency="USD")
    b = write(tmp_path, "b.toml", currency="GBP", fx_exposure_limit=0.01)
    out = report([load(a), load(b)])
    assert "`a.toml`" in out and "`b.toml`" in out and out.count("| currency | USD | GBP |") == 1
    assert "REFUSE [b.toml]" in out and "recorded decision, not a re-run" in out


def test_cli_exit_codes(tmp_path, capsys):
    assert main([str(write(tmp_path, "ok.toml", currency="USD"))]) == 0
    assert main([str(write(tmp_path, "bad.toml", currency="GBP", fx_exposure_limit=0.01))]) == 1
    missing = tmp_path / "nope.toml"
    assert main([str(missing)]) == 2
    assert "does not load" in capsys.readouterr().out


def test_whatif_writes_nothing():
    import inspect
    from occams import whatif
    src = inspect.getsource(whatif)
    assert "write_text" not in src and ".append(" not in src.replace("flags.append(", "").replace("cfgs.append(", "").replace("lines.append(", "")
