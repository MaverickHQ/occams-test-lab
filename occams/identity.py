"""What measured it (M16.10; ADR-0055; the review's F13).

Three things identify the code behind a number, and before this module two of them were
soft. The **commit** was read by the vendored ``core/archive.engine_sha``, which appends
``-dirty`` when *anything* in the working tree has changed — the loop's own Register
appends included, so every programme 2 verdict reads ``-dirty`` — and returns ``unknown``
on any error; both were accepted. The **content hash** covered a hand-kept list of eleven
files that left out the fill model, the sizing rule, the measurement contract and the
guards. Here:

- the content hash is over the **import closure inside** ``occams/`` of the modules that
  measure — nothing is listed by hand, and a page template is not in it;
- **only code can make the tree dirty** — the status is read on the code paths alone;
- **dirty or unknown code does not measure** — ``require_clean`` refuses by name.

The vendored file is untouched; the lab stops asking it.
"""

from __future__ import annotations

import ast
import hashlib
import subprocess
from pathlib import Path
from collections.abc import Iterable

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ("occams.loop", "occams.engine.day_boxed", "occams.engine.position_boxed", "occams.survey.run")   # the modules that measure
CODE_PATHS = ("occams", "tools", "pyproject.toml")                                                         # what can make a tree dirty
PACKAGE = "occams"
UNKNOWN = "unknown"


class EngineNotClean(RuntimeError):
    """A measurement or a survey was asked of code that no commit holds, or of a tree
    whose commit cannot be read (ADR-0055). Commit the change, then measure."""


# ---- the content hash: what a measurement imports ---------------------------------------------------

def _exists_exactly(path: Path) -> bool:
    """Is there a file of exactly this name? On a file system that ignores case,
    ``Store.py`` "exists" beside ``store.py`` — and the closure, hence the hash, would then
    differ between the author's machine and a runner's."""
    try:
        return path.name in {p.name for p in path.parent.iterdir()} and path.is_file()
    except OSError:
        return False


def _file_of(module: str, root: Path) -> Path | None:
    base = root.joinpath(*module.split("."))
    if _exists_exactly(base.with_suffix(".py")):
        return base.with_suffix(".py")
    named_exactly = base.parent.is_dir() and base.name in {p.name for p in base.parent.iterdir()}
    if named_exactly and _exists_exactly(base / "__init__.py"):
        return base / "__init__.py"
    return None


def _is_command_line(node: ast.AST) -> bool:
    """A module's command-line entry — ``main`` or ``*_main`` — dispatches to pages, reports and
    other commands; what it imports is not something a measurement reaches."""
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (node.name == "main" or node.name.endswith("_main"))


def _walk(node: ast.AST):
    for child in ast.iter_child_nodes(node):
        if _is_command_line(child):
            continue
        yield child
        yield from _walk(child)


def _imported(path: Path, module: str, is_package: bool) -> set[str]:
    """Every module name ``path`` imports, absolute — at any depth, so an import inside a
    function counts: it is still code a measurement can reach. The one exception is a
    module's command-line entry."""
    here = module.split(".") if is_package else module.split(".")[:-1]
    out: set[str] = set()
    for node in _walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = here[:len(here) - (node.level - 1)]
                stem = ".".join(base + (node.module.split(".") if node.module else []))
            else:
                stem = node.module or ""
            if stem:
                out.add(stem)
                out.update(f"{stem}.{a.name}" for a in node.names)      # ``from occams.engine import probes`` names a module
    return out


def closure(entry: Iterable[str] = ENTRY, *, root: Path = ROOT) -> tuple[str, ...]:
    """The files under ``occams/`` that importing ``entry`` can reach, as sorted paths
    relative to ``root`` — each module's file and the ``__init__`` of every package above it."""
    root = Path(root)
    seen: dict[str, Path] = {}
    todo = list(entry)
    while todo:
        module = todo.pop()
        parts = module.split(".")
        if parts[0] != PACKAGE:
            continue
        for depth in range(1, len(parts) + 1):                     # the packages above it run too
            name = ".".join(parts[:depth])
            if name in seen:
                continue
            path = _file_of(name, root)
            if path is None:
                continue                                            # a name imported from a module, not a module
            seen[name] = path
            todo.extend(_imported(path, name, path.name == "__init__.py"))
    return tuple(sorted(p.relative_to(root).as_posix() for p in seen.values()))


def code_closure_sha(entry: Iterable[str] = ENTRY, *, root: Path = ROOT) -> str:
    """sha256 over the closure's paths and bytes, sixteen hex characters: the engine's
    identity by content. Any file a measurement depends on changes it; nothing else does."""
    root = Path(root)
    h = hashlib.sha256()
    for rel in closure(entry, root=root):
        h.update(rel.encode("utf-8") + b"\0" + (root / rel).read_bytes() + b"\0")
    return h.hexdigest()[:16]


_OWN: str | None = None


def own_code_sha() -> str:
    """The content hash of the code this process is running — read once: a process does
    not change the code it has imported."""
    global _OWN
    if _OWN is None:
        _OWN = code_closure_sha()
    return _OWN


# ---- the commit, and whether the code is what the commit holds ---------------------------------------

def _git(root: Path, *args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout
    except Exception:
        return None


def commit(root: Path = ROOT) -> str:
    """The commit of the tree at ``root``, or ``unknown`` — which measures nothing."""
    top = _git(Path(root), "rev-parse", "--show-toplevel")
    if top is None or Path(top.strip()).resolve() != Path(root).resolve():
        return UNKNOWN                                              # no repository here, or someone else's above it
    out = _git(Path(root), "rev-parse", "HEAD")
    return out.strip() if out and out.strip() else UNKNOWN


def dirty_paths(root: Path = ROOT) -> tuple[str, ...]:
    """The code paths that differ from the commit — modified, staged or untracked — and
    nothing else: a Register, an archive or a page written during a run is an output."""
    out = _git(Path(root), "status", "--porcelain", "--", *CODE_PATHS)
    if out is None:
        return ()
    return tuple(sorted(line[3:].split(" -> ")[-1].strip('"') for line in out.splitlines() if line.strip()))


def engine_sha(root: Path = ROOT) -> str:
    """The commit, ``-dirty`` when code differs from it, or ``unknown``."""
    head = commit(root)
    if head == UNKNOWN:
        return UNKNOWN
    return head + ("-dirty" if dirty_paths(root) else "")


def require_clean(what: str, *, root: Path = ROOT) -> str:
    """The commit ``what`` may stamp — or ``EngineNotClean``, naming why (ADR-0055 §3)."""
    head = commit(root)
    if head == UNKNOWN:
        raise EngineNotClean(f"{what} is refused: the commit of this tree cannot be read, so nothing it measured could be named "
                             f"(ADR-0055). Run from a checkout.")
    changed = dirty_paths(root)
    if changed:
        shown = ", ".join(changed[:6]) + (f" and {len(changed) - 6} more" if len(changed) > 6 else "")
        raise EngineNotClean(f"{what} is refused: the code differs from commit {head[:12]} — {shown}. A number measured on "
                             f"code no commit holds cannot be reproduced (ADR-0055). Commit the change, then measure.")
    return head


def describe(root: Path = ROOT) -> str:
    """One line for a run that is exempt and says so: the commit as found, and the content hash."""
    sha = engine_sha(root)
    shown = sha if sha == UNKNOWN else sha[:12] + ("-dirty" if sha.endswith("-dirty") else "")
    return f"code {shown} · content {code_closure_sha(root=root)}"
