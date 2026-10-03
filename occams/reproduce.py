"""Reproduction, which never skips (M11.5, M11.6; F14, N1)::

    python -m occams reproduce private --question ID --register R --queue Q --archive A --config C [--null-draws N] [--at-commit]
    python -m occams reproduce public [--claim-historical]

**Private** re-measures a resolved question from the licensed archive, on
a scratch copy of the Register, with the stamped seed, and compares the
winner — spec hash, EV in net R, trade count, and the outcome under the
checks the verdict was judged against — with the stamped Verdict. Exit 0
when it recreates it; 1 when it does not, saying what moved, the engine
commit first; 2 when it cannot run at all — no archive on this machine,
no such question, no config — loudly, never as a skip. ``--at-commit``
runs the measurement in a detached worktree of the commit the verdict
stamps, so an engine that has moved since is not the reason.

**Public** runs the pipeline on synthetic fixtures — the two controls on
both engines, the null refused and the planted effect accepted — and
says that is what it did. It reads the recorded source rights and refuses
an exact-historical claim when raw redistribution is not permitted.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LABEL = {"plateau": "plateau", "beats_null": "beats-null", "clears_floor": "floor", "leave_one_out": "leave-one-out",
         "beats_always_long": "beats-always-long"}
FOUR = ("plateau", "beats_null", "clears_floor", "leave_one_out")


class NamesOnly:
    """The archive seen through the names a verdict consumed (its
    ``ObservationsConsumed`` record) and the classifier's index: an archive
    that has grown since the verdict must not widen the world it is
    reproduced on. Everything else is the archive's own."""

    def __init__(self, archive, names):
        self._archive, self._names = archive, frozenset(names)

    def latest_bars(self, names=None):
        keep = self._names if names is None else self._names & frozenset(names)
        return {n: v for n, v in self._archive.latest_bars(names=keep).items() if n in self._names}

    def __getattr__(self, name):
        return getattr(self._archive, name)


def _stamped(register, qid: str) -> tuple[dict | None, dict | None, frozenset[str]]:
    """The verdict, the measurement, and the names the question consumed plus the frozen classifier's index."""
    resolved = measured = None
    names: set[str] = set()
    for r in register.records():
        if r["type"] == "ClassifierFrozen":
            names.add(str(r.get("index_name") or ""))
        if r.get("hypothesis_id") != qid:
            continue
        if r["type"] == "HypothesisResolved":
            resolved = r
        elif r["type"] == "HypothesisMeasured":
            measured = r
        elif r["type"] == "ObservationsConsumed":
            names.update(r.get("names", ()))
    return resolved, measured, frozenset(n for n in names if n)


def _refusal_heads(reasons, checks) -> set[str]:
    heads = {LABEL[c] for c in checks}
    return {str(r).split(":")[0] for r in reasons if str(r).split(":")[0] in heads}


def private(a) -> int:
    from occams.config import ConfigRefused, load
    from occams.data.archive import BarArchive
    from occams.guards import forward
    from occams.question import QuestionQueue, measure_question
    from occams.register import Register

    for label, p in (("register", a.register), ("queue", a.queue), ("config", a.config)):
        if not Path(p).exists():
            print(f"REPRODUCTION FAILED: no {label} at {p}")
            return 2
    if not Path(a.archive).is_dir():
        print(f"REPRODUCTION FAILED: no archive at {a.archive} — the licensed bars are not on this machine, so an exact private "
              f"reproduction cannot run (F14). This is a failure, not a skip.")
        return 2
    try:
        cfg = load(a.config)
    except ConfigRefused as e:
        print("REPRODUCTION FAILED: the configuration does not load: " + "; ".join(e.reasons))
        return 2
    reg = Register(Path(a.register))
    resolved, measured, names = _stamped(reg, a.question)
    if resolved is None or measured is None:
        print(f"REPRODUCTION FAILED: {a.question} has no HypothesisResolved and HypothesisMeasured in {a.register}")
        return 2
    qs = [q for q in QuestionQueue(Path(a.queue)).questions() if q.id == a.question]
    if not qs:
        print(f"REPRODUCTION FAILED: {a.question} is not in the queue {a.queue}; the registered question is what is re-measured")
        return 2
    q = qs[-1]
    stamped_commit = str(resolved.get("engine_sha", "unknown"))
    registered = [r for r in reg.records() if r["type"] == "HypothesisRegistered" and r["hypothesis_id"] == a.question]
    stamped_cfg = str(registered[-1].get("config_sha") or "") if registered else ""
    from occams.whatif import config_sha

    if stamped_cfg and config_sha(cfg) != stamped_cfg:
        print(f"NOTE: the question was registered under config {stamped_cfg}; this reproduction runs under {config_sha(cfg)} — "
              f"costs and partitions may differ, and a difference below may be the config's, not the engine's")
    if a.at_commit:
        return _at_commit(a, stamped_commit, resolved, measured, names)
    from occams.core.archive import engine_sha

    here = engine_sha()
    with tempfile.TemporaryDirectory(prefix="occams-reproduce-") as tmp:
        scratch = Path(tmp) / "register.jsonl"
        shutil.copy(a.register, scratch)                         # the Register is never written by a reproduction
        try:
            _, m = measure_question(q, cfg=cfg, archive=NamesOnly(BarArchive(Path(a.archive)), names), register=Register(scratch),
                                    seed=int(resolved["seed"]), null_draws=int(a.null_draws))
        except Exception as e:  # noqa: BLE001 — a missing name, a refused world: loud, with the reason
            print(f"REPRODUCTION FAILED: the measurement could not run: {type(e).__name__}: {e}")
            return 2
    checks = tuple(resolved.get("checks") or FOUR)
    fired = forward.check(m, q.hypothesis) or ()
    got = {"spec_hash": m.winner.spec_hash, "ev_net_r": float(m.winner.ev), "n": int(m.winner.n),
           "refused_by": sorted(_refusal_heads([r.reason for r in fired], checks))}
    want = {"spec_hash": resolved["spec_hash"], "ev_net_r": float(resolved["ev_net_r"]), "n": int(measured["n"]),
            "refused_by": sorted(_refusal_heads(resolved["refusals"], checks))}
    same = (got["spec_hash"] == want["spec_hash"] and abs(got["ev_net_r"] - want["ev_net_r"]) < 1e-9
            and got["n"] == want["n"] and got["refused_by"] == want["refused_by"])
    print(f"{a.question}: stamped on engine {stamped_commit[:12]}, re-measured on {here[:12]}, seed {resolved['seed']}, "
          f"{a.null_draws} null draws, {len(names)} names as consumed, checks {', '.join(LABEL[c] for c in checks)}")
    for k in ("spec_hash", "ev_net_r", "n", "refused_by"):
        mark = "=" if got[k] == want[k] or (k == "ev_net_r" and abs(got[k] - want[k]) < 1e-9) else "≠"
        print(f"  {k:<11} stamped {want[k]!s:<70} re-measured {got[k]!s} {mark}")
    if same:
        print(f"REPRODUCED: the stamped Verdict of {a.question} is recreated exactly from the archive (M11.5, F14).")
        return 0
    moved = "" if here.split("-")[0] == stamped_commit.split("-")[0] else \
        f" The engine has moved since the verdict ({stamped_commit[:12]} → {here[:12]}); --at-commit re-runs at the stamped commit."
    print(f"NOT REPRODUCED: the re-measurement differs from the stamped Verdict of {a.question}.{moved}")
    return 1


_CHILD = r"""
import json, sys
from pathlib import Path
from occams.config import load
from occams.data.archive import BarArchive
from occams.guards import forward
from occams.question import QuestionQueue, measure_question
from occams.register import Register
qid, reg, queue, arch, cfgp, seed, draws, names = sys.argv[1:9]
cfg = load(cfgp)
q = [x for x in QuestionQueue(Path(queue)).questions() if x.id == qid][-1]
class NamesOnly:
    def __init__(self, archive, keep): self._archive, self._keep = archive, set(keep.split(","))
    def latest_bars(self, names=None):
        keep = self._keep if names is None else self._keep & set(names)
        return {n: v for n, v in self._archive.latest_bars(names=keep).items() if n in self._keep}
    def __getattr__(self, name): return getattr(self._archive, name)
_, m = measure_question(q, cfg=cfg, archive=NamesOnly(BarArchive(Path(arch)), names), register=Register(Path(reg)), seed=int(seed), null_draws=int(draws))
fired = forward.check(m, q.hypothesis) or ()
print(json.dumps({"spec_hash": m.winner.spec_hash, "ev_net_r": float(m.winner.ev), "n": int(m.winner.n),
                  "refusals": [r.reason for r in fired]}))
"""


def _at_commit(a, stamped_commit: str, resolved: dict, measured: dict, names: frozenset[str]) -> int:
    """Measure inside a detached worktree of the stamped commit, with this
    interpreter, and compare here. The worktree is removed afterwards."""
    commit = stamped_commit.split("-")[0]
    if not commit or commit == "unknown":
        print("REPRODUCTION FAILED: the verdict stamps no engine commit to reproduce at")
        return 2
    root = Path(__file__).resolve().parent.parent
    tmp = Path(tempfile.mkdtemp(prefix="occams-worktree-"))
    try:
        wt = subprocess.run(["git", "worktree", "add", "--detach", str(tmp / "tree"), commit], cwd=root, capture_output=True, text=True)
        if wt.returncode != 0:
            print(f"REPRODUCTION FAILED: cannot check out {commit[:12]}: {wt.stderr.strip()}")
            return 2
        with tempfile.TemporaryDirectory(prefix="occams-reproduce-") as scratch_dir:
            scratch = Path(scratch_dir) / "register.jsonl"
            shutil.copy(a.register, scratch)
            child = subprocess.run([sys.executable, "-", a.question, str(scratch), str(Path(a.queue).resolve()),
                                    str(Path(a.archive).resolve()), str(Path(a.config).resolve()), str(resolved["seed"]),
                                    str(a.null_draws), ",".join(sorted(names))], input=_CHILD, cwd=tmp / "tree", capture_output=True, text=True)
        if child.returncode != 0:
            print(f"REPRODUCTION FAILED: the measurement at {commit[:12]} did not run:\n{child.stderr.strip()[-2000:]}")
            return 2
        got = json.loads(child.stdout.strip().splitlines()[-1])
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(tmp / "tree")], cwd=root, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
    checks = tuple(resolved.get("checks") or FOUR)
    want_ref = sorted(_refusal_heads(resolved["refusals"], checks))
    got_ref = sorted(_refusal_heads(got["refusals"], checks))
    same = (got["spec_hash"] == resolved["spec_hash"] and abs(got["ev_net_r"] - float(resolved["ev_net_r"])) < 1e-9
            and got["n"] == int(measured["n"]) and got_ref == want_ref)
    print(f"{a.question}: re-measured at the stamped commit {commit[:12]}, seed {resolved['seed']}, {a.null_draws} null draws")
    print(f"  spec_hash   stamped {resolved['spec_hash']}  re-measured {got['spec_hash']}")
    print(f"  ev_net_r    stamped {float(resolved['ev_net_r'])}  re-measured {got['ev_net_r']}")
    print(f"  n           stamped {measured['n']}  re-measured {got['n']}")
    print(f"  refused_by  stamped {want_ref}  re-measured {got_ref}")
    if same:
        print(f"REPRODUCED: the stamped Verdict of {a.question} is recreated exactly at its own commit (M11.5, F14).")
        return 0
    print(f"NOT REPRODUCED: the re-measurement at {commit[:12]} differs from the stamped Verdict of {a.question}.")
    return 1


def public(a) -> int:
    from occams.controls import load_controls, run
    from occams.data.rights import RightsRefused, Use, require

    try:
        require(a.source, Use.RAW_REDISTRIBUTION)
        historical_ok = True
        why = f"the recorded rights for {a.source} permit raw redistribution"
    except RightsRefused as e:
        historical_ok = False
        why = f"the recorded rights for {a.source} do not permit raw redistribution: {e}"
    except KeyError:
        historical_ok = False
        why = f"no rights record for {a.source}"
    if a.claim_historical and not historical_ok:
        print(f"REFUSED: an exact-historical claim cannot be made in public — {why} (F14, ADR-0021). "
              f"The private path reproduces the exact Verdict from the licensed archive on this machine.")
        return 1
    cfg = load_controls()
    ok = True
    with tempfile.TemporaryDirectory(prefix="occams-public-") as tmp:
        for engine in ("synthetic", "day_boxed"):
            for kind, want in (("null", False), ("signal", True)):
                o = run(kind, cfg, Path(tmp) / f"{engine}-{kind}", engine=engine)
                held = o.accepted is want
                ok = ok and held
                print(f"  {kind:<6} on {engine:<9}: {'ACCEPTED' if o.accepted else 'REFUSED'} — "
                      f"{'as the control requires' if held else 'THE CONTROL DOES NOT HOLD'}"
                      + (f" ({', '.join(r.split(':')[0] for r in o.refusals)})" if o.refusals else ""))
    print("public reproduction: the pipeline on synthetic fixtures, no vendor access, no licensed bar read — "
          "a coin flip refused and a planted effect at the floor accepted on both engines"
          + (", naming five checks" if ok else ""))
    print(f"scope: synthetic. {why}; this run makes no exact-historical claim (M11.6, F14).")
    if not ok:
        print("REPRODUCTION FAILED: a control did not hold (S3, S10) — stop and fix the guards before anything else.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="python -m occams reproduce")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("private", help="exact reproduction of a stamped Verdict from the licensed archive; fails loudly without it")
    p.add_argument("--question", required=True)
    p.add_argument("--register", required=True)
    p.add_argument("--queue", required=True)
    p.add_argument("--archive", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--null-draws", type=int, default=4000)
    p.add_argument("--at-commit", action="store_true", help="re-measure in a worktree of the commit the verdict stamps")
    u = sub.add_parser("public", help="the pipeline on synthetic fixtures; no vendor access; no exact-historical claim")
    u.add_argument("--source", default="tiingo-starter", help="the archive's source id, whose rights decide what may be claimed")
    u.add_argument("--claim-historical", action="store_true", help="ask for an exact-historical claim; refused when the rights forbid it")
    a = ap.parse_args(argv)
    return private(a) if a.cmd == "private" else public(a)


if __name__ == "__main__":
    sys.exit(main())
