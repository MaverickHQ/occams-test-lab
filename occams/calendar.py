"""``python -m occams calendar freeze|show`` — the calendar every partition
is cut from (ADR-0038, amending ADR-0006).

    python -m occams calendar freeze --archive DIR --register PATH [--config occams.toml]
                                     [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                     [--reason TEXT] [--supersedes START-END]
    python -m occams calendar show   --register PATH

The partitions used to be cut from the archive's live common span, so a
later last bar moved every boundary — a slow leak of the sealed reserve
into measurement. ``freeze`` records the span once; it refuses a span
that would move a boundary the Register has already used and names the
end day that reproduces it. Bars beyond the frozen end are forward data.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path


def _day(s: str | None) -> int | None:
    return None if s is None else date.fromisoformat(s).toordinal()


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="python -m occams calendar")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--archive", required=True, type=Path)
    f.add_argument("--register", required=True, type=Path)
    f.add_argument("--config", default=None, help="the author's occams.toml; default: the working directory's")
    f.add_argument("--start", default=None, help="YYYY-MM-DD; default: the archive's first day")
    f.add_argument("--end", default=None, help="YYYY-MM-DD; default: the archive's last day")
    f.add_argument("--reason", default="")
    f.add_argument("--supersedes", default="", help="START-END of the calendar this one supersedes (day ordinals)")
    f.add_argument("--universe", default="", help="freeze the calendar of a declared universe (its members' common span)")
    sh = sub.add_parser("show")
    sh.add_argument("--register", required=True, type=Path)
    sh.add_argument("--universe", default=None, help="one universe's calendar; default: every calendar in the Register")
    a = ap.parse_args(argv)

    from occams.data.partitions import declared_universe, frozen_calendar
    from occams.register import Register

    reg = Register(a.register)
    if a.cmd == "show":
        if a.universe is not None:
            c = frozen_calendar(reg, a.universe)
            if c is None:
                print(f"no calendar is frozen for universe {a.universe!r}")
                return 1
            print(_describe(c))
            return 0
        cals = [r for r in reg.records() if r["type"] == "CalendarFrozen"]
        if not cals:
            print("no calendar is frozen in this Register")
            return 1
        for c in cals:
            print(_describe(c))
        return 0

    from occams.config import ConfigRefused, load
    from occams.data.archive import BarArchive
    from occams.data.partitions import AlreadyFrozen, Partitions, freeze_calendar
    from occams.whatif import config_sha

    try:
        cfg = load(a.config)
    except ConfigRefused as e:
        print("REFUSED: the configuration does not load.")
        for r in e.reasons:
            print(f"  - {r}")
        return 2
    latest = {n: b for n, (b, _a) in BarArchive(a.archive).latest_bars().items()}
    if a.universe:
        u = declared_universe(reg, a.universe)
        if u is None:
            print(f"REFUSED: universe {a.universe!r} is not declared in this Register; declare it first (M12.1)")
            return 1
        missing = [n for n in u["members"] if n not in latest]
        if missing:
            print(f"REFUSED: universe {a.universe!r} has members not in the archive: {missing}; ingest them first")
            return 1
        latest = {n: latest[n] for n in u["members"]}
    try:
        c = freeze_calendar(reg, latest, split=Partitions.from_config(cfg), config_sha=config_sha(cfg), reason=a.reason,
                            start=_day(a.start), end=_day(a.end), supersedes=a.supersedes, universe=a.universe)
    except (ValueError, AlreadyFrozen) as e:
        print(f"REFUSED: {e}")
        return 1
    print("FROZEN " + _describe(c))
    return 0


def _describe(c: dict) -> str:
    d = date.fromordinal
    return ((f"[{c['universe']}] " if c.get("universe") else "") +
            f"calendar {d(int(c['start_day']))} to {d(int(c['end_day']))} ({int(c['end_day']) - int(c['start_day']) + 1} days) · "
            f"definition to {d(int(c['definition_end_day']))} · measurement to {d(int(c['measurement_end_day']))} · "
            f"reserve to the end · split {tuple(c['split'])} · names {', '.join(c['names'])} · config {c['config_sha']}"
            + (f" · supersedes {c['supersedes']}" if c.get("supersedes") else "")
            + (f" · reason: {c['reason']}" if c.get("reason") else ""))


if __name__ == "__main__":
    sys.exit(main())
