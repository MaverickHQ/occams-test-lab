"""M16.9 (the review's F20) — the probes and the distributions built from them moved into
one place; nothing they compute may move with them. Each digest below is a Measurement at
a fixed seed — every cell, the null, the always-long distribution, the winner — or the
survey's readiness rows, captured on the code **before** the refactor and compared after.

A row of the task list that changes what a guard draws (M16.14, M16.15) changes these on
purpose: it replaces the digest in the same commit and says so there.
"""

from __future__ import annotations

import hashlib
import json

import pytest

GOLDEN = {
    "day_boxed:martingale-rho0.5@3": "9dbb09aa7d9b5e04",
    "position_boxed:martingale-rho0.5@3": "d07189098829b68c",
    "day_boxed:downdrift-rho0.0:coin@3": "bef4ba75c8d28eb6",
    "controls:null@7": "36e3b59f7fcc0836",
    "controls:signal@7": "f01a9e4e790ec859",
    "survey:readiness@7": "9e1bccd7058212e7",
}


def _f(x) -> str:
    return "None" if x is None else f"{float(x):.9e}"          # ten significant digits: the numbers, not the platform's last bit


def digest(m) -> str:
    blob = json.dumps({"null": [_f(x) for x in m.null_ev], "base": [_f(x) for x in m.baseline_ev],
                       "cells": [[list(c.indices), c.n, _f(c.ev), _f(c.baseline_ev), [[g, _f(ev), n] for g, ev, n in c.baseline_by_group]]
                                 for c in m.cells],
                       "winner": list(m.winner.indices)}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _measurement(key: str):
    world, seed = key.rsplit("@", 1)
    if world.startswith("controls:"):
        from occams.controls import _day_boxed_measurement, load_controls

        return _day_boxed_measurement(world.split(":")[1], load_controls(), int(seed), None, None, None)[1]
    from occams.calibrate import _measure

    return _measure(world, int(seed))


@pytest.mark.slow
@pytest.mark.parametrize("key", [k for k in GOLDEN if not k.startswith("survey:")])
def test_a_measurement_is_what_it_was_before_the_probes_moved(key):
    assert digest(_measurement(key)) == GOLDEN[key]


def readiness_digest(tmp_path) -> str:
    import tests.test_survey_candidates as fixture
    from occams.ledger.alpha_budget import AlphaBudget
    from occams.survey.candidates import candidates, fifth_check_readiness
    from occams.whatif import config_sha

    a, cfg, _cfg_path, reg, _reg_path, grid, _grid_path, out = fixture.survey(tmp_path)
    index = json.loads((out / "survey.json").read_text())
    cands = candidates(index, grid, budget=AlphaBudget(cfg, reg, config_sha=config_sha(cfg)))
    rows = fifth_check_readiness(cands, index, archive=a, register=reg, cfg=cfg, seed=7, draws=600)
    blob = json.dumps([[r["cell"], _f(r["baseline_now"]), r["draws"], r["needed"], r["fifth_check"], _f(r["p_baseline"]),
                        [_f(x) for x in r["eras_margin"]]] for r in rows], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


@pytest.mark.slow
def test_the_surveys_readiness_rows_are_what_they_were(tmp_path):
    assert readiness_digest(tmp_path) == GOLDEN["survey:readiness@7"]
