"""M1.7 — the loader refuses on each missing field individually, holds S8,
accepts only all-zero allocations on a non-runnable axis, and carries no
default. Fixture values below are deliberately absurd (risk per trade equal
to capital) so that nothing here can be read as a recommendation (R9)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from occams import config
from occams.config import ConfigRefused, InformationAxis, load, parse

FIXTURE = {
    "capital": {  # absurd on purpose: risk per trade is half the capital; nothing here is a value to copy
        "starting": 4.0, "max_drawdown_per_strategy": 4.0,
        "max_drawdown_portfolio": 4.0, "risk_per_trade": 2.0,
        "currency": "XXX", "fx_exposure_limit": 1.0,
        "forward_window_min_size": 1.0,
    },
    "alpha": {
        "total": 1.0, "reserve": 0.25, "correction": "bonferroni",
        "axes": {
            "regime": {"budget": 0.5, "mechanism_test_alpha": 0.5, "implementation_test_alpha": 0.25},
            "price_daily": {"budget": 0.25, "mechanism_test_alpha": 0.5, "implementation_test_alpha": 0.25},
            "cross_sectional": {"budget": 0.0, "mechanism_test_alpha": 0.0, "implementation_test_alpha": 0.0},
            "fundamental": {"budget": 0.0, "mechanism_test_alpha": 0.0, "implementation_test_alpha": 0.0},
        },
    },
    "lab": {"falsifier_count": 1, "falsifier_outcome": "null", "overlap_threshold": 1.0},
    "partitions": {"definition": 0.25, "measurement": 0.5, "reserve": 0.25},
}


def _fx():
    return copy.deepcopy(FIXTURE)


def test_the_fixture_is_accepted():
    cfg = parse(_fx(), Path("fixture"))
    assert cfg.capital.currency == "XXX"
    assert cfg.alpha.axes[InformationAxis.REGIME].runnable
    assert not cfg.alpha.axes[InformationAxis.FUNDAMENTAL].runnable
    assert cfg.lab.falsifier_count == 1


def _paths():
    out = []
    for k in FIXTURE["capital"]:
        out.append(("capital", k))
    for k in ("total", "reserve", "correction"):
        out.append(("alpha", k))
    for ax in FIXTURE["alpha"]["axes"]:
        for k in FIXTURE["alpha"]["axes"][ax]:
            out.append(("alpha.axes." + ax, k))
    for k in FIXTURE["lab"]:
        out.append(("lab", k))
    for k in FIXTURE["partitions"]:
        out.append(("partitions", k))
    return out


@pytest.mark.parametrize("section,key", _paths(), ids=[f"{s}.{k}" for s, k in _paths()])
def test_each_missing_field_is_refused_individually(section, key):
    raw = _fx()
    node = raw
    for part in section.split("."):
        node = node[part]
    del node[key]
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert any(f"[{section}].{key} missing" == r for r in e.value.reasons), e.value.reasons


@pytest.mark.parametrize("section", ["capital", "alpha", "lab", "partitions"])
def test_each_missing_section_is_refused(section):
    raw = _fx()
    del raw[section]
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert f"[{section}] missing" in e.value.reasons


def test_s8_invariant_holds_on_load():
    raw = _fx()
    raw["alpha"]["reserve"] = 0.3  # 0.5 + 0.25 + 0.3 != 1.0
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert any(r.startswith("S8:") for r in e.value.reasons)


def test_non_runnable_axis_accepts_only_all_zero_allocations():
    raw = _fx()
    raw["alpha"]["axes"]["cross_sectional"]["mechanism_test_alpha"] = 0.5
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert any("cross_sectional" in r and "ADR-0017" in r for r in e.value.reasons)


def test_runnable_axis_needs_implementation_below_mechanism_and_above_zero():
    raw = _fx()
    raw["alpha"]["axes"]["regime"]["implementation_test_alpha"] = 0.5  # == mechanism
    with pytest.raises(ConfigRefused):
        parse(raw, Path("fixture"))
    raw = _fx()
    raw["alpha"]["axes"]["regime"]["implementation_test_alpha"] = 0.0
    with pytest.raises(ConfigRefused):
        parse(raw, Path("fixture"))


def test_free_text_axis_is_refused():
    raw = _fx()
    raw["alpha"]["axes"]["technical"] = {"budget": 0.0, "mechanism_test_alpha": 0.0, "implementation_test_alpha": 0.0}
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert any("closed-enum" in r for r in e.value.reasons)


def test_unknown_keys_and_sections_are_refused():
    raw = _fx()
    raw["capital"]["leverage"] = 1.0
    raw["venue"] = {"name": "x"}
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert "[capital].leverage is not a known field" in e.value.reasons
    assert "[venue] is not a known section" in e.value.reasons


def test_refusal_lists_every_defect_not_the_first():
    raw = _fx()
    del raw["capital"]["starting"]
    del raw["lab"]["falsifier_count"]
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert len(e.value.reasons) >= 2


def test_amounts_typed_as_fractions_are_caught_by_shape():
    raw = _fx()
    raw["capital"]["risk_per_trade"] = raw["capital"]["starting"]  # a fraction of 1.0 typed where an amount belongs
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert any("amounts, not fractions" in r for r in e.value.reasons)


def test_alpha_is_a_probability_not_money():
    raw = _fx()
    raw["alpha"]["total"] = 10000.0
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert any("probability in (0, 1]" in r for r in e.value.reasons)


def test_partitions_are_three_and_sum_to_one_and_a_fourth_is_refused():
    raw = _fx()
    raw["partitions"]["reserve"] = 0.3
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert any("sum to exactly 1" in r for r in e.value.reasons)
    raw = _fx()
    raw["partitions"]["forward"] = 0.1  # the forward window is wall-clock time, not a split (ADR-0031)
    with pytest.raises(ConfigRefused) as e:
        parse(raw, Path("fixture"))
    assert "[partitions].forward is not a known field" in e.value.reasons


def test_a_missing_file_is_a_refusal_not_a_default(tmp_path):
    with pytest.raises(ConfigRefused):
        load(tmp_path / "nope.toml")


def test_bad_toml_is_a_refusal(tmp_path):
    p = tmp_path / "occams.toml"
    p.write_text("[capital\nstarting = ")
    with pytest.raises(ConfigRefused):
        load(p)


def test_a_toml_file_round_trips(tmp_path):
    p = tmp_path / "occams.toml"
    lines = []
    for sec, body in (("capital", FIXTURE["capital"]), ("alpha", {k: v for k, v in FIXTURE["alpha"].items() if k != "axes"}), ("lab", FIXTURE["lab"]), ("partitions", FIXTURE["partitions"])):
        lines.append(f"[{sec}]")
        lines += [f'{k} = "{v}"' if isinstance(v, str) else f"{k} = {v}" for k, v in body.items()]
    for ax, body in FIXTURE["alpha"]["axes"].items():
        lines.append(f"[alpha.axes.{ax}]")
        lines += [f"{k} = {v}" for k, v in body.items()]
    p.write_text("\n".join(lines) + "\n")
    cfg = load(p)
    assert cfg.path == p and cfg.alpha.total == 1.0


def test_the_module_carries_no_default_values():
    """R9 by inspection: the only numeric literals the loader may hold are the
    zero a non-runnable axis must carry and the one a falsifier count starts
    at. Anything else is a default, and a default is a recommendation."""
    import ast
    src = (Path(config.__file__)).read_text()
    nums = sorted({n.value for n in ast.walk(ast.parse(src))
                   if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                   and not isinstance(n.value, bool)})
    assert set(nums) <= {0, 1, 3, 1e-12}, nums  # 3 = ISO code length, 1e-12 = S8 tolerance; 1 = a probability's ceiling


def test_schema_prints_keys_and_no_values():
    s = config.schema()
    for k in FIXTURE["capital"]:
        assert k in s
    assert "<float>" in s and "= 1" not in s and "= 0." not in s
