"""``python -m occams spread`` — M5.0, the author's measurement of the spread
on the demo account, recorded as observations and summarised into the
measured spread the cost model accepts (``EquityCosts.with_measured``).

``record`` appends one reading — instrument, bid, ask, session phase, the
instant — to a local JSONL file that is gitignored (``*.local.*``): observed
quotes are market data, but where they were observed is the account's
business and stays off the record. ``summarise`` refuses until the open,
mid-session and close phases are all present, then writes the measurement
with its provenance beside the observations.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean

from occams.costs.equity import SpreadObservation, measured_spread

PHASES = ("open", "mid", "close")


def record(path: Path, *, instrument: str, bid: float, ask: float, phase: str, at: str | None = None) -> SpreadObservation:
    if phase not in PHASES:
        raise ValueError(f"phase must be one of {PHASES}")
    if not (0 < bid < ask):
        raise ValueError("a spread needs 0 < bid < ask")
    if path.name.count(".local.") == 0:
        raise ValueError("observations go in a *.local.* file, which is gitignored; where they were observed stays off the record")
    obs = SpreadObservation(instrument, at or datetime.now(timezone.utc).isoformat(timespec="seconds"), float(bid), float(ask), phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obs.__dict__, sort_keys=True) + "\n")
    return obs


def load(path: Path) -> tuple[SpreadObservation, ...]:
    if not path.exists():
        return ()
    return tuple(SpreadObservation(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def summarise(path: Path, *, provenance: str) -> dict:
    obs = load(path)
    sp = measured_spread(obs, provenance=provenance)  # refuses until open, mid and close are all present
    by_instrument = {}
    for o in obs:
        by_instrument.setdefault(o.instrument, []).append(o.fraction)
    by_phase = {p: fmean(o.fraction for o in obs if o.phase == p) for p in PHASES if any(o.phase == p for o in obs)}
    out = {"fraction": sp.fraction, "basis": sp.basis, "provenance": sp.provenance, "observations": sp.observations,
           "instruments": {k: {"mean": fmean(v), "max": max(v), "n": len(v)} for k, v in sorted(by_instrument.items())},
           "phases": by_phase, "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    path.with_suffix(".measurement.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m occams spread")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("path", type=Path)
    r.add_argument("--instrument", required=True)
    r.add_argument("--bid", required=True, type=float)
    r.add_argument("--ask", required=True, type=float)
    r.add_argument("--phase", required=True, choices=PHASES)
    s = sub.add_parser("summarise")
    s.add_argument("path", type=Path)
    s.add_argument("--provenance", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "record":
            o = record(a.path, instrument=a.instrument, bid=a.bid, ask=a.ask, phase=a.phase)
            print(f"{o.instrument} {o.phase} {o.at}: spread {o.fraction:.4%}")
            return 0
        out = summarise(a.path, provenance=a.provenance)
        print(f"measured spread {out['fraction']:.4%} over {out['observations']} observations; "
              f"phases {', '.join(f'{k} {v:.4%}' for k, v in out['phases'].items())}; "
              f"written beside the observations")
        return 0
    except ValueError as e:
        print(f"REFUSED: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
