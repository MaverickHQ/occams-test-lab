"""The pinned heads of the hash-chained stores (M16.4, ADR-0054).

A line's digest shows that the line was not changed without the rest of the file.
It cannot show that the file is the one that was written: a copy with one outcome
flipped and every digest recomputed verifies, and so does a copy cut short. So the
count and the head of every committed store are pinned in ``register/HEADS.toml``,
the tests and the publication check compare the stores with the pin, and the pin is
attested outside the repository when it changes. A pin is moved only by this
module's command, after an append — never by hand.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from collections.abc import Iterable

from occams.register.store import Store, TamperedHistory, now

ROOT = Path(__file__).resolve().parent.parent.parent
HEADS = ROOT / "register" / "HEADS.toml"
GENESIS = "genesis"

HEADER = """\
# The count and the head of every hash-chained store under register/ (ADR-0054).
# Written by `python -m occams register pin` after an append, never by hand; compared
# with the stores by the tests and by tools/prepublish.py; attested outside this
# repository whenever it changes. The attestation dates the pin, not the past.
"""


def head_of(path: Path) -> tuple[int, str]:
    """(record count, head sha) of a store whose chain verifies; raises if it does not."""
    store = Store(path)
    n = store.verify()
    return n, (store.chain()[-1]["sha"] if n else GENESIS)


def load(heads_path: Path = HEADS) -> list[dict]:
    if not heads_path.exists():
        return []
    return list(tomllib.loads(heads_path.read_text(encoding="utf-8")).get("store", []))


def _dump(entries: list[dict]) -> str:
    out = [HEADER]
    for e in sorted(entries, key=lambda e: e["path"]):
        out.append(f'[[store]]\npath = "{e["path"]}"\ncount = {int(e["count"])}\nhead = "{e["head"]}"\npinned_at = "{e["pinned_at"]}"\n')
    return "\n".join(out)


def _rel(path: Path, root: Path) -> str:
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def pin(heads_path: Path, paths: Iterable[Path], *, root: Path = ROOT) -> list[dict]:
    """Pin each store as it stands. An entry whose count and head did not move keeps its date."""
    entries = {e["path"]: e for e in load(heads_path)}
    for p in paths:
        rel = _rel(p, root)
        count, head = head_of(Path(p))
        old = entries.get(rel)
        if old is None or int(old["count"]) != count or old["head"] != head:
            entries[rel] = {"path": rel, "count": count, "head": head, "pinned_at": now()}
    heads_path.parent.mkdir(parents=True, exist_ok=True)
    heads_path.write_text(_dump(list(entries.values())), encoding="utf-8")
    return load(heads_path)


def repin_if_pinned(store_path: Path, *, heads_path: Path = HEADS, root: Path = ROOT) -> bool:
    """After an append: move the pin of a store that is pinned. A store outside the pin
    (a scratch Register, a test's) is left alone. Returns whether the pin moved."""
    try:
        rel = _rel(store_path, root)
    except ValueError:
        return False
    if rel not in {e["path"] for e in load(heads_path)}:
        return False
    before = load(heads_path)
    return pin(heads_path, [store_path], root=root) != before


def check(heads_path: Path = HEADS, *, root: Path = ROOT) -> list[str]:
    """Every problem, by name: a store that left its pin, one that is not pinned, a pin with no store."""
    problems: list[str] = []
    pinned = {e["path"]: e for e in load(heads_path)}
    if not pinned:
        return [f"{heads_path}: no pinned heads — run `python -m occams register pin`"]
    for rel, e in sorted(pinned.items()):
        path = Path(root) / rel
        if not path.exists():
            problems.append(f"{rel}: pinned at {e['count']} records, head {e['head'][:12]}, and missing from the tree")
            continue
        try:
            count, head = head_of(path)
        except TamperedHistory as err:
            problems.append(f"{rel}: the chain itself is broken — {err}")
            continue
        if count < int(e["count"]):
            problems.append(f"{rel}: truncated — {count} records against the {e['count']} pinned (head {e['head'][:12]})")
        elif count > int(e["count"]):
            problems.append(f"{rel}: {count} records against the {e['count']} pinned — an append that was not pinned "
                            f"(`python -m occams register pin`)")
        elif head != e["head"]:
            problems.append(f"{rel}: rewritten — {count} records as pinned, head {head[:12]} against the pinned {e['head'][:12]}")
    folder = Path(root) / "register"
    for p in sorted(folder.glob("*.jsonl")) if folder.is_dir() else []:
        rel = _rel(p, root)
        if rel not in pinned:
            problems.append(f"{rel}: not pinned — every committed store is (`python -m occams register pin`)")
    return problems


def main(argv: list[str] | None = None) -> int:
    """``python -m occams register pin|check [--heads PATH] [--root DIR] [STORE ...]``."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("pin", "check"):
        print("usage: python -m occams register pin|check [--heads PATH] [--root DIR] [STORE ...]")
        return 2
    cmd, rest = argv[0], argv[1:]
    root, heads_path, stores = ROOT, None, []
    while rest:
        a = rest.pop(0)
        if a == "--heads":
            heads_path = Path(rest.pop(0))
        elif a == "--root":
            root = Path(rest.pop(0))
        else:
            stores.append(Path(a))
    heads_path = heads_path or (Path(root) / "register" / "HEADS.toml")
    if cmd == "pin":
        stores = stores or sorted((Path(root) / "register").glob("*.jsonl"))
        for e in pin(heads_path, stores, root=root):
            print(f"pinned {e['path']}: {e['count']} records, head {e['head'][:12]}")
        return 0
    problems = check(heads_path, root=root)
    for p in problems:
        print(f"HEADS: {p}")
    if not problems:
        print(f"heads: {len(load(heads_path))} store(s) match their pins ({heads_path})")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
