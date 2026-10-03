"""The publication gate's check (M11.7, R7, F18.7). Publishing is an
explicit recorded decision; before one is recorded, every page that would
go out and every Register that would go with it is checked here,
independently of the code that rendered them.

    python tools/prepublish.py [PATH ...]      # default: docs/*.html, docs/surveys/*.html, docs/*CONCLUSION*.md, docs/RUNBOOK.md, register/*.jsonl

A page fails on: a script; a network reference (http, https, @import);
a credential-shaped string (the shapes ``tools/credscan.py`` lists — one
list, imported); a broker's or venue's terms (R6, listed); raw bars — a
run of dated rows carrying four prices, which no page is allowed to
carry (F18.7). A Register fails on a payload key that names money (the
Register holds none by type, S7; this checks the file, not the type) or
on a credential shape. Exit 1 on any hit, naming the file and the reason.
No allow-list: a hit is fixed, not excused.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NETWORK = re.compile(r"(?i)\bhttps?://|@import\b|<link\b[^>]*\bhref\s*=\s*['\"]?//")
SCRIPT = re.compile(r"(?i)<script\b")
# R6: a broker's or venue's terms, by name. Listed, not inferred; extended by decision.
BROKER_TERMS = ("Trading 212", "Trading212", "T212", "Interactive Brokers", "IBKR", "spread bet", "spread-bet",
                "CFD", "margin call", "financing rate", "overnight fee")
BROKER = re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(t) for t in BROKER_TERMS) + r")(?![A-Za-z0-9])")
# F18.7: raw bars — a dated row followed, on the same line or cell run, by four prices
BAR_ROW = re.compile(r"\b\d{4}-\d{2}-\d{2}\b(?:[^\n<]|<\/?t[dh][^>]*>){0,60}?(?:\d+\.\d+(?:[^\n\d<]|<\/?t[dh][^>]*>){1,20}){3}\d+\.\d+")
BAR_ROWS_ALLOWED = 10   # a handful of dated prices is a fact; a run of them is a dataset
MONEY_KEYS = re.compile(r"(?i)(?:^|_)(?:money|cash|currency|balance|equity|capital|pnl|profit|drawdown|risk_per_trade)(?:$|_)")


def _credscan_shapes() -> dict[str, re.Pattern[str]]:
    spec = importlib.util.spec_from_file_location("_credscan", ROOT / "tools" / "credscan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return dict(mod.SHAPES)


def check_page(text: str, *, name: str = "page") -> list[str]:
    problems: list[str] = []
    if SCRIPT.search(text):
        problems.append(f"{name}: a <script> — a published page carries no script (M11.4)")
    m = NETWORK.search(text)
    if m:
        problems.append(f"{name}: a network reference ({m.group(0).strip()!r}) — a published page is self-contained")
    for label, pat in _credscan_shapes().items():
        if pat.search(text):
            problems.append(f"{name}: a credential-shaped string ({label}) (R5, S5)")
    m = BROKER.search(text)
    if m:
        problems.append(f"{name}: a broker's or venue's term ({m.group(0)!r}) (R6)")
    rows = len(BAR_ROW.findall(text))
    if rows > BAR_ROWS_ALLOWED:
        problems.append(f"{name}: {rows} dated rows with four prices — raw bars are never published (F18.7)")
    return problems


def check_register(text: str, *, name: str = "register") -> list[str]:
    problems: list[str] = []
    for i, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        try:
            payload = json.loads(line).get("payload", {})
        except json.JSONDecodeError:
            problems.append(f"{name}: line {i} is not a record")
            continue
        for k in payload:
            if MONEY_KEYS.search(str(k)):
                problems.append(f"{name}: record {i} ({payload.get('type')}) carries a key that names money: {k!r} (S7)")
    for label, pat in _credscan_shapes().items():
        if pat.search(text):
            problems.append(f"{name}: a credential-shaped string ({label}) (R5, S5)")
    return problems


def default_targets() -> list[Path]:
    out: list[Path] = []
    out += sorted((ROOT / "docs").glob("*.html"))
    out += sorted((ROOT / "docs" / "surveys").glob("*.html"))
    out += sorted((ROOT / "docs").glob("*CONCLUSION*.md"))   # M12.8: a conclusion goes out with the pages
    out += sorted((ROOT / "docs").glob("RUNBOOK.md"))        # M14.2: the runbook goes out with the pages
    out += sorted((ROOT / "docs").glob("SETUP.md"))          # M15.4: so does the setup path
    out += sorted((ROOT / "docs").glob("INTEGRITY.md"))      # M15.1: and the integrity write-up
    out += sorted((ROOT / "docs").glob("EXTENDING.md"))      # M15.10: the extending guide
    out += sorted((ROOT / "docs").glob("EXPLAINER-*.md"))     # M15.11: the explainers
    out += sorted((ROOT / "docs").glob("PUBLICATION.md"))     # M15.12: the decision itself goes out with the pages
    out += sorted((ROOT / "docs" / "reviews").glob("*.md"))   # M16.2: an external review and its verification go out with the pages
    out += sorted((ROOT / "register").glob("*.jsonl"))
    if (ROOT / "build" / "console.html").exists():
        out.append(ROOT / "build" / "console.html")
    return out


# ---- M15.3: the whole tree, before the flip ------------------------------------------------------
#
# The page checks cover what is published as a page; this walks every committed
# text file for what a reader of the repository itself would see: a broker's or
# venue's term (R6), a money figure in prose, a private path, an e-mail address,
# an account identifier. Every hit is either removed or kept by the author's
# recorded decision in tools/publication-decisions.toml — nothing is excused
# silently. The scanner and its test name the terms they refuse and are exempt
# from the broker check by construction.

TREE_TEXT_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".jsonl", ".txt", ".cfg", ".sh", ".html", ".css", ".example"}
TREE_EXEMPT = {"tools/prepublish.py", "tests/test_prepublish.py", "tools/publication-decisions.toml"}   # they name what they refuse or keep
TREE_CHECKS: dict[str, re.Pattern[str]] = {
    "broker term (R6)": BROKER,
    "money figure": re.compile(r"(?<![A-Za-z0-9_])[$£€]\s?\d[\d,]*(?:\.\d+)?"),
    "private path": re.compile(r"(?:/Users/[A-Za-z0-9_.-]+|(?<![A-Za-z0-9])~/[A-Za-z0-9_.-]+|\bDocuments/[^\s`)\"']+)"),
    "e-mail address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "account identifier": re.compile(r"(?<![0-9A-Za-z.,])\d{12}(?![0-9A-Za-z.,])"),
}
DECISIONS = ROOT / "tools" / "publication-decisions.toml"


def committed_text_files(root: Path = ROOT) -> list[Path]:
    import subprocess

    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, text=True, check=True).stdout
    files = [root / f for f in out.split("\0") if f]
    return [f for f in files if f.suffix in TREE_TEXT_SUFFIXES or f.name in ("Makefile", "LICENSE", "NOTICE")]


def load_decisions(path: Path = DECISIONS) -> list[dict]:
    import tomllib

    if not path.exists():
        return []
    return list(tomllib.loads(path.read_text(encoding="utf-8")).get("keep", []))


def scan_tree(files: list[Path], *, decisions: list[dict], root: Path = ROOT) -> tuple[list[dict], list[dict]]:
    """Every hit as {file, line, check, match}; returns (unresolved, kept)."""
    unresolved, kept = [], []
    for f in files:
        rel = str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for check, pat in TREE_CHECKS.items():
                if rel in TREE_EXEMPT:
                    continue
                if check == "money figure" and (f.suffix == ".sh" or f.name == "Makefile"):
                    continue        # $1, $2 … are positional parameters in a shell, not amounts
                if check == "account identifier" and f.suffix in (".html", ".jsonl"):
                    continue        # pages and Registers are checked by their own rules; a 12-digit run there is a hash or a float
                for m in pat.finditer(line):
                    hit = {"file": rel, "line": i, "check": check, "match": m.group(0)}
                    d = next((d for d in decisions if d.get("file") == rel and d.get("check") == check
                              and d.get("match") in ("*", hit["match"])), None)
                    (kept if d else unresolved).append({**hit, **({"by": d["by"], "date": d["date"], "reason": d.get("reason", "")} if d else {})})
    return unresolved, kept


def heads_problems(root: Path = ROOT) -> list[str]:
    """M16.4 / ADR-0054: every committed store against its pinned count and head. A rewrite
    or a truncation of a store verifies on its own chain and fails here."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from occams.register import heads

    return heads.check(Path(root) / "register" / "HEADS.toml", root=Path(root))


def tree_main() -> int:
    unresolved, kept = scan_tree(committed_text_files(), decisions=load_decisions())
    for h in unresolved:
        print(f"TREE HIT: {h['file']}:{h['line']}: {h['check']} ({h['match']!r})")
    for h in kept:
        print(f"kept by decision: {h['file']}:{h['line']}: {h['check']} ({h['match']!r}) — {h['by']}, {h['date']}")
    by_file = len({h["file"] for h in unresolved})
    if unresolved:
        print(f"prepublish --all: {len(unresolved)} unresolved hit(s) in {by_file} file(s), {len(kept)} kept by recorded decision — "
              f"each is removed or kept in {DECISIONS.relative_to(ROOT)} before the flip (M15.3)")
        return 1
    print(f"prepublish --all: every committed text file clean, {len(kept)} hit(s) kept by recorded decision (M15.3)")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--all" in argv:
        return tree_main()
    targets = [Path(a) for a in argv] or default_targets()
    heads = [] if argv else heads_problems()
    problems: list[str] = []
    pages = regs = 0
    for t in targets:
        if not t.exists():
            problems.append(f"{t}: missing")
            continue
        text = t.read_text(encoding="utf-8", errors="replace")
        rel = str(t.resolve().relative_to(ROOT)) if t.resolve().is_relative_to(ROOT) else str(t)
        if t.suffix == ".jsonl":
            regs += 1
            problems += check_register(text, name=rel)
        else:
            pages += 1
            problems += check_page(text, name=rel)
    problems += [f"pinned heads — {h}" for h in heads]
    if problems:
        for p in problems:
            print(f"PREPUBLISH FAIL: {p}")
        return 1
    pinned = "" if argv else "; every committed store matches its pinned head (ADR-0054)"
    print(f"prepublish: {pages} page(s), {regs} register(s) clean — no script, no network, no credential shape, no broker term, "
          f"no raw bars, no money key (M11.7){pinned}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
