"""``python -m occams console`` — the research console (M11.4, F8).

    python -m occams console --register register/register.jsonl [--archive DIR]
                             [--config occams.toml] [--out docs/console.html]
                             [--controls all|synthetic|none]

ONE static HTML file rendered from the Register, stamped with the chain
head, the engine sha, the config sha and the generation time. Offline: no
network, no credentials, no bars. The controls run inside the build; if a
null is accepted or a signal refused the page says so at the top and the
command exits 1 (S3, S10).

Two builds. Without ``--config`` the *plain build* shows what the Register
alone supports: spend, verdicts, refusals, spans. With it the *author's
build* adds the balances, the falsifier count and the partition split, and
labels itself. Money cannot reach either: the configuration is reduced to
an ``AuthorView`` that has no field for it (S7, R9).

The generated page is committed under ``docs/`` so a verdict's rendering is
diffable; it is never served. Publishing it is the M11.7 gate.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from occams.console.facts import AuthorView, Facts, gather
from occams.console.render import render


def build(register: Path, *, archive: Path | None = None, author: AuthorView | None = None,
          controls: str = "all", generated: str | None = None, repo_sha: str | None = None,
          others: tuple[Path, ...] = ()) -> tuple[str, Facts]:
    """One page. ``others`` are further programmes' Registers (M12.0): each
    is rendered as its own programme beside the first, sharing the archive
    and the controls; a closed one is marked closed."""
    facts = gather(Path(register), archive_dir=archive, author=author, controls=controls,
                   generated=generated, repo_sha=repo_sha)
    more = [gather(Path(o), archive_dir=archive, author=author, controls="none", generated=facts.generated,
                   repo_sha=facts.repo_sha, controls_outcomes=facts.controls) for o in others]
    return render(facts, others=tuple(more)), facts


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    p = argparse.ArgumentParser(prog="python -m occams console", description=__doc__.split("\n\n")[1])
    p.add_argument("--register", required=True, action="append",
                   help="a chained Register to render; repeat for a second programme (the first is primary)")
    p.add_argument("--archive", default=None, help="archive directory; only its manifest is read")
    p.add_argument("--config", default=None, help="the author's occams.toml: adds balances and the falsifier count, labelled")
    p.add_argument("--out", default="docs/console.html")
    p.add_argument("--controls", choices=("all", "synthetic", "none"), default="all")
    a = p.parse_args(argv)
    author = None
    if a.config:
        from occams.config import ConfigRefused, load

        try:
            author = AuthorView.from_config(load(a.config))
        except ConfigRefused as e:
            print("REFUSED: the configuration does not load.")
            for r in e.reasons:
                print(f"  - {r}")
            return 2
    try:
        page, facts = build(Path(a.register[0]), archive=Path(a.archive) if a.archive else None, author=author, controls=a.controls,
                            others=tuple(Path(r) for r in a.register[1:]))
    except Exception as e:  # a tampered Register, an unreadable manifest: a failure, not a report
        print(f"REFUSED: {type(e).__name__}: {e}")
        return 1
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    kind = "author's build" if author else "plain build"
    print(f"console: {out} ({len(page):,} bytes, {kind}) — Register {facts.register_path}, {len(facts.chain)} records, "
          f"head {facts.head[:12]}; {len(facts.findings)} question(s), {len(facts.resolved)} resolved; "
          f"archive {'present' if facts.archive_present else 'absent'}; controls {'held' if facts.controls_ok else 'FAILED'}"
          + ("" if facts.controls else " (not run)")
          + (f"; {len(a.register) - 1} further programme(s) rendered beside it" if len(a.register) > 1 else ""))
    if not facts.controls_ok:
        print("STOP: a control failed inside the build. Fix the guards before reading anything on the page (S3, S10).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
