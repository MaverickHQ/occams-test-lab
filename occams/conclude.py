"""The conclusion, written from the Register after the programme stopped —
and not before (M12.8)::

    python -m occams conclude --register R --out PATH [--config C] [--archive A] [--plateau-cells 4]

Refused until one of the three stopping conditions is a Register record:
``LabClosed`` (the falsifier fired, ADR-0033) or ``ProgrammeStopped`` (its
alpha exhausted, or the author's stop). The document is in the shape of
``docs/PROGRAMME-CONCLUSION.md`` with the survey layer: cells screened,
questions registered from them, verdicts, shrinkage, eras. Every number in
it is in the Register, cited by record number; the sections that are the
author's — what outlasts the questions, the decision — are marked and
left. A draft has no standing; adoption is the author's recorded act. An
existing file is never overwritten: a conclusion is superseded by a new
file (append, never overwrite). No money is in the Register, so none can
reach the page (S7); the author's build adds budgets and the falsifier
count, labelled as such.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, UTC
from pathlib import Path

from occams.console.facts import AuthorView, Facts, Finding, gather
from occams.stopping import PLATEAU_CELLS, conditions, describe, stopping_record

CHECKS = ("beats-null", "plateau", "floor", "leave-one-out", "beats-always-long")
FOUR = CHECKS[:4]   # the checks a verdict with no `checks` field was evaluated against (before ADR-0043)
LABEL = {"plateau": "plateau", "beats_null": "beats-null", "clears_floor": "floor", "leave_one_out": "leave-one-out",
         "beats_always_long": "beats-always-long"}
AUTHORS = "*The author's, written on adoption. The Register does not choose.*"


# ---- small helpers ---------------------------------------------------------------

def _day(o) -> str:
    try:
        return date.fromordinal(int(o)).isoformat()
    except (TypeError, ValueError, OverflowError):
        return "—"


def _when(iso) -> str:
    try:
        return datetime.fromisoformat(str(iso)).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError):
        return str(iso or "—")


def _n(x, places: int = 3, sign: bool = False) -> str:
    if x is None:
        return "—"
    return f"{float(x):+.{places}f}" if sign else f"{float(x):.{places}f}"


def _c(x) -> str:
    return f"{int(x):,}"


def _cell(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def _short(sha) -> str:
    return str(sha or "")[:12]


def _refs(f: Facts):
    """Record numbers by payload identity: every payload a Facts holds is the chain's own object."""
    seq_of = {id(line["payload"]): line["seq"] for line in f.chain}

    def ref(p) -> str:
        return f"#{seq_of[id(p)]}" if p is not None and id(p) in seq_of else "—"
    return ref


def _evaluated(v: dict) -> tuple[str, ...]:
    names = tuple(v.get("checks") or ())
    return tuple(LABEL.get(n, n) for n in names) if names else FOUR


def _checks(fd: Finding) -> dict[str, str]:
    if not fd.resolved:
        return {c: "—" for c in CHECKS}
    evaluated = _evaluated(fd.resolved)
    out = {}
    for c in CHECKS:
        if c not in evaluated:
            out[c] = "not evaluated"
            continue
        hit = [r for r in fd.resolved["refusals"] if str(r).startswith(c + ":")]
        out[c] = ("refused — " + str(hit[0]).split(":", 1)[1].strip()) if hit else "passed"
    return out


def _origin(fd: Finding) -> str:
    r = fd.registered
    if r.get("survey_cell"):
        return (f"survey cell `{r['survey_cell']}` of results `{_short(r.get('survey_results_sha'))}`, "
                f"{_c(r.get('screened_cells', 0))} cells screened")
    return "a Draft under `docs/drafts/`, not a survey"


def _name_list(names) -> str:
    names = list(names)
    if len(names) > 12:
        return f"{len(names)} names: {', '.join(names[:6])} … {', '.join(names[-3:])}"
    return ", ".join(names) or "—"


def _names(fd: Finding) -> str:
    return _name_list(fd.consumed[-1]["names"]) if fd.consumed else "—"


def _span(fd: Finding) -> str:
    return f"{_day(fd.consumed[-1]['start_day'])} to {_day(fd.consumed[-1]['end_day'])}" if fd.consumed else "—"


def _eras(fd: Finding, ref) -> str:
    d = fd.depth
    if not d:
        return "—"
    eras = " / ".join(f"{_c(e['n'])} at {_n(e['ev_net'], 3, True)}" for e in d["eras"])
    held = ", ".join(_n(x, 3, True) for x in d["leave_one_era_out"])
    return f"{eras}; each held out {held}; {_c(d['missed'])} missed ({ref(d)})"


def _shrink(fd: Finding, ref) -> str:
    s = fd.shrinkage
    if not s:
        return "—"
    return (f"EV {_n(s['definition_ev_net'], 3, True)} → {_n(s['measured_ev_net'], 3, True)} (Δ {_n(s['ev_shrinkage'], 3, True)}); "
            f"margin {_n(s['definition_margin_net'], 3, True)} → {_n(s['measured_margin_net'], 3, True)} "
            f"(Δ {_n(s['margin_shrinkage'], 3, True)}) ({ref(s)})")


# ---- sections ----------------------------------------------------------------------

def _header(f: Facts, stop: dict, ref, dated: str) -> str:
    n_res = len(f.resolved)
    name = Path(f.register_path).name
    first = _when(f.chain[0]["payload"].get("at")) if f.chain else "—"
    last = _when(f.chain[-1]["payload"].get("at")) if f.chain else "—"
    return (f"# Programme conclusion — what {_c(n_res)} verdict{'' if n_res == 1 else 's'} established\n\n"
            f"**Dated {dated}. Draft: the author's to adopt.** Written from `{name}` because a stopping condition is a "
            f"record in it (M12.8): {describe(stop)} — record `{ref(stop)}`, {_when(stop.get('at'))}. Nothing here is new "
            f"analysis. Every number below is in the Register; the record number is given as `#n`. The Register holds "
            f"**{_c(len(f.chain))} records**, chain-verified, head `{_short(f.head)}`, from {first} to {last}. "
            f"No money appears in it and none appears here (ADR-0008, S7).\n\n")


def _scoreboard(f: Facts, ref) -> str:
    fds = f.findings
    if f.author:
        fals = (f"The falsifier was declared as {f.author.falsifier_count} {f.author.falsifier_outcome} mechanism "
                f"verdict{'' if f.author.falsifier_count == 1 else 's'} before the first question; it stands at "
                f"{f.falsifier_standing()}.")
    else:
        fals = (f"{f.falsifier_standing()} mechanism verdict{'' if f.falsifier_standing() == 1 else 's'} carried the "
                f"falsifier's outcome; the closing count is the author's configuration and is not shown on a plain build.")
    intro = (f"{_c(len(fds))} question{'' if len(fds) == 1 else 's'} registered by the author, "
             f"{_c(sum(1 for fd in fds if fd.measured))} measured on a partition no one looked at before registration, "
             f"{_c(len(f.resolved))} resolved by the machine against a floor declared before the run. {fals}\n\n")
    if not fds:
        return "## 1. The scoreboard\n\n" + intro + "No question was registered in this programme.\n\n"
    rows: list[tuple[str, list[str]]] = []

    def row(label, fn):
        rows.append((label, [fn(fd) for fd in fds]))
    row("axis", lambda fd: fd.registered["axis"])
    row("tier", lambda fd: fd.registered["tier"])
    row("mechanism", lambda fd: fd.registered["mechanism"])
    row("universe", lambda fd: fd.registered.get("universe") or "—")
    row("names", _names)
    row("measurement span", _span)
    row("origin", _origin)
    row("engine", lambda fd: fd.measured["engine"] if fd.measured else "—")
    row("search space k", lambda fd: _c(fd.registered["search_space_size"]))
    row("alpha spent", lambda fd: f"{_n(fd.registered['alpha_spent'], 4)} ({ref(fd.spent)})")
    row("required / available N", lambda fd: f"{_c(fd.registered['required_n'])} / {_c(fd.registered['available_n'])} ({ref(fd.registered)})")
    row("trades measured", lambda fd: (f"{_c(fd.measured['n'])} ({ref(fd.measured)})"
                                       + (f" · {_c(fd.depth['missed'])} missed" if fd.depth else "")) if fd.measured else "—")
    row("seed", lambda fd: str(fd.resolved["seed"]) if fd.resolved else (str(fd.measured["seed"]) if fd.measured else "—"))
    row("floor declared: net R, trades per year",
        lambda fd: f"{_n(fd.registered['floor_ev_net_r'], 2)}, {_n(fd.registered['floor_min_trades_per_year'], 0)}")
    row("EV per trade, net R", lambda fd: (f"**{_n(fd.resolved['ev_net_r'], 3, True)}** at {fd.resolved.get('cost_basis', 'unknown')} "
                                           f"costs ({ref(fd.resolved)})") if fd.resolved else "—")
    row("trades per year", lambda fd: _n(fd.resolved["trades_per_year"], 1) if fd.resolved else "—")
    for c in CHECKS:
        row(c, lambda fd, c=c: _checks(fd)[c])
    def outcome(fd) -> str:
        if fd.resolved:
            return f"**{fd.resolved['outcome']}** ({ref(fd.resolved)})"
        hit = [r for r in fd.refusals if r.get("transition") == "REGISTERED->MEASURED"]
        if not hit:
            return fd.state
        r = hit[-1]                    # M14.5: the refusal that left the question unresolved, with its evidence
        ev = r.get("evidence") or {}
        detail = ", ".join(f"{k} {_c(v) if isinstance(v, int) else v}" for k, v in ev.items())
        return f"{fd.state} — {r['reason']}" + (f" ({detail}; {ref(r)})" if detail else f" ({ref(r)})")

    row("outcome", outcome)
    row("winner chosen by", lambda fd: (fd.resolved.get("surface") or "EV (before ADR-0045)") if fd.resolved else "—")
    row("paths archived", lambda fd: f"{_c(fd.paths['draws'])} draws ({ref(fd.paths)})" if fd.paths else "—")
    row("eras on the measurement partition", lambda fd: _eras(fd, ref))
    row("shrinkage from screening", lambda fd: _shrink(fd, ref))
    head = "| | " + " | ".join(f"`{fd.id}`" for fd in fds) + " |\n|---|" + "---|" * len(fds) + "\n"
    body = "".join(f"| {label} | " + " | ".join(_cell(v) for v in vals) + " |\n" for label, vals in rows)
    return "## 1. The scoreboard\n\n" + intro + head + body + "\n"


def _survey_layer(f: Facts, ref) -> str:
    if not f.surveys:
        return "**The survey layer.** No survey was recorded; every question came from a Draft.\n\n"
    out = ["**The survey layer.** Breadth on the definition partition at zero alpha; nothing in a survey is a verdict; "
           "every cell screened is counted beside every question registered from it (N6).\n\n"]
    for s in f.surveys:
        from_it = [fd for fd in f.findings if fd.registered.get("survey_results_sha") == s["results_sha"]]
        qs = ", ".join(f"`{fd.id}` (cell `{fd.registered['survey_cell']}`)" for fd in from_it) or "none"
        out.append(f"- `{s['grid_name']}`, grid `{_short(s['grid_sha'])}`, seed {s['seed']}: {_c(s['cell_count'])} cells over "
                   f"{', '.join(s['universes'])}; results `{_short(s['results_sha'])}`; classifier `{_short(s['classifier_hash'])}` "
                   f"({ref(s)}). Questions registered from it: {qs}.\n")
    screened = sum(int(s["cell_count"]) for s in f.surveys)
    stamped = sum(int(fd.registered.get("screened_cells", 0)) for fd in f.findings)
    out.append(f"\nCells screened: {_c(screened)} across {_c(len(f.surveys))} survey(s), stamped on every question registered from "
               f"them ({_c(stamped)} in all, N6); questions registered: {_c(len(f.findings))}; verdicts: {_c(len(f.resolved))}.\n\n")
    rows = [fd for fd in f.findings if fd.shrinkage]
    if rows:
        out.append("| Question | Survey cell | Screened | EV, definition | EV, measured | Δ EV | Margin, definition | "
                   "Margin, measured | Δ margin | Verdict |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---|\n")
        for fd in rows:
            s = fd.shrinkage
            out.append(f"| `{fd.id}` | `{s['survey_cell']}` | {_c(s['screened_cells'])} | {_n(s['definition_ev_net'], 3, True)} | "
                       f"{_n(s['measured_ev_net'], 3, True)} | {_n(s['ev_shrinkage'], 3, True)} | {_n(s['definition_margin_net'], 3, True)} | "
                       f"{_n(s['measured_margin_net'], 3, True)} | {_n(s['margin_shrinkage'], 3, True)} | {fd.state} ({ref(s)}) |\n")
        out.append("\nNet R per trade. The definition numbers are the survey cell's on the calibration set; the measured ones are "
                   "the winner cell's on the measurement partition against always-long at the same geometry.\n\n")
    return "".join(out)


def _lab_records(f: Facts, ref) -> str:
    out = ["**Lab-level records.** "]
    c = f.classifier
    if c:
        shares = ", ".join(f"{k} {100 * float(v):.1f} %" for k, v in c["shares"].items())
        out.append(f"The classifier: {c['level']}-level on {c['index_name']}, short {c['short']}, long {c['long']}, band {c['band']}, "
                   f"frozen on the definition partition {_day(c['definition_start_day'])} to {_day(c['definition_end_day'])}, "
                   f"regime shares {shares}, persistence {_n(c['persistence'], 3)} ({ref(c)}). ")
    else:
        out.append("No classifier is frozen in this Register. ")
    latest_u: dict[str, dict] = {}
    for u in f.of("UniverseDeclared"):
        latest_u[u["name"]] = u
    if latest_u:
        out.append("The universes, each the latest record under its name: " + "; ".join(
            f"`{u['name']}` — {len(u['members'])} names, {u['instrument_class']}, {u['source_id']}; bias: {u['bias']} ({ref(u)})"
            for u in latest_u.values()) + ". ")
    latest_c: dict[str, dict] = {}
    for k in f.of("CalendarFrozen"):
        latest_c[k.get("universe") or ""] = k
    if latest_c:
        out.append("The calendar" + ("s" if len(latest_c) > 1 else "") + ": " + "; ".join(
            (f"[{k['universe']}] " if k.get("universe") else "") + f"{_day(k['start_day'])} to {_day(k['end_day'])}, definition to "
            f"{_day(k['definition_end_day'])}, measurement to {_day(k['measurement_end_day'])}, reserve after, split "
            f"{' / '.join(str(x) for x in k['split'])} ({ref(k)})" for k in latest_c.values()) + ". ")
    else:
        out.append("No calendar is frozen in this Register. ")
    return "".join(out) + "\n\n"


def _alpha(f: Facts, ref) -> str:
    spent = f.spent_by_axis
    looks = f.of("ReserveLook")
    moved = f.of("ReserveTransfer")
    reserve = ("The reserve was never looked at" if not looks else
               f"Reserve looks: {', '.join(x['hypothesis_id'] + ' (' + ref(x) + ')' for x in looks)}")
    if moved:
        reserve += "; drawn on: " + ", ".join(f"{_n(m['alpha_moved'], 4)} to {m['axis']} ({ref(m)})" for m in moved)
    if f.author:
        parts = [f"{_n(spent.get(a, 0.0), 4)} of the {_n(b, 2)} declared on {a}"
                 for a, b in sorted(f.author.axis_budgets.items(), key=lambda kv: (-kv[1], kv[0])) if b > 0]
        return (f"**Alpha.** Spent: {'; '.join(parts) or 'nothing'}; the reserve declared at {_n(f.author.reserve, 2)} "
                f"(the author's build, from the configuration the questions were stamped with). {reserve} (ADR-0006).\n\n")
    by = "; ".join(f"{_n(v, 4)} on {a}" for a, v in sorted(spent.items())) or "nothing"
    return (f"**Alpha.** Spent: {by}; the budgets are the author's configuration and are not shown on a plain build. "
            f"{reserve} (ADR-0006).\n\n")


def _archive(f: Facts) -> str:
    names = sorted({n for fd in f.findings for c in fd.consumed for n in c["names"]})
    consumed = f"the questions consumed {_name_list(names)}" if names else "no question consumed a name"
    if f.archive_present and f.series:
        srcs = sorted({s.source_id for s in f.series})
        return f"**The archive.** {_c(len(f.series))} names from {', '.join(srcs)}; {consumed}; no bars in the repository.\n\n"
    return f"**The archive.** Not read for this document; {consumed}; no bars are in the repository.\n\n"


def _controls() -> str:
    return ("**The controls.** Before every verdict the same pipeline refused a dead world and accepted a planted edge on both "
            "engines (S3, S10), and does so again on every build of the console (`docs/console.html`); they are not re-run "
            "here.\n\n")


def _established(f: Facts, ref) -> str:
    res = [fd for fd in f.findings if fd.resolved]
    head = "## 2. What the Register establishes\n\n"
    if not res:
        n_m = sum(1 for fd in f.findings if fd.measured)
        return head + (f"No verdict. {_c(len(f.findings))} question{'' if len(f.findings) == 1 else 's'} registered, "
                       f"{_c(n_m)} measured, none resolved: the programme stopped before a verdict, and the Register "
                       f"establishes nothing about any mechanism.\n\n")
    out = [head]
    for fd in res:
        v, r = fd.resolved, fd.registered
        ch = _checks(fd)
        refused = [c for c in CHECKS if ch[c].startswith("refused")]
        passed = [c for c in CHECKS if ch[c] == "passed"]
        mech = str(r["mechanism"]).strip()
        mech += "" if mech.endswith(".") else "."
        where = f"`{r['universe']}` ({_names(fd)})" if r.get("universe") else _names(fd)
        para = (f"**`{fd.id}` resolved {v['outcome']}** ({ref(v)}). {mech} On {where}, the "
                f"{v['partition']} partition {_span(fd)}, {fd.measured['engine'] if fd.measured else '—'}, seed {v['seed']}: "
                f"EV {_n(v['ev_net_r'], 3, True)} net R per trade over {_c(fd.measured['n']) if fd.measured else '—'} trades at "
                f"{v.get('cost_basis', 'unknown')} costs, {_n(v['trades_per_year'], 1)} a year, against a floor of "
                f"{_n(r['floor_ev_net_r'], 2)} net R and {_n(r['floor_min_trades_per_year'], 0)} a year declared at "
                f"registration ({ref(r)}). ")
        para += f"Passed: {', '.join(passed)}. " if passed else ""
        para += (f"Refused: {'; '.join(c + ' (' + ch[c].split('— ', 1)[1] + ')' for c in refused)}. " if refused
                 else "Every check passed. ")
        if fd.depth:
            para += "Eras: " + _eras(fd, ref) + ". "
        if fd.shrinkage:
            s = fd.shrinkage
            para += (f"From the survey: cell `{s['survey_cell']}` of {_c(s['screened_cells'])} screened; " + _shrink(fd, ref) + ". ")
        out.append(para + "\n\n")
    return "".join(out)


def _not_established(f: Facts) -> str:
    items = []
    looks = f.of("ReserveLook")
    items.append("- **Anything about the reserve.** " + ("Sealed, never looked at (ADR-0006): no reserve look is in the Register."
                                                          if not looks else f"{_c(len(looks))} reserve look(s) are recorded."))
    bases = sorted({str(fd.resolved.get("cost_basis", "unknown")) for fd in f.findings if fd.resolved})
    if bases and bases != ["measured"]:
        items.append(f"- **Anything about costs beyond the {' and '.join(bases)} model.** Every verdict is at "
                     f"{' or '.join(bases)} costs; at measured costs (M5.0) the numbers move.")
    if not f.of("ForwardWindowOpened"):
        at_forward = sorted({t["hypothesis_id"] for t in f.of("StrategyTransitioned") if t.get("to_state") == "FORWARD"})
        items.append("- **Obtainability in a forward window.** No forward window was opened"
                     + (f"; the Strategy of {', '.join('`' + h + '`' for h in at_forward)} reached `FORWARD` and stands there as a record "
                        f"(ADR-0044: the execution host is deferred)." if at_forward else "; no Strategy passed MEASURED."))
    screened = sum(int(s["cell_count"]) for s in f.surveys)
    from_survey = sum(1 for fd in f.findings if fd.registered.get("survey_cell"))
    if screened:
        items.append(f"- **{_c(screened - from_survey)} of the {_c(screened)} cells screened.** Registered from them: "
                     f"{_c(from_survey)}. A screen is not a verdict; a cell not registered has no standing and says nothing.")
    declared = {u["name"] for u in f.of("UniverseDeclared")}
    used = {fd.registered.get("universe") for fd in f.findings if fd.registered.get("universe")}
    unused = sorted(declared - used)
    if unused:
        items.append(f"- **The universes no question was registered on: {', '.join('`' + u + '`' for u in unused)}.** "
                     f"Declared and surveyed, not measured.")
    items.append("- *The rest of this section is the author's, written on adoption: what was not asked, and why.*")
    return "## 3. What is not established\n\n" + "\n".join(items) + "\n\n"


def _footer(f: Facts, stop: dict, ref, generated: str) -> str:
    repo = f" · repo `{_short(f.repo_sha)}`" if f.repo_sha else ""
    return (f"---\n\nGenerated by `python -m occams conclude` at {generated} from `{Path(f.register_path).name}`: "
            f"{_c(len(f.chain))} records, head `{_short(f.head)}`, stopping record `{ref(stop)}`{repo}. "
            f"A draft has no standing; adoption is the author's recorded act.\n")


def render(f: Facts, *, dated: str | None = None, generated: str | None = None) -> str:
    """The document, or ``ValueError`` when no stopping condition is a record."""
    stop = f.lab_closed or f.stopped
    if not stop:
        raise ValueError("no stopping condition is a Register record")
    if f.lab_closed and f.stopped:
        stop = max((f.lab_closed, f.stopped), key=lambda p: p.get("at", ""))
    ref = _refs(f)
    dated = dated or date.today().isoformat()
    generated = generated or f.generated
    return (_header(f, stop, ref, dated) + _scoreboard(f, ref) + _survey_layer(f, ref) + _lab_records(f, ref) + _alpha(f, ref)
            + _archive(f) + _controls() + _established(f, ref) + _not_established(f)
            + "## 4. The findings that outlast the questions\n\n" + AUTHORS + "\n\n"
            + "## 5. The decision\n\n" + AUTHORS + "\n\n"
            + "## 6. Was it worth doing?\n\n" + AUTHORS + "\n\n" + _footer(f, stop, ref, generated))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    p = argparse.ArgumentParser(prog="python -m occams conclude",
                                description="the conclusion from the Register, after the programme stopped and not before (M12.8)")
    p.add_argument("--register", required=True)
    p.add_argument("--out", required=True, help="a new file; an existing one is never overwritten")
    p.add_argument("--config", default=None, help="the author's configuration: budgets and the falsifier count, labelled")
    p.add_argument("--archive", default=None, help="archive directory; only its manifest is read")
    p.add_argument("--plateau-cells", type=int, default=PLATEAU_CELLS)
    a = p.parse_args(argv)
    author = cfg = None
    if a.config:
        from occams.config import ConfigRefused, load

        try:
            cfg = load(a.config)
        except ConfigRefused as e:
            print("REFUSED: the configuration does not load.")
            for r in e.reasons:
                print(f"  - {r}")
            return 2
        author = AuthorView.from_config(cfg)
    try:
        f = gather(Path(a.register), archive_dir=Path(a.archive) if a.archive else None, author=author, controls="none")
    except Exception as e:  # noqa: BLE001 — a tampered Register is a failure, not a report
        print(f"REFUSED: {type(e).__name__}: {e}")
        return 1
    from occams.register import Register

    stop = stopping_record(Register(Path(a.register)))
    if not stop:
        print("REFUSED: no stopping condition is a Register record — the conclusion is written after the programme stops, "
              "not before (M12.8). Where the three stand:")
        if cfg is not None:
            for line in conditions(cfg, Register(Path(a.register)), plateau_cells=a.plateau_cells).lines():
                print(f"  {line}")
        else:
            print(f"  falsifier: {f.falsifier_standing()} null mechanism verdicts; the closing count and the alpha budgets are "
                  f"the author's configuration — pass --config to see the room")
            print("  author's stop: none recorded")
        print("The falsifier's stop is the loop's (LabClosed); the other two are `python -m occams programme stop … --yes`.")
        return 1
    out = Path(a.out)
    if out.exists():
        print(f"REFUSED: {out} exists — a conclusion is superseded by a new file, never overwritten; choose another path")
        return 1
    text = render(f, generated=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"conclusion: {out} ({len(text):,} bytes, {'author' if author else 'plain'}'s build) — {Path(a.register).name}: "
          f"{len(f.chain)} records, {len(f.findings)} question(s), {len(f.resolved)} resolved, {len(f.surveys)} survey(s); "
          f"stopped: {describe(stop)}. A draft, the author's to adopt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
