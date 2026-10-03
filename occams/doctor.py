"""``python -m occams init`` and ``python -m occams doctor`` — the setup path a
stranger walks (M15.4).

``init`` writes the configuration *skeleton* from the schema: every required
key with a placeholder and no value. The three sets of numbers — money, alpha,
the falsifier — are the author's alone; a placeholder is not a default, and
the lab refuses to start until each is declared (R9, R4, ADR-0033). It never
overwrites: a configuration is the author's document.

``doctor`` says what is missing, by name, and never prints a secret: the
interpreter, the install, the configuration and which keys are still
placeholders, the data key (the environment, or the macOS Keychain — checked
for presence only), the archive, and the AWS CLI the burst needs with the
variables the burst scripts read. It exits non-zero when the lab could not
start; the AWS checks are advisory, since the burst is optional.
"""

from __future__ import annotations

import argparse
import importlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"=\s*<(float|int|str|bool)>")
BURST_VARIABLES = (
    ("REGION", "the AWS region; default: the CLI's configured region"),
    ("INSTANCE_TYPES", "spot instance types to try in order; default: c7a.32xlarge c6i.32xlarge"),
    ("CONFIG", "the programme's configuration file (gitignored); default: configs/programme-2.toml"),
    ("REGISTER", "the programme's Register the box reads; default: register/programme-2.jsonl"),
    ("NAME", "the prefix of every AWS resource the burst creates; default: occams-burst"),
)


def init_main(argv: list[str] | None = None) -> int:
    from occams.config import schema

    ap = argparse.ArgumentParser(prog="python -m occams init",
                                 description="write the configuration skeleton — every required key, no value")
    ap.add_argument("--out", type=Path, default=Path("occams.toml"))
    a = ap.parse_args(argv or [])
    if a.out.exists():
        print(f"REFUSED: {a.out} exists — a configuration is the author's document and is never overwritten; "
              f"edit it, or pass --out for another path")
        return 1
    text = ("# The lab's configuration — the author's numbers, never defaulted (R9, R4, ADR-0033).\n"
            "# Every <placeholder> must be replaced before the lab starts; `python -m occams doctor`\n"
            "# names the ones still unfilled and `python -m occams whatif` shows what a set implies.\n"
            "# This file is gitignored: it carries capital, drawdown and risk figures and the alpha split.\n\n"
            + schema().rstrip("\n") + "\n")
    a.out.write_text(text, encoding="utf-8")
    n = len(PLACEHOLDER.findall(text))
    print(f"wrote {a.out}: {n} keys to declare, no value supplied — the numbers are yours (R9, R4)")
    return 0


# ---- doctor ------------------------------------------------------------------------------------

def _keychain_has(service: str) -> bool | None:
    """True/False on macOS by presence only — the secret is never read; None elsewhere."""
    if sys.platform != "darwin" or shutil.which("security") is None:
        return None
    r = subprocess.run(["security", "find-generic-password", "-s", service], capture_output=True, text=True)
    return r.returncode == 0


def _aws_configured() -> tuple[bool, str]:
    if shutil.which("aws") is None:
        return False, "the AWS CLI is not on PATH (the burst is optional; install it to run surveys on a spot instance)"
    region = subprocess.run(["aws", "configure", "get", "region"], capture_output=True, text=True).stdout.strip()
    ident = subprocess.run(["aws", "sts", "get-caller-identity", "--query", "Arn", "--output", "text"],
                           capture_output=True, text=True)
    if ident.returncode != 0:
        return False, "the AWS CLI has no working credentials (`aws configure`, or a profile in the environment)"
    return True, f"the AWS CLI is configured{' for region ' + region if region else ' (no default region: set REGION or `aws configure`)'}"


def checks(*, config: Path, archive: Path, env: dict | None = None, cwd: Path | None = None) -> list[tuple[str, str, str]]:
    """Every check as (status, name, detail): status is ``ok``, ``missing`` (the lab cannot start) or ``note`` (advisory)."""
    env = os.environ if env is None else env
    cwd = Path.cwd() if cwd is None else cwd
    out: list[tuple[str, str, str]] = []
    v = sys.version_info
    out.append(("ok" if (v.major, v.minor) >= (3, 12) else "missing", "interpreter",
                f"Python {v.major}.{v.minor}.{v.micro}" + ("" if (v.major, v.minor) >= (3, 12) else " — 3.12 or later is required")))
    for mod, what in (("numpy", "the vendored core's one dependency"), ("pytest", "the dev extras (`make setup`)"), ("ruff", "the dev extras")):
        try:
            importlib.import_module(mod)
            out.append(("ok", f"install: {mod}", what))
        except ImportError:
            out.append(("missing" if mod == "numpy" else "note", f"install: {mod}", f"not importable — {what}"))
    if not config.exists():
        out.append(("missing", "configuration", f"{config} does not exist — `python -m occams init` writes the skeleton; the numbers are yours"))
    else:
        text = config.read_text(encoding="utf-8")
        unfilled = [line.split("=")[0].strip() for line in text.splitlines() if PLACEHOLDER.search(line)]
        if unfilled:
            out.append(("missing", "configuration", f"{config}: {len(unfilled)} key(s) still a placeholder — " + ", ".join(unfilled[:8])
                        + (" …" if len(unfilled) > 8 else "") + "; the lab does not start until each is declared (R9, R4)"))
        else:
            try:
                from occams.config import load
                load(config)
                out.append(("ok", "configuration", f"{config} loads; alpha sums and partitions hold (S8)"))
            except Exception as e:   # noqa: BLE001 — the loader's refusal is the message
                out.append(("missing", "configuration", f"{config} is refused: {str(e).splitlines()[0][:160]}"))
    if env.get("TIINGO_API_KEY"):
        out.append(("ok", "data key", "TIINGO_API_KEY is in the environment (never printed)"))
    else:
        kc = _keychain_has("TIINGO_API_KEY")
        if kc:
            out.append(("ok", "data key", "TIINGO_API_KEY is in the macOS Keychain; substitute it inline at ingest (docs/RUNBOOK.md)"))
        else:
            out.append(("note", "data key", "TIINGO_API_KEY is not set" + (" and not in the Keychain" if kc is False else "")
                        + " — `make quickstart` and `make reproduce-public` need no data; ingesting does"))
    manifest = archive / "manifest.jsonl"
    if manifest.exists():
        n = sum(1 for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip())
        out.append(("ok", "archive", f"{archive}: {n} manifest entries (bars never leave this machine)"))
    else:
        out.append(("note", "archive", f"{archive} holds no manifest — nothing ingested yet; the controls and the public reproduction run without it"))
    ok, detail = _aws_configured()
    out.append(("ok" if ok else "note", "burst: AWS CLI", detail))
    out.append(("note", "burst: variables", "; ".join(f"{k} — {d}" for k, d in BURST_VARIABLES) + " (tools/aws/burst.env.example)"))
    for f in ("tools/aws/burst.sh", "tools/aws/user-data.sh"):
        out.append(("ok" if (cwd / f).exists() else "missing", f"burst: {f}", "present" if (cwd / f).exists() else "missing from the checkout"))
    return out


def doctor_main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m occams doctor", description="what is missing, by name; never a secret")
    ap.add_argument("--config", type=Path, default=Path("occams.toml"))
    ap.add_argument("--archive", type=Path, default=Path("archive"))
    a = ap.parse_args(argv or [])
    rows = checks(config=a.config, archive=a.archive)
    width = max(len(name) for _s, name, _d in rows)
    for status, name, detail in rows:
        mark = {"ok": "ok     ", "missing": "MISSING", "note": "note   "}[status]
        print(f"{mark}  {name.ljust(width)}  {detail}")
    missing = [name for s, name, _d in rows if s == "missing"]
    if missing:
        print(f"\nthe lab cannot start: {', '.join(missing)}")
        return 1
    print("\nthe lab can start; the notes are optional — `make quickstart` next (S2)")
    return 0
