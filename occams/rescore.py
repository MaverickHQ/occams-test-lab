"""The diagnostic re-score (M16.18; ADR-0047; the review's T02, T22, T23)::

    python -m occams rescore --archive archive --programme REGISTER QUEUE CONFIG [--programme …] [--question ID] [--null-draws N]

Three programmes are stopped by record and their verdicts are sealed. The rules that judged
them were then found looser than they claimed and were corrected, forward only. What the
corrected rules would have said of each question is written here — **beside the record,
never in its place**: one ``Rescored`` record per question in ``register/diagnostics.jsonl``,
a hash-chained store that is not a Register.

In order, for each question a programme resolved or refused at measurement:

1. **Reproduce first** (ADR-0047 §4). The question is measured again in the code of the
   commit its record stamps — from that commit's snapshot in the private archive, verified
   against ``SOURCES.toml`` — and the result is compared with the record: the winner's spec
   hash, its EV in net R, its count, the checks that refused it. A question that is not
   recreated exactly is recorded ``reproduced=False`` with the reason and is **not**
   re-scored: a correction to a number nobody can recreate corrects nothing.
2. **Then re-score**, with this code, the stamped seed and the same bars, under the rule set
   the record names in full. Every number of every check is written, passing or failing.
3. **Judge only what the question declared** (§7). The floor's lower confidence bound needs
   no new number and is judged against the recorded floor. A slack in standard errors and
   an alternative to plan power against were never declared; they are reported, not judged.

Nothing here is a verdict. No programme Register is opened for writing; a scratch copy is
what the measurement reads. The falsifier's count and every alpha balance are what they were.
"""

from __future__ import annotations

import argparse
import math
import shutil
import sys
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

from occams import identity, sources
from occams.register import Diagnostics, Register, Rescored

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "register" / "diagnostics.jsonl"
RULES = ("ADR-0043", "ADR-0045", "ADR-0048", "ADR-0049", "ADR-0050", "ADR-0051", "ADR-0055")
NOT_JUDGED = ("plateau_slack_se — the question declared no slack in standard errors; the gap in standard errors is in the plateau's "
              "evidence (ADR-0051 §4)",
              "alternative_ev_net_r — the question declared no alternative to plan its power against; the count its own formula "
              "requires at the winner's dispersion is in at_measurement (ADR-0050 §6)")
AT_MEASUREMENT = "REGISTERED->MEASURED"
TOLERANCE = 1e-9


@dataclass(frozen=True)
class Programme:
    register: Path
    queue: Path
    config: Path


def clean(x):
    """Evidence as the chain can hold it: plain lists and dicts, and ``None`` where a guard held a not-a-number."""
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if hasattr(x, "item") and not isinstance(x, (str, bytes)):          # a numpy scalar
        return clean(x.item())
    return x


# ---- what the record says -----------------------------------------------------------------------------

def _lines(chain: list[dict], qid: str) -> dict:
    """The question's lines in its Register: its resolution, its measurement, a refusal at measurement."""
    out: dict = {}
    for line in chain:
        p = line["payload"]
        if p.get("hypothesis_id") != qid:
            continue
        if p["type"] == "HypothesisResolved":
            out["resolved"] = line
        elif p["type"] == "HypothesisMeasured":
            out["measured"] = line
        elif p["type"] == "RefusalRecorded" and p.get("transition") == AT_MEASUREMENT:
            out["refused"] = line
    return out


def recorded_of(lines: dict) -> tuple[dict, dict] | None:
    """(what the record says, the line a re-score annotates) — or None for a question the Register neither resolved nor refused."""
    if "resolved" in lines:
        r, m = lines["resolved"]["payload"], lines.get("measured", {}).get("payload", {})
        return ({"outcome": r["outcome"], "ev_net_r": r["ev_net_r"], "n": m.get("n"), "trades_per_year": r["trades_per_year"],
                 "spec_hash": r["spec_hash"], "winner_cell": list(r.get("winner_cell", ())), "refusals": list(r["refusals"]),
                 "checks": list(r.get("checks") or ()), "surface": r.get("surface", ""), "seed": r["seed"], "engine_sha": r["engine_sha"],
                 "at": r.get("at", "")}, lines["resolved"])
    if "refused" in lines:
        r = lines["refused"]["payload"]
        return ({"outcome": "refused at measurement", "reason": r["reason"], "evidence": dict(r.get("evidence") or {}), "at": r.get("at", "")},
                lines["refused"])
    return None


# ---- reproduce first ------------------------------------------------------------------------------------

def measure_at_source(*, commit: str, question: str, register: Path, queue: Path, archive: Path, config: Path, seed: int,
                      null_draws: int, names) -> dict:
    """The stamped measurement, run in the stamped commit's snapshot (M16.17). Raises ``SourceMissing`` when the snapshot
    is not here or is not the tree the manifest names, ``RuntimeError`` when the old code does not run."""
    from occams import reproduce

    with tempfile.TemporaryDirectory(prefix="occams-rescore-source-") as tmp:
        tree = sources.extract(commit, archive=archive, dest=Path(tmp) / "tree")
        return reproduce.measure_in(tree, question=question, register=register, queue=queue, archive=archive, config=config,
                                    seed=seed, null_draws=null_draws, names=names)


def _reproduction(qid: str, prog: Programme, recorded: dict, *, archive: Path, names, null_draws: int, at_source) -> dict:
    from occams.reproduce import FOUR, _refusal_heads

    commit = sources.commit_of(recorded["engine_sha"])
    try:
        got = at_source(commit=commit, question=qid, register=prog.register, queue=prog.queue, archive=archive, config=prog.config,
                        seed=int(recorded["seed"]), null_draws=null_draws, names=names)
    except (sources.SourceMissing, RuntimeError) as e:
        return {"reproduced": False, "source": commit, "reason": str(e)[-600:]}
    checks = tuple(recorded["checks"] or FOUR)
    want = sorted(_refusal_heads(recorded["refusals"], checks))
    have = sorted(_refusal_heads(got["refusals"], checks))
    differs = [k for k, same in (("spec_hash", got["spec_hash"] == recorded["spec_hash"]),
                                 ("ev_net_r", abs(float(got["ev_net_r"]) - float(recorded["ev_net_r"])) < TOLERANCE),
                                 ("n", recorded["n"] is None or int(got["n"]) == int(recorded["n"])),
                                 ("refused_by", have == want)) if not same]
    out = {"reproduced": not differs, "source": commit, "measured": {"spec_hash": got["spec_hash"], "ev_net_r": float(got["ev_net_r"]),
                                                                    "n": int(got["n"]), "refused_by": have}}
    if differs:
        out.update({"differs": differs, "reason": "the stamped source does not recreate the record's " + ", ".join(differs)})
    return out


# ---- then re-score ----------------------------------------------------------------------------------------

def rescore_question(q, *, cfg, archive, register_path: Path, names, seed: int, null_draws: int, recorded: dict) -> dict:
    """The question measured with this code on the same bars and seed, and judged under ``RULES``."""
    from occams.data.archive import BarArchive
    from occams.guards import beats_always_long, beats_null, clears_floor, forward, leave_one_out, plateau
    from occams.guards import measure as measure_guard
    from occams.hypothesis import HypothesisState
    from occams.question import apply_cell, measurement_world
    from occams.reproduce import NamesOnly

    with tempfile.TemporaryDirectory(prefix="occams-rescore-") as tmp:
        scratch = Path(tmp) / "register.jsonl"
        shutil.copy(register_path, scratch)                      # the programme's Register is read through a copy and never opened
        w = measurement_world(q, cfg=cfg, archive=NamesOnly(BarArchive(Path(archive)), names), register=Register(scratch))
        m = w["engine"].measure(q.template, q.sweep.as_dict(), apply_cell, w["world"], seed=seed, cost_in_r=0.0,
                                null_draws=null_draws, partition="measurement", actions=w["actions"], partition_bounds=w["bounds"],
                                split=w["parts"].as_tuple(), costs=w["costs"], regime=w["regime"])
    h = replace(q.hypothesis, state=HypothesisState.REGISTERED)
    k, win = h.search_space_size, m.winner
    refusal = measure_guard.check(h, m)
    at = {"passed": refusal is None, "required_n": h.required_n, "available_n": h.power_plan.available_n, "n": win.n,
          "plan_sigma_r": h.power_plan.sigma_r, **dict(m.winner_stats)}
    if refusal is not None:
        at.update({"reason": refusal.reason, "evidence": dict(refusal.evidence)})
    judged = (plateau.evaluate(m, h.gates), beats_null.evaluate(m, h.power_plan, k),
              clears_floor.evaluate(m, h.floor, h.power_plan, k, bound=True),       # the bound against the recorded floor (ADR-0050 §6)
              leave_one_out.evaluate(m, h.gates), beats_always_long.evaluate(m, h.power_plan, k))
    checks = tuple({"check": name, "passed": r is None, "judged": True, "evidence": seen} for name, (r, seen) in zip(forward.CHECKS, judged, strict=True))
    refused_by = tuple(c["check"] for c in checks if not c["passed"])
    reading = "would be refused at measurement" if refusal is not None else "would be null" if refused_by else "would be supported"
    winner = {"cell": list(win.indices), "params": dict(win.params), "spec_hash": win.spec_hash, "n": win.n, "ev_net_r": win.ev,
              "baseline_ev_net_r": win.baseline_ev, "margin_net_r": win.margin, "surface": m.surface, "long_share": win.long_share,
              "trades_per_year": win.n / m.years if m.years else None, "is_the_recorded_winner": win.spec_hash == recorded["spec_hash"],
              "cells": [{"cell": list(c.indices), "n": c.n, "ev_net_r": c.ev if c.trades else None, "margin_net_r": c.margin} for c in m.cells]}
    return clean({"winner": winner, "at_measurement": at, "checks": checks, "refused_by": refused_by, "reading": reading})


# ---- the run ------------------------------------------------------------------------------------------------

def run(programmes, *, archive: Path, out: Diagnostics, null_draws: int = 4000, only: str | None = None,
        measure_at_source=measure_at_source, log=lambda *_: None) -> list[dict]:
    """One ``Rescored`` per question not yet in ``out``; returns what was appended. Refuses dirty or unknown code first."""
    from occams.config import load
    from occams.question import QuestionQueue
    from occams.reproduce import _stamped

    commit = identity.require_clean("a re-score")               # ADR-0055: a number from code no commit holds annotates nothing
    done = {(r["register"], r["hypothesis_id"]) for r in out.records()} if Path(out.path).exists() else set()
    appended = []
    for prog in programmes:
        chain = Register(prog.register).chain()
        cfg = load(prog.config)
        for q in {q.id: q for q in QuestionQueue(prog.queue).questions()}.values():
            name = Path(prog.register).name
            if (only is not None and q.id != only) or (name, q.id) in done:
                continue
            found = recorded_of(_lines(chain, q.id))
            if found is None:
                continue
            recorded, line = found
            base = dict(hypothesis_id=q.id, register=name, annotates_seq=int(line["seq"]), annotates_sha=line["sha"], recorded=clean(recorded),
                        rules=RULES, engine_sha=commit, engine_code_sha=identity.own_code_sha(), null_draws=int(null_draws),
                        seed=int(recorded.get("seed", 0)))
            blank = dict(rescored=False, winner={}, at_measurement={}, checks=(), refused_by=(), reading="not re-scored")
            if recorded["outcome"] == "refused at measurement":
                why = ("the refusal at measurement stamps no engine commit: there is no stamped source to recreate its count from, "
                       "and a question that is not recreated is not re-scored (ADR-0047 §4)")
                rec = Rescored(**base, reproduced=False, reproduction={"reproduced": False, "reason": why}, **blank)
            else:
                _resolved, _measured, names = _stamped(Register(prog.register), q.id)
                log(f"{q.id}: reproducing at its stamped source {sources.commit_of(recorded['engine_sha'])[:12]} …")
                rep = _reproduction(q.id, prog, recorded, archive=Path(archive), names=names, null_draws=int(null_draws),
                                    at_source=measure_at_source)
                if not rep["reproduced"]:
                    rec = Rescored(**base, reproduced=False, reproduction=clean(rep), **blank)
                else:
                    log(f"{q.id}: recreated exactly; re-scoring under {', '.join(RULES)} …")
                    r = rescore_question(q, cfg=cfg, archive=archive, register_path=Path(prog.register), names=names,
                                         seed=int(recorded["seed"]), null_draws=int(null_draws), recorded=recorded)
                    rec = Rescored(**base, reproduced=True, reproduction=clean(rep), rescored=True, winner=r["winner"],
                                   at_measurement=r["at_measurement"], checks=tuple(r["checks"]), refused_by=tuple(r["refused_by"]),
                                   reading=r["reading"], not_judged=NOT_JUDGED)
            appended.append(out.append(rec)["payload"])
            log(f"{q.id}: {appended[-1]['reading']}" + ("" if appended[-1]["reproduced"] else f" — {appended[-1]['reproduction']['reason'][:160]}"))
    return appended


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m occams rescore",
                                 description="what the corrected rules would have said, beside the record and never in its place (ADR-0047)")
    ap.add_argument("--archive", required=True, type=Path, help="the private archive: the licensed bars and the source snapshots")
    ap.add_argument("--programme", nargs=3, action="append", required=True, metavar=("REGISTER", "QUEUE", "CONFIG"), type=Path)
    ap.add_argument("--question", default=None, help="one question id; default: every question not yet re-scored")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--null-draws", type=int, default=4000)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    for reg, queue, config in a.programme:
        for label, p in (("register", reg), ("queue", queue), ("config", config)):
            if not Path(p).exists():
                print(f"RE-SCORE FAILED: no {label} at {p}")
                return 2
    if not a.archive.is_dir():
        print(f"RE-SCORE FAILED: no archive at {a.archive} — the licensed bars and the stamped sources are not on this machine")
        return 2
    try:
        records = run([Programme(*p) for p in a.programme], archive=a.archive, out=Diagnostics(a.out), null_draws=a.null_draws,
                      only=a.question, log=print)
    except identity.EngineNotClean as e:
        print(f"REFUSED: {e}")
        return 2
    from occams.register import heads

    if a.out.resolve().is_relative_to(ROOT) and a.out.exists():
        heads.pin(heads.HEADS, [a.out])              # the store's pin moves with its appends (ADR-0054); the Registers' do not move
    print(f"{len(records)} record(s) appended to {a.out}; nothing here is a verdict, and no Register was written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
