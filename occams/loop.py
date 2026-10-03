"""``python -m occams loop`` — the registered queue runs unattended (M8.6,
ADR-0035). For each REGISTERED question: measure on the archive's
measurement partition, evaluate the five refusals, append the verdict or
the refusals, then the depth records (M12.6: the winner's era
decomposition with its missed entries, and the shrinkage from screening
for a question that came from a survey), advance. It never registers,
never touches the reserve, runs only with a declared ``--seed``, and stops
when the queue is empty or the lab's falsifier fires."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from occams import falsifier
from occams.config import Config, load
from occams.data.archive import BarArchive
from occams.guards import Refused
from occams.hypothesis import HypothesisState
from occams.question import QuestionQueue, depth_records, measure_question, resolve_question
from occams.register import Register
from occams.stopping import describe, stopping_record


@dataclass(frozen=True)
class LoopResult:
    resolved: tuple[tuple[str, str], ...]
    refused: tuple[tuple[str, str], ...]
    lab_closed: bool


def run(cfg: Config, *, register: Register, archive: BarArchive, queue: QuestionQueue, seed: int,
        null_draws: int = 4000, path_draws: int = 2000) -> LoopResult:
    from occams.spec.compile import clear_engine_sha, stamp_engine_sha

    stamp_engine_sha()      # M14.3: the tree as the loop found it, before the loop's own appends dirty it
    try:
        return _run(cfg, register=register, archive=archive, queue=queue, seed=seed, null_draws=null_draws, path_draws=path_draws)
    finally:
        clear_engine_sha()
        from occams.register.heads import repin_if_pinned

        repin_if_pinned(register.path)   # ADR-0054: a pinned store's pin moves with its appends, by this call and never by hand


def _run(cfg: Config, *, register: Register, archive: BarArchive, queue: QuestionQueue, seed: int,
         null_draws: int, path_draws: int) -> LoopResult:
    done = {r["hypothesis_id"] for r in register.records() if r["type"] == "HypothesisResolved"}
    resolved, refused = [], []
    if stopping_record(register):   # LabClosed (ADR-0033) or ProgrammeStopped (M12.8): a stopped programme measures nothing more
        return LoopResult((), (), True)
    for q in queue.questions():
        if q.id in done or q.hypothesis.state is not HypothesisState.REGISTERED:
            continue
        try:
            q2, m = measure_question(q, cfg=cfg, archive=archive, register=register, seed=seed, null_draws=null_draws)
            q3, v, _ = resolve_question(q2, m, register=register, archive=archive, seed=seed, path_draws=path_draws)
            depth_records(q3, m, cfg=cfg, archive=archive, register=register, seed=seed)   # M12.6: eras, missed, shrinkage — after the verdict
            resolved.append((q.id, v.outcome))
        except Refused as e:
            refused.append((q.id, "; ".join(r.reason for r in e.refusals)))
            continue
        if falsifier.evaluate(cfg, register).fired:
            return LoopResult(tuple(resolved), tuple(refused), True)
    return LoopResult(tuple(resolved), tuple(refused), False)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 3:
        print("usage: python -m occams loop REGISTER.jsonl ARCHIVE_DIR QUEUE.jsonl --seed N [--config PATH]")
        return 2
    if "--seed" not in argv or argv.index("--seed") + 1 >= len(argv):
        print("REFUSED: the loop runs with a declared --seed and no default (M12.6); a verdict names the seed it was drawn with")
        return 2
    seed = int(argv[argv.index("--seed") + 1])
    cfg = load(argv[argv.index("--config") + 1] if "--config" in argv else None)
    res = run(cfg, register=Register(Path(argv[0])), archive=BarArchive(Path(argv[1])), queue=QuestionQueue(Path(argv[2])),
              seed=seed)
    for hid, out in res.resolved:
        print(f"resolved {hid}: {out}")
    for hid, why in res.refused:
        print(f"refused  {hid}: {why}")
    if res.lab_closed:
        stop = stopping_record(Register(Path(argv[0])))
        if stop and stop["type"] == "ProgrammeStopped":
            print(f"THE PROGRAMME IS STOPPED (M12.8): {describe(stop)}. Nothing measures after that record.")
        else:
            print("THE LAB FALSIFIER FIRED: the lab is closed (ADR-0033).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
