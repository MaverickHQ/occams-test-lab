"""``python -m occams refusals REGISTER`` — what was searched, what it cost,
and why each thing died (N6). Reads the Register; re-runs nothing."""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from occams.register import Register


def report(path: Path) -> str:
    reg = Register(path)
    rows = reg.records()
    hyps = [r for r in rows if r["type"] == "HypothesisRegistered"]
    refusals = [r for r in rows if r["type"] == "RefusalRecorded"]
    resolved = [r for r in rows if r["type"] == "HypothesisResolved"]
    by_hyp = defaultdict(list)
    for r in refusals:
        by_hyp[r.get("hypothesis_id")].append(r)
    out = [f"Register: {path} — {len(rows)} records, chain verified",
           f"Searched: {len(hyps)} hypotheses, search-space cells {sum(h['search_space_size'] for h in hyps)}, "
           f"alpha spent {sum(h['alpha_spent'] for h in hyps):.4f}",
           f"Resolved: {len(resolved)} ({Counter(r['outcome'] for r in resolved) or 'none'})",
           f"Refusals: {len(refusals)}", ""]
    for h in hyps:
        out.append(f"- {h['hypothesis_id']} [{h['tier']}/{h['axis']}] k={h['search_space_size']} "
                   f"alpha={h['alpha_spent']:.4f} floor=({h['floor_ev_net_r']}R, {h['floor_min_trades_per_year']}/yr) "
                   f"N required {h['required_n']} available {h['available_n']}")
        for r in by_hyp.get(h["hypothesis_id"], []):
            out.append(f"    refused at {r['transition']}: {r['reason']}")
    orphan = by_hyp.get(None, [])
    for r in orphan:
        out.append(f"- (no hypothesis) refused at {r['transition']}: {r['reason']}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: python -m occams refusals REGISTER.jsonl")
        return 2
    print(report(Path(argv[0])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
