"""The programme page (M12.7): one static page that answers, for every
programme, *what did we search, what did it cost, what did we find* —
from each programme's Register, beside each other, the closed one marked
closed. A verdict is never shown without the survey cell it came from;
a question registered from a Draft says so.

    python -m occams programme --register R1 [--register R2 …] [--archive DIR] [--config PATH] [--out docs/programme.html]

No script, no network, no money by construction (the Register holds none
by type; the configuration reaches the page without a field for it). It
is built locally and committed, never served, and the publication gate's
check (M11.7, ``tools/prepublish.py``) runs on it before anything is
published (R7).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from occams.console.facts import AuthorView, Facts, Finding, gather
from occams.console.render import CSS, _shrinkage_table, count, day, esc, num, pill, short
from occams.stopping import describe as describe_stop

TITLE = "Occams · the programmes"


def _head(progs: list[Facts]) -> str:
    heads = " · ".join(f"P{i} {short(p.head)} ({count(len(p.chain))} records)" for i, p in enumerate(progs, 1))
    return ('<h1>Occams <span class="thin">the programmes</span></h1>'
            '<p class="lede">For each programme: <strong>what did we search, what did it cost, what did we find.</strong> '
            'Rendered from the programmes\' Registers and nothing else. <strong>A dated artifact, not a live view.</strong></p>'
            f'<p class="mono">{heads} · chain verified · generated {esc(progs[0].generated)}'
            + (f' · repository {short(progs[0].repo_sha)}' if progs[0].repo_sha else "") + '</p>'
            + ('<p class="note">Author\'s build: budgets, the falsifier count and the split come from the author\'s configuration. '
               'No money appears on this page and none can.</p>' if progs[0].author else
               '<p class="note">Plain build: spend is shown from the Register alone; budgets and the falsifier count are the author\'s configuration and are not shown.</p>'))


def _nav(progs: list[Facts]) -> str:
    items = []
    for i, _p in enumerate(progs, 1):
        items += [f'<a href="#searched-{i}">P{i} Searched</a>', f'<a href="#cost-{i}">P{i} Cost</a>', f'<a href="#found-{i}">P{i} Found</a>']
    return '<nav class="toc" aria-label="Sections">' + "".join(items) + "</nav>"


def _banner(f: Facts, n: int) -> str:
    state = pill("refused", "Closed") if f.lab_closed else pill("refused", "Stopped") if f.stopped else pill("pass", "Open")
    return (f'<h2 id="programme-{n}" class="programme">Programme {n} <span class="thin">· {esc(Path(f.register_path).name)} · '
            f'{count(len(f.chain))} records · head {short(f.head)}</span> {state}</h2>')


def _origin(fd: Finding) -> str:
    r = fd.registered
    if r.get("survey_cell"):
        return (f'survey cell <code>{esc(r["survey_cell"])}</code> of results {short(r["survey_results_sha"])} · '
                f'{count(r.get("screened_cells", 0))} cells screened · {esc(r.get("universe") or "—")}')
    return "registered from a Draft, not from a survey"


def _searched(f: Facts, n: int) -> str:
    universes = f.of("UniverseDeclared")
    latest_u: dict[str, dict] = {}
    for u in universes:
        latest_u[u["name"]] = u
    surveys = f.surveys
    screened = sum(int(s["cell_count"]) for s in surveys)
    tiles = [(count(len(latest_u)), "universes declared"), (count(len(surveys)), "surveys recorded"),
             (count(screened), "cells screened at zero alpha"), (count(len(f.findings)), "questions registered")]
    tiles_html = '<div class="tiles">' + "".join(f'<div class="tile"><div class="big">{b}</div><div class="lab">{lab}</div></div>' for b, lab in tiles) + "</div>"
    body = ""
    if latest_u:
        rows = "".join(f'<tr><td class="mono">{esc(u["name"])}</td><td class="num">{count(len(u["members"]))}</td><td>{esc(u["rule"][:120])}</td>'
                       f'<td>{esc(u["bias"][:140])}</td></tr>' for u in latest_u.values())
        body += ('<h5>Universes, each a record with its calendar frozen</h5><div class="wrap"><table><tr><th>Universe</th><th class="num">Names</th>'
                 '<th>Rule</th><th>Bias, named</th></tr>' + rows + "</table></div>")
    if f.classifier:
        c = f.classifier
        body += (f'<p class="note">Regime classifier frozen at <code>{short(c["frozen_hash"])}</code>, {esc(c["level"])}-level on {esc(c["index_name"])}, '
                 f'calibrated on the definition partition only ({esc(c["definition_first_at"][:10])} to {esc(c["definition_last_at"][:10])}).</p>')
    if surveys:
        rows = "".join(f'<tr><td class="mono">{esc(s["grid_name"])}</td><td class="mono">{short(s["grid_sha"])}</td><td class="num">{count(s["cell_count"])}</td>'
                       f'<td>{esc(", ".join(s["universes"]))}</td><td class="mono">{short(s["results_sha"])}</td><td class="mono">{esc(str(s["seed"]))}</td>'
                       f'<td><a href="surveys/{esc(s["grid_name"])}-seed{esc(str(s["seed"]))}.html">the survey page</a></td></tr>' for s in surveys)
        body += ('<h5>Surveys — breadth on the definition partition, zero alpha, no verdict</h5><div class="wrap"><table><tr><th>Grid</th><th>Grid sha</th>'
                 '<th class="num">Cells</th><th>Universes</th><th>Results</th><th>Seed</th><th></th></tr>' + rows + "</table></div>")
    else:
        body += '<p class="note">No survey: every question of this programme was registered from a Draft.</p>'
    if f.findings:
        rows = "".join(f'<tr><td class="mono">{esc(fd.id)}</td><td>{esc(fd.registered["tier"])}</td><td>{esc(fd.registered["axis"])}</td>'
                       f'<td>{esc(fd.registered["mechanism"])}</td><td class="num">{count(fd.registered["search_space_size"])}</td><td>{_origin(fd)}</td>'
                       f'<td>{esc(fd.state)}</td></tr>'
                       for fd in f.findings)
        body += ('<h5>Questions registered — depth, with alpha</h5><div class="wrap"><table><tr><th>Question</th><th>Tier</th><th>Axis</th>'
                 '<th>Mechanism</th><th class="num">k</th><th>Origin</th><th>State</th></tr>' + rows + "</table></div>")
    else:
        body += '<p class="note">No question registered yet. Registration is the author\'s act (M8.1, M12.5).</p>'
    return f'<h3 id="searched-{n}">What did we search</h3>' + tiles_html + body


def _cost(f: Facts, n: int) -> str:
    spent = sum(f.spent_by_axis.values())
    screened = sum(int(s["cell_count"]) for s in f.surveys)
    from_surveys = sum(1 for fd in f.findings if fd.registered.get("survey_cell"))
    consumed = [c for fd in f.findings for c in fd.consumed]
    tiles = [(num(spent, 3), "alpha spent, all axes"), (count(screened), f"cells screened, stamped on {count(from_surveys)} question(s) (N6)"),
             (count(len(consumed)), "measurement spans consumed")]
    tiles_html = '<div class="tiles">' + "".join(f'<div class="tile"><div class="big">{b}</div><div class="lab">{lab}</div></div>' for b, lab in tiles) + "</div>"
    if f.author:
        rows = ""
        for axis, budget in sorted(f.author.axis_budgets.items(), key=lambda kv: (-kv[1], kv[0])):
            used = f.spent_by_axis.get(axis, 0.0)
            rows += (f'<tr><td>{esc(axis)}</td><td class="num">{num(used, 4)}</td><td class="num">{num(budget, 2)}</td>'
                     f'<td class="num">{num(max(0.0, budget - used), 4)}</td></tr>')
        alpha = ('<h5>Alpha by axis · author\'s build</h5><div class="wrap"><table><tr><th>Axis</th><th class="num">Spent</th><th class="num">Budget</th>'
                 '<th class="num">Remaining</th></tr>' + rows + f'<tr><td>reserve</td><td class="num">{num(0.0, 4)}</td><td class="num">{num(f.author.reserve, 2)}</td>'
                 f'<td class="num">{num(f.author.reserve, 4)}</td></tr></table></div>'
                 '<p class="note">Spend is replayed from <code>AlphaSpent</code> records: rate × search-space size. The reserve stays sealed.</p>')
    else:
        rows = "".join(f'<tr><td>{esc(a)}</td><td class="num">{num(v, 4)}</td></tr>' for a, v in sorted(f.spent_by_axis.items())) or \
               '<tr><td colspan="2" class="note">nothing spent</td></tr>'
        alpha = ('<h5>Alpha spent by axis</h5><div class="wrap"><table><tr><th>Axis</th><th class="num">Spent</th></tr>' + rows + '</table></div>'
                 '<p class="note">Budgets are the author\'s configuration and are not shown on a plain build.</p>')
    cons = ""
    if consumed:
        rows = "".join(f'<tr><td class="mono">{esc(c["hypothesis_id"])}</td><td>{esc(c["partition"])}</td><td>{day(c["start_day"])} to {day(c["end_day"])}</td>'
                       f'<td>{esc(", ".join(c["names"]))}</td></tr>' for c in consumed)
        cons = ('<h5>Observations consumed</h5><div class="wrap"><table><tr><th>Question</th><th>Partition</th><th>Span</th><th>Names</th></tr>'
                + rows + '</table></div>')
    return f'<h3 id="cost-{n}">What did it cost</h3>' + tiles_html + alpha + cons


def _found(f: Facts, n: int) -> str:
    resolved = [fd for fd in f.findings if fd.resolved]
    standing = f.falsifier_standing()
    if f.author:
        fals = (f'{standing} of {f.author.falsifier_count} {esc(f.author.falsifier_outcome)} mechanism verdict'
                f'{"" if f.author.falsifier_count == 1 else "s"} — the count at which the lab closes, declared before the first question')
    else:
        fals = f'{standing} null mechanism verdict{"" if standing == 1 else "s"}; the closing count is the author\'s configuration'
    tiles = [(count(len(resolved)), "verdicts"), (count(sum(1 for fd in resolved if fd.resolved["outcome"] == "supported")), "supported"),
             (count(sum(1 for fd in resolved if fd.resolved["outcome"] == "null")), "null")]
    tiles_html = '<div class="tiles">' + "".join(f'<div class="tile"><div class="big">{b}</div><div class="lab">{lab}</div></div>' for b, lab in tiles) + "</div>"
    body = f'<p><strong>Lab falsifier:</strong> {fals}.</p>'
    if f.lab_closed:
        body += (f'<p class="stopline">The lab closed: {count(f.lab_closed["falsifier_count"])} {esc(f.lab_closed["outcome"])} verdicts '
                 f'({esc(", ".join(f.lab_closed["verdicts"]))}). Nothing registers after this record. '
                 f'The conclusion is drafted from the Register in <code>docs/PROGRAMME-CONCLUSION.md</code>, the author\'s to adopt.</p>')
    elif f.stopped:
        body += (f'<p class="stopline">The programme stopped: {esc(describe_stop(f.stopped))}. Nothing registers after this record. '
                 f'The conclusion is written from the Register by <code>python -m occams conclude</code> (M12.8), the author\'s to adopt.</p>')
    if resolved:
        rows = ""
        for fd in resolved:
            v = fd.resolved
            missed = ""
            if fd.depth:
                missed = f' · {count(fd.depth["missed"])} missed'
            rows += (f'<tr><td class="mono">{esc(fd.id)}</td><td>{pill("null" if v["outcome"] == "null" else "pass", v["outcome"])}</td>'
                     f'<td class="num">{num(v["ev_net_r"], 4, True)}</td><td class="num">{num(v["trades_per_year"], 1)}</td>'
                     f'<td class="num">{count(fd.measured["n"]) if fd.measured else "—"}{missed}</td>'
                     f'<td>{esc("; ".join(v["refusals"])) or "none"}</td><td>{_origin(fd)}</td></tr>')
        body += ('<h5>Verdicts — every one beside where it came from</h5><div class="wrap"><table><tr><th>Question</th><th>Outcome</th>'
                 '<th class="num">EV net R</th><th class="num">Trades / yr</th><th class="num">n</th><th>Refused by</th><th>Origin</th></tr>'
                 + rows + '</table></div>')
    else:
        body += '<p class="note">No verdict yet.</p>'
    body += _shrinkage_table(f)
    return f'<h3 id="found-{n}">What did we find</h3>' + tiles_html + body


def _footer(progs: list[Facts]) -> str:
    return ('<footer><p><strong>What this page is not.</strong> It is not live: it is rendered from the Registers and committed, and '
            'a later build is a later artifact. It is not a dashboard of profit: no equity curve, no money, by construction. It is not '
            'a verdict on anything a survey screened: a survey is breadth at zero alpha and says so on its own page. It is not public '
            'until the publication gate (R7): <code>tools/prepublish.py</code> checks it for scripts, network, credential shapes, '
            'broker terms, raw bars and money before any publication is recorded (M11.7).</p>'
            f'<p class="mono">generated {esc(progs[0].generated)} · ' + " · ".join(f"P{i} head {short(p.head)}" for i, p in enumerate(progs, 1)) + '</p></footer>')


def render_programmes(progs: list[Facts]) -> str:
    body = ""
    for i, p in enumerate(progs, 1):
        body += _banner(p, i) + _searched(p, i) + _cost(p, i) + _found(p, i)
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{esc(TITLE)}</title><style>{CSS}</style></head><body><main>"
            + _head(progs) + _nav(progs) + body + _footer(progs) + "</main></body></html>\n")


def build(registers: tuple[Path, ...], *, archive: Path | None = None, author: AuthorView | None = None,
          generated: str | None = None, repo_sha: str | None = None) -> tuple[str, list[Facts]]:
    """One page for every Register given, in order. The controls are not
    re-run here: the console is the instrument's calibration page."""
    progs: list[Facts] = []
    for r in registers:
        f = gather(Path(r), archive_dir=archive, author=author, controls="none",
                   generated=progs[0].generated if progs else generated, repo_sha=progs[0].repo_sha if progs else repo_sha)
        progs.append(f)
    return render_programmes(progs), progs


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    p = argparse.ArgumentParser(prog="python -m occams programme")
    p.add_argument("--register", required=True, action="append", help="a chained Register; repeat for each programme, in order")
    p.add_argument("--archive", default=None, help="archive directory; only its manifest is read")
    p.add_argument("--config", default=None, help="the author's configuration: adds budgets and the falsifier count, labelled")
    p.add_argument("--out", default="docs/programme.html")
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
        page, progs = build(tuple(Path(r) for r in a.register), archive=Path(a.archive) if a.archive else None, author=author)
    except Exception as e:  # noqa: BLE001 — a tampered Register or an unreadable manifest is a failure, not a report
        print(f"REFUSED: {type(e).__name__}: {e}")
        return 1
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"programme page: {out} ({len(page):,} bytes, {'author' if author else 'plain'}'s build) — "
          + "; ".join(f"P{i} {Path(f.register_path).name}: {len(f.chain)} records, {len(f.findings)} question(s), {len(f.resolved)} resolved, "
                      f"{len(f.surveys)} survey(s){', closed' if f.lab_closed else (', stopped' if f.stopped else '')}" for i, f in enumerate(progs, 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
