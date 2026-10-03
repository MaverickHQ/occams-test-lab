"""``python -m occams question remeasure`` — a resolved question on a moving
cut of its own measurement partition (M15.9).

Roll ``k`` of ``K`` starts the window ``k`` steps into the measurement
partition and ends where the partition ends; the definition partition and
the reserve are not touched, so no bar is read that the question did not
already consume, and the reserve stays sealed (ADR-0006). Each roll runs
the question's whole sweep under the same surface and checks and appends a
``RollMeasured`` record to a *rolls* Register beside the programme's — a
stopped programme's Register is never written again (M12.8), and a roll is
a record, never a verdict. The frozen calendar is not superseded (ADR-0038):
a roll is a window inside a partition it does not move.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from occams.config import load
from occams.data.archive import BarArchive
from occams.guards import Refused, forward
from occams.question import QuestionQueue, apply_cell, measurement_world
from occams.register import Register, RollMeasured


def windows(bounds: tuple[int, int], rolls: int) -> list[tuple[int, int]]:
    lo, hi = int(bounds[0]), int(bounds[1])
    step = (hi - lo) / (rolls + 1)
    return [(lo + int(round(k * step)), hi) for k in range(1, rolls + 1)]


def remeasure(q, *, cfg, archive, register: Register, out: Register, seed: int, rolls: int, null_draws: int, log=print) -> list[dict]:
    from occams.spec.compile import clear_engine_sha, stamp_engine_sha

    resolved = [r for r in register.records() if r["type"] == "HypothesisResolved" and r["hypothesis_id"] == q.id]
    if not resolved:
        raise Refused((forward.Refusal("REGISTERED->MEASURED", f"{q.id} has no HypothesisResolved record; a roll re-measures a verdict", {}),))
    head = register.chain()[-1]["sha"]
    bounds = measurement_world(q, cfg=cfg, archive=archive, register=register)["bounds"]
    stamp_engine_sha()
    try:
        recs = []
        for k, (lo, hi) in enumerate(windows(bounds, rolls), 1):
            # the engine's measurement, as measure_question runs it — without the REGISTERED->MEASURED transition:
            # the question is resolved; a roll re-measures it and says whether the window still holds the plan's power
            w_ = measurement_world(q, cfg=cfg, archive=archive, register=register, window=(lo, hi))
            m = w_["engine"].measure(q.template, q.sweep.as_dict(), apply_cell, w_["world"], seed=seed, cost_in_r=0.0,
                                     null_draws=null_draws, partition="measurement", actions=w_["actions"], partition_bounds=w_["bounds"],
                                     split=w_["parts"].as_tuple(), costs=w_["costs"], regime=w_["regime"])
            fired = forward.check(m, q.hypothesis) or ()
            w = m.winner
            powered = int(w.n) >= int(q.hypothesis.required_n)
            rec = RollMeasured(q.id, k, rolls, lo, hi, int(bounds[0]), int(bounds[1]), int(w.n), powered, w.spec_hash, float(w.ev),
                               None if w.margin is None else float(w.margin), tuple(sorted({r.reason.split(":")[0] for r in fired})),
                               m.surface, seed, Path(register.path).name, head, m.engine_sha)
            out.append(rec)
            recs.append(rec)
            log(f"roll {k}/{rolls} · days [{lo}, {hi}) · n {w.n} ({'powered' if powered else 'under the plan'}) · EV {w.ev:+.3f} · "
                f"margin {('—' if w.margin is None else f'{w.margin:+.3f}')} · "
                f"{'passes every check' if not fired else 'refused by ' + ', '.join(sorted({r.reason.split(':')[0] for r in fired}))}")
        return recs
    finally:
        clear_engine_sha()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m occams question remeasure",
                                 description="a resolved question re-measured on a rolling cut of its measurement partition; records, never verdicts")
    ap.add_argument("--question", required=True)
    ap.add_argument("--register", required=True, type=Path, help="the programme's Register the question is resolved in (read only)")
    ap.add_argument("--queue", required=True, type=Path)
    ap.add_argument("--archive", required=True, type=Path)
    ap.add_argument("--config", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--rolls", type=int, required=True)
    ap.add_argument("--out", required=True, type=Path, help="the rolls Register the records go to — never the programme's")
    ap.add_argument("--null-draws", type=int, default=4000)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.out.resolve() == a.register.resolve():
        print("REFUSED: --out is the programme's Register; a roll is recorded beside it, never in it (M12.8)")
        return 1
    if a.rolls < 1:
        print("REFUSED: --rolls must be at least 1")
        return 1
    qs = [q for q in QuestionQueue(a.queue).questions() if q.id == a.question]
    if not qs:
        print(f"REFUSED: {a.question} is not in {a.queue}")
        return 1
    reg = Register(a.register)
    n_before = len(reg.records())
    try:
        recs = remeasure(qs[-1], cfg=load(a.config), archive=BarArchive(a.archive), register=reg, out=Register(a.out),
                         seed=a.seed, rolls=a.rolls, null_draws=a.null_draws)
    except Refused as e:
        for r in e.refusals:
            print(f"REFUSED: {r.reason}")
        return 1
    assert len(reg.records()) == n_before, "the programme's Register was written by a roll"
    print(f"{len(recs)} roll(s) of {a.question} recorded in {a.out}; the programme's Register untouched; a roll is not a verdict")
    return 0
