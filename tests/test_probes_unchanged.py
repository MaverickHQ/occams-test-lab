"""M16.9 (the review's F20) — the probes and the distributions built from them moved into
one place; nothing they compute may move with them. Each fingerprint below is a Measurement
at a fixed seed — every cell, the winner, and the null and always-long distributions by
their moments and quantiles — or the survey's readiness rows.

They were first held as digests of every number to ten significant digits, captured on the
code **before** the refactor and identical after it, on this machine and on the CI machine
twice. A third CI run, on another processor, differed in one of them: the signal control's
walk is built by a scalar loop whose last bit depends on the processor, and a digest of
numbers near nil has no tolerance for a last bit. So the same numbers are held here as
numbers, compared to one part in a hundred million.

A row of the task list that changes what a guard draws (M16.14, M16.15) changes these on
purpose: it replaces the fingerprint in the same commit and says so there.

**M16.14 (ADR-0048) replaced the null's fingerprints, and only the null's.** Every cell,
every winner, every always-long distribution and the survey's readiness rows are the numbers
they were. The null's spread is what moved: 0.0074 to 0.0131 on the day-boxed world whose
names share a market and 0.0096 to 0.0281 on the multi-day one — and within a few per cent
of what it was on the three worlds whose names are independent, where the old null was right.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "probes-unchanged.json").read_text(encoding="utf-8"))
TOLERANCE = 1e-8


def _moments(xs) -> list[float]:
    x = np.asarray(xs, dtype=float)
    return [float(len(x)), float(x.mean()), float(x.std()), *(float(q) for q in np.quantile(x, [0.0, 0.01, 0.5, 0.99, 1.0]))]


def fingerprint(m) -> dict:
    return {"winner": list(m.winner.indices),
            "cells": [[c.n, c.ev, c.baseline_ev] + [v for _g, ev, n in c.baseline_by_group for v in (ev, float(n))] for c in m.cells],
            "null": _moments(m.null_ev), "baseline": _moments(m.baseline_ev)}


def _measurement(key: str):
    world, seed = key.rsplit("@", 1)
    if world.startswith("controls:"):
        from occams.controls import _day_boxed_measurement, load_controls

        return _day_boxed_measurement(world.split(":")[1], load_controls(), int(seed), None, None, None)[1]
    from occams.calibrate import _measure

    return _measure(world, int(seed))


def _same(got, want) -> None:
    assert got["winner"] == want["winner"]
    assert len(got["cells"]) == len(want["cells"])
    for a, b in zip(got["cells"], want["cells"], strict=True):
        assert a == pytest.approx(b, abs=TOLERANCE)
    assert got["null"] == pytest.approx(want["null"], abs=TOLERANCE) and got["baseline"] == pytest.approx(want["baseline"], abs=TOLERANCE)


@pytest.mark.slow
@pytest.mark.parametrize("key", [k for k in GOLDEN if not k.startswith("survey:")])
def test_a_measurement_is_what_it_was_before_the_probes_moved(key):
    _same(fingerprint(_measurement(key)), GOLDEN[key])


def readiness_rows(tmp_path) -> list[list]:
    import tests.test_survey_candidates as fixture
    from occams.ledger.alpha_budget import AlphaBudget
    from occams.survey.candidates import candidates, fifth_check_readiness
    from occams.whatif import config_sha

    a, cfg, _cfg_path, reg, _reg_path, grid, _grid_path, out = fixture.survey(tmp_path)
    index = json.loads((out / "survey.json").read_text())
    cands = candidates(index, grid, budget=AlphaBudget(cfg, reg, config_sha=config_sha(cfg)))
    rows = fifth_check_readiness(cands, index, archive=a, register=reg, cfg=cfg, seed=7, draws=600)
    return [[r["cell"], r["fifth_check"], r["draws"], r["needed"], r["baseline_now"], r["p_baseline"], *r["eras_margin"]] for r in rows]


@pytest.mark.slow
def test_the_surveys_readiness_rows_are_what_they_were(tmp_path):
    got, want = readiness_rows(tmp_path), GOLDEN["survey:readiness@7"]
    assert len(got) == len(want)
    for a, b in zip(got, want, strict=True):
        assert a[:4] == b[:4] and a[4:] == pytest.approx(b[4:], abs=TOLERANCE)
