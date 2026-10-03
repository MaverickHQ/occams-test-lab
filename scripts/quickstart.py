"""S2 / M1.6 — the $0 quickstart. No data, no credentials, no network, under
ten seconds.

At M1 there is no engine and no strategy, so this shows the four things that
exist and are worth showing, in the order they protect the rest:

  1. PROVENANCE     the vendored core matches its recorded hashes
  2. IMPORT CLOSURE occams/core imports nothing outside itself
  3. NO DEFAULTS    started without occams.toml, the system refuses, naming
                    every required field and no value
  4. POWER          the vendored calculator reproduces M0.15's on-paper
                    number from the same declared parameters

Step 3 is the point. The three sets of numbers are the author's; a program
that runs without them has defaulted them, and a default is a
recommendation (R9).

    python3 scripts/quickstart.py        (or: make quickstart)
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from occams import config  # noqa: E402
from occams.core import power  # noqa: E402

RULE = "-" * 72


def head(n: int, title: str) -> None:
    print(f"\n{RULE}\n{n}. {title}\n{RULE}")


def _tool(name: str):
    spec = importlib.util.spec_from_file_location(f"_{name}", ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def controls() -> dict:
    """The four controls, as data, so a test asserts the same numbers this prints."""
    out: dict = {}
    prov = json.loads((ROOT / "occams" / "core" / "PROVENANCE.json").read_text())
    out["provenance_mismatches"] = _tool("vendor_core").verify(False)
    out["modules"] = len([r for r in prov["files"] if r["kind"] == "module"])
    out["donor_commit"] = prov["donor_commit"]

    out["leaks"] = _tool("closure").leaks()

    # No defaults — start without a config and read the refusal.
    try:
        config.load(ROOT / "this-file-does-not-exist.toml")
        out["refused"] = False
    except config.ConfigRefused as e:
        out["refused"] = True
        out["refusal"] = e.reasons
    out["required_fields"] = (len(config.CAPITAL_FIELDS) + len(config.ALPHA_FIELDS)
                              + len(config.AXIS_FIELDS) * len(config.InformationAxis)
                              + len(config.LAB_FIELDS))

    # Power — M0.15's row: floor 0.15R, sigma 1.2R, k = 4, 80 %.
    # These are the declared on-paper parameters of docs/M0-ANSWERS.md, not
    # money, alpha or the falsifier, and the answer there was 714.
    out["n_required"] = power.n_for_mean_shift(0.15 / 1.2, alpha=0.05 / 4, power=0.80)
    return out


def main() -> int:
    t0 = time.perf_counter()
    c = controls()
    ok = True

    head(1, "PROVENANCE — the vendored core is the donor's, at a recorded commit")
    print(f"{c['modules']} modules from prop-challenge-lab @ {c['donor_commit'][:12]}: "
          f"{c['provenance_mismatches']} hash mismatches")
    ok &= c["provenance_mismatches"] == 0 and c["modules"] == 12

    head(2, "IMPORT CLOSURE — occams/core reaches nothing outside itself")
    print("leaks:", c["leaks"] or "none (stdlib, numpy, pandas admitted)")
    ok &= not c["leaks"]

    head(3, "NO DEFAULTS — started without occams.toml, the system refuses")
    print("refused:", c["refused"])
    for r in c.get("refusal", []):
        print("  -", r)
    print(f"{c['required_fields']} required fields; none has a default or a recommended value.")
    ok &= c["refused"]

    head(4, "POWER — the vendored calculator agrees with M0.15's paper")
    print(f"floor 0.15R, sigma 1.2R, Bonferroni over 4, power 80%: N = {c['n_required']}  "
          f"(docs/M0-ANSWERS.md §M0.15 says 714)")
    ok &= c["n_required"] == 714

    dt = time.perf_counter() - t0
    print(f"\n{RULE}\n{'ALL FOUR PASS' if ok else 'A CONTROL FAILED'} in {dt:.2f}s. "
          "This touched no market data, no API key, and no network.\n"
          "make null and make signal are the fifth and sixth: S3 and S10, in CI.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
