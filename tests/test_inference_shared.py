"""M16.9 (the review's F20) — one inference module and shared probes: the fifth check the
survey shows before alpha moves is the guard's own, the distributions are drawn in one
place, and no engine reaches into another's private names."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from occams import inference
from occams.engine import synthetic
from occams.guards import beats_always_long, beats_null
from occams.hypothesis import PowerPlan
from tests.test_forward_refusals import measure

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.slow
def test_survey_and_guard_share_fifth_check(tmp_path, monkeypatch):
    """A spy on ``occams.inference.exceedance``: the survey's readiness, beats-always-long and
    beats-null all pass through it — the alpha, the draws needed and the p are computed once."""
    import tests.test_survey_candidates as fixture
    from occams.ledger.alpha_budget import AlphaBudget
    from occams.survey.candidates import candidates, fifth_check_readiness
    from occams.whatif import config_sha

    seen: list[tuple[int, float, float]] = []
    real = inference.exceedance

    def spy(dist, value, alpha_corrected):
        dist = tuple(dist)
        seen.append((len(dist), value, alpha_corrected))
        return real(dist, value, alpha_corrected)

    monkeypatch.setattr(inference, "exceedance", spy)
    a, cfg, _cfg_path, reg, _reg_path, grid, _grid_path, out = fixture.survey(tmp_path)
    index = json.loads((out / "survey.json").read_text())
    cands = candidates(index, grid, budget=AlphaBudget(cfg, reg, config_sha=config_sha(cfg)))
    rows = fifth_check_readiness(cands, index, archive=a, register=reg, cfg=cfg, seed=7, draws=600)
    assert rows and len(seen) == len(rows)
    assert [(n, ev, alpha) for n, ev, alpha in seen] == [(r["draws"], r["ev_net"], r["alpha_corrected"]) for r in rows]
    m, plan = measure(synthetic.flat(0.35)), PowerPlan(1.2, 0.05, 0.8, 1000)
    del seen[:]
    assert beats_always_long.evaluate(m, plan, 9)[0] is None and beats_null.evaluate(m, plan, 9)[0] is None
    assert seen == [(len(m.baseline_ev), m.winner.ev, 0.05 / 9), (len(m.null_ev), m.winner.ev, 0.05 / 9)]


def test_the_shared_test_refuses_a_thin_distribution_and_never_passes_it():
    assert inference.exceedance((0.0,) * 100, 1.0, 0.01) == ("thin", None, 2000)
    assert inference.exceedance((0.0,) * 2000, 1.0, 0.01) == ("pass", 1 / 2001, 2000)
    assert inference.exceedance((2.0,) * 2000, 1.0, 0.01) == ("refuse", 1.0, 2000)
    assert inference.draws_needed(0.05 / 9) == 3600 and beats_null.DRAWS_PER_ALPHA == beats_always_long.DRAWS_PER_ALPHA == 20


def _imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                yield node.module, alias.name, node.lineno


def test_engines_import_no_private_names_across_modules():
    """No module of the lab takes an underscore name out of an engine module: what two
    engines share lives in ``occams/engine/common.py`` and ``occams/engine/probes.py``."""
    offenders = []
    for path in sorted((ROOT / "occams").rglob("*.py")):
        if "core" in path.relative_to(ROOT / "occams").parts[:1]:
            continue
        for module, name, line in _imports(path):
            if module.startswith("occams.engine") and name.startswith("_"):
                offenders.append(f"{path.relative_to(ROOT)}:{line} takes {name} from {module}")
    assert offenders == []


def test_the_engines_and_the_survey_draw_through_the_shared_modules():
    """The distributions are built in ``occams/engine/probes.py`` from ``occams/inference.py``,
    and nowhere else: a second implementation is how the three drifted apart."""
    for rel in ("occams/engine/day_boxed.py", "occams/engine/position_boxed.py", "occams/survey/candidates.py",
                "occams/guards/beats_null.py", "occams/guards/beats_always_long.py"):
        source = (ROOT / rel).read_text(encoding="utf-8")
        assert "default_rng" not in source.replace("np.random.default_rng([int(seed), zlib.crc32", ""), rel   # the coin's own stream stays
        assert ">= w.ev" not in source and "/ len(dist)" not in source.replace("sum(dist) / len(dist)", ""), rel
    probes = (ROOT / "occams/engine/probes.py").read_text(encoding="utf-8")
    assert "inference.block_bootstrap_means" in probes and "inference.coin_sided_means" in probes and "inference.resampled_means" in probes
