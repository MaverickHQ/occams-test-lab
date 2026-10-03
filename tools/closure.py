"""M1.3 — the import-closure rule for ``occams/core/``, in one place, so the
CI test and the quickstart evaluate the same rule rather than two copies.

The core may import itself, the standard library, numpy and pandas. One lazy
import is admitted by name: ``archive`` reaches for an S3 client inside a
function that runs only when a bucket is configured. It is listed, not
hidden, so the closure claim stays honest about it.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parent.parent / "occams" / "core"
ALLOWED_THIRD_PARTY = frozenset({"numpy", "pandas"})
LAZY_ADMITTED = frozenset({("archive", "boto3")})


def leaks(core: Path = CORE) -> list[tuple[str, str]]:
    stdlib = sys.stdlib_module_names
    out: list[tuple[str, str]] = []
    for f in sorted(core.glob("*.py")):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            for n in names:
                top = n.split(".")[0]
                if top in stdlib or top in ALLOWED_THIRD_PARTY or top == "__future__":
                    continue
                if n.startswith("occams.core"):
                    continue
                if (f.stem, top) in LAZY_ADMITTED:
                    continue
                out.append((f.name, n))
    return out


if __name__ == "__main__":
    found = leaks()
    print("closure leaks:", found or "none")
    sys.exit(1 if found else 0)
