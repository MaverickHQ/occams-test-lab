"""``python -m occams ingest`` — pull the M0.7 class into the archive through
the port (M4.1): rights first, the 500-symbol monthly budget second, the
fetch third, the archive last. The live source takes its key from
``TIINGO_API_KEY`` and nowhere else (R5); ``--fixture PATH`` uses the
synthetic Tiingo-format fixture instead, for a dry run that reaches no
network."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from occams.data.archive import BarArchive
from occams.data.rights import REGISTRY, Answer, Rights, RightsRefused, Use
from occams.data.source import BudgetExceeded, CsvSource, FixtureSource, RateLimited, SourceError, SymbolBudget, TiingoSource, ingest

TIINGO_STARTER_SYMBOLS_PER_MONTH = 500  # docs/M0-ANSWERS.md §M0.3, as displayed 2026-09-10


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m occams ingest")
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--start", required=True, type=date.fromisoformat)
    ap.add_argument("--end", required=True, type=date.fromisoformat)
    ap.add_argument("--archive", required=True, type=Path)
    ap.add_argument("--budget", type=Path, help="symbol-budget ledger (default: <archive>/symbol-budget.json)")
    ap.add_argument("--fixture", type=Path, help="synthetic Tiingo-format fixture instead of the live source")
    ap.add_argument("--csv", type=Path, help="M15.5: your own bars — a directory of <SYMBOL>.csv or one file; no vendor, no key, no budget charge")
    ap.add_argument("--source-id", default=None, help="with --csv: the name the archive records the series under (required)")
    ap.add_argument("--rights-provenance", default=None,
                    help="with --csv: where the bars came from and what you may do with them, in your words (required — a CSV carries no licence)")
    ap.add_argument("--permit", default="",
                    help="with --csv: the uses you declare allowed, comma-separated from "
                         "private_retention, internal_reproduction, raw_redistribution, derived_artifacts, synthetic_publication; "
                         "everything else is recorded forbidden; private_retention is needed to archive at all")
    ap.add_argument("--venue", default="NYSE")
    ap.add_argument("--refresh", action="store_true",
                    help="fetch even if the archive already covers the span (a vendor revision lands beside the original)")
    a = ap.parse_args(argv)
    archive = BarArchive(a.archive)
    registry = REGISTRY
    budget: SymbolBudget | None = SymbolBudget(a.budget or (a.archive / "symbol-budget.json"), limit=TIINGO_STARTER_SYMBOLS_PER_MONTH)
    if a.csv:
        if not a.source_id or not (a.rights_provenance or "").strip():
            print("REFUSED: --csv needs --source-id and --rights-provenance — your bars, your name for them, and the rights in your "
                  "words; a CSV carries no licence and an undeclared right is a refusal (F18.7)")
            return 1
        try:
            permitted = {Use(u.strip()) for u in a.permit.split(",") if u.strip()}
        except ValueError as e:
            print(f"REFUSED: --permit names a use the rights matrix does not have: {e}")
            return 1
        rights = Rights(source_id=a.source_id, recorded_on=date.today().isoformat(), provenance=a.rights_provenance.strip(),
                        uses={u: (Answer.ALLOWED if u in permitted else Answer.FORBIDDEN) for u in Use},
                        notes="declared by the user at ingest (M15.5); recorded in the archive under rights/")
        registry = {**REGISTRY, a.source_id: rights}
        sha = archive.put_blob("rights", {"source_id": rights.source_id, "recorded_on": rights.recorded_on, "provenance": rights.provenance,
                                         "uses": {u.value: ans.value for u, ans in rights.uses.items()}, "notes": rights.notes})
        print(f"rights for {a.source_id} recorded in the archive as rights/{sha[:12]}: "
              + ", ".join(f"{u.value} {ans.value}" for u, ans in rights.uses.items()))
        source = CsvSource(a.csv, a.source_id)
        budget = None                                     # your own bars are not the vendor's symbols
    else:
        source = FixtureSource(a.fixture) if a.fixture else TiingoSource()
    month = date.today().strftime("%Y-%m")
    failures = 0
    for i, sym in enumerate(a.symbols):
        have = None if a.refresh else archive.covers(sym, a.start, a.end)
        if have is not None:
            print(f"{sym}: already archived {have['first_at'][:10]} -> {have['last_at'][:10]} as {have['sha'][:12]}; "
                  f"not fetched (pass --refresh to fetch anyway)")
            continue
        try:
            got = ingest(source, sym, a.start, a.end, archive=archive, budget=budget, month=month, registry=registry, venue=a.venue)
            print(f"{sym}: {got.bars.n} bars, {len(got.actions.actions)} actions -> {got.sha[:12]} ({got.rights.source_id}"
                  + (f"; budget used this month: {len(budget.used(month))}/{budget.limit})" if budget is not None else "; your own bars, no budget charge)"))
        except RateLimited as e:
            # the hour's allocation is spent (M0.3: 50 requests an hour on Starter); every further request
            # fails the same way, so stop here and name what is left rather than charge the ledger for it
            rest = a.symbols[i + 1:]
            print(f"{sym}: REFUSED — {e}")
            print(f"STOPPED: the source's hourly request allocation is spent; {len(rest)} not requested"
                  + (f": {' '.join(rest)}" if rest else "") + " — rerun after the hour")
            return 1
        except (RightsRefused, BudgetExceeded, SourceError) as e:
            print(f"{sym}: REFUSED — {e}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
