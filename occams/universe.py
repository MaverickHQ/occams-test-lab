"""``python -m occams universe declare|show`` — a universe is a Register
record (M12.1): a named instrument set of the M0.7 class, its members,
the rule that chose them, when, from what source, and the bias that rule
carries. A survey cell names its universe by this record; the universe's
calendar is frozen under its name (``calendar freeze --universe``).

    python -m occams universe declare --register PATH --name NAME --members A,B,C
                                      --rule TEXT --bias TEXT --chosen-on YYYY-MM-DD
                                      [--class us_large] [--source tiingo-starter] [--notes TEXT]
                                      [--archive DIR]      # refuse a member the archive does not hold
    python -m occams universe show --register PATH [--name NAME]

A universe is never edited: a changed membership is a new record under a
new name, or the same name with a note saying what it supersedes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="python -m occams universe")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("declare")
    d.add_argument("--register", required=True, type=Path)
    d.add_argument("--name", required=True)
    d.add_argument("--members", required=True, help="comma-separated symbols")
    d.add_argument("--rule", required=True, help="the rule that chose the members, in words")
    d.add_argument("--bias", required=True, help="the bias the rule carries, named")
    d.add_argument("--chosen-on", required=True, help="YYYY-MM-DD the rule was applied")
    d.add_argument("--class", dest="instrument_class", default="us_large")
    d.add_argument("--source", default="tiingo-starter")
    d.add_argument("--notes", default="")
    d.add_argument("--archive", default=None, type=Path, help="if given, every member must already be archived")
    s = sub.add_parser("show")
    s.add_argument("--register", required=True, type=Path)
    s.add_argument("--name", default=None)
    a = ap.parse_args(argv)

    from occams.data.partitions import declared_universe
    from occams.register import Register

    reg = Register(a.register)
    if a.cmd == "show":
        recs = [r for r in reg.records() if r["type"] == "UniverseDeclared" and (a.name is None or r["name"] == a.name)]
        if not recs:
            print("no universe declared" + (f" under {a.name!r}" if a.name else "") + " in this Register")
            return 1
        for r in recs:
            print(_describe(r))
        return 0

    members = tuple(dict.fromkeys(m.strip().upper() for m in a.members.split(",") if m.strip()))
    if len(members) < 3:
        print(f"REFUSED: a universe needs at least three members for leave-one-out to be possible (ADR-0012); got {len(members)}")
        return 1
    if declared_universe(reg, a.name) is not None and "supersedes" not in a.notes.lower():
        print(f"REFUSED: universe {a.name!r} is already declared in this Register; a changed membership is a new name, "
              f"or the same name with a note saying what it supersedes")
        return 1
    if a.archive is not None:
        from occams.data.archive import BarArchive

        held = {e["name"] for e in BarArchive(a.archive).entries()}
        missing = [m for m in members if m not in held]
        if missing:
            print(f"REFUSED: members not in the archive: {missing}; ingest them first")
            return 1
    from occams.data.rights import REGISTRY

    if a.source not in REGISTRY:
        print(f"REFUSED: source {a.source!r} has no rights record (F18.7)")
        return 1
    reg.append(reg.UniverseDeclared(a.name, members, a.instrument_class, a.source, a.rule, a.chosen_on, a.bias, a.notes))
    print("DECLARED " + _describe(declared_universe(reg, a.name)))
    return 0


def _describe(r: dict) -> str:
    return (f"{r['name']} · {len(r['members'])} names: {', '.join(r['members'])} · {r['instrument_class']} · {r['source_id']} · "
            f"chosen {r['chosen_on']} · rule: {r['rule']} · bias: {r['bias']}" + (f" · {r['notes']}" if r.get("notes") else ""))


if __name__ == "__main__":
    sys.exit(main())
