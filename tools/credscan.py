"""Credential scan — R5, S5. A credential-shaped string anywhere in the tree
fails the build. Scans tracked PLUS untracked-but-not-ignored files (a new
file is invisible to ``git ls-files`` until committed, one commit too late).

Shapes are listed, not inferred, so a new one is a deliberate addition:
the Telegram bot token is here because CLAUDE.md said the scan should learn
it. Exit 1 on any hit. No allow-list — a hit is fixed, not excused.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SHAPES: dict[str, re.Pattern[str]] = {
    "aws access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "aws secret key": re.compile(r"(?i)aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}"),
    "telegram bot token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    "github token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b"),
    "slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY"),
    "assigned secret": re.compile(
        r"(?i)\b(?:api[_-]?key|api[_-]?secret|secret[_-]?key|access[_-]?token|auth[_-]?token|password)\b"
        r"\s*[:=]\s*['\"][A-Za-z0-9_\-/+=]{16,}['\"]"),
    "basic auth in url": re.compile(r"https?://[^/\s:@]+:[^/\s:@]+@"),
}

TEXT_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt", ".cfg",
                 ".ini", ".env", ".sh", ".pine", ".csv", ""}


def scannable_files(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root, capture_output=True, text=True, check=True).stdout.splitlines()
    return [root / p for p in sorted(set(out))
            if (root / p).is_file() and Path(p).suffix in TEXT_SUFFIXES]


def scan_text(text: str) -> list[tuple[str, int]]:
    hits = []
    for name, pat in SHAPES.items():
        for m in pat.finditer(text):
            hits.append((name, text.count("\n", 0, m.start()) + 1))
    return hits


def scan(root: Path) -> list[tuple[Path, str, int]]:
    found = []
    for f in scannable_files(root):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name, line in scan_text(text):
            found.append((f.relative_to(root), name, line))
    return found


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    hits = scan(root)
    if hits:
        for f, name, line in hits:
            print(f"CREDENTIAL SHAPE: {f}:{line} looks like a {name}")
        return 1
    print(f"credscan: {len(scannable_files(root))} files clean, {len(SHAPES)} shapes checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
