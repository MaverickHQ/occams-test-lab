"""One static page from the facts (M11.4). No JavaScript, no external
assets, no network at view time: a page that needs a CDN to render has a
shelf life, and this one has to open in a decade. Generated, not live — a
page that shows whatever the store says when you load it cannot be cited,
diffed, or shown to disagree with itself later.

Colour encodes TRUST, not profit: refused, null, accepted, pending. There
is no equity curve and there will not be one.
"""

from __future__ import annotations

import html
from datetime import date, datetime

from pathlib import Path

from occams.console.facts import Facts, Finding, Series
from occams.stopping import describe as describe_stop

TITLE = "Occams research console"


# ---- small helpers ---------------------------------------------------------------

def esc(x) -> str:
    return html.escape(str(x), quote=True)


def short(sha: str | None, n: int = 12) -> str:
    return esc((sha or "")[:n])


def num(x, places: int = 4, sign: bool = False) -> str:
    if x is None:
        return "—"
    return f"{float(x):{'+' if sign else ''}.{places}f}"


def count(x) -> str:
    return f"{int(x):,}"


def day(ordinal) -> str:
    try:
        return date.fromordinal(int(ordinal)).isoformat()
    except (ValueError, OverflowError, TypeError):
        return str(ordinal)


def when(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return esc(iso)


def pill(kind: str, text: str) -> str:
    return f'<span class="pill {kind}">{esc(text)}</span>'


def state_pill(state: str) -> str:
    if state == "null":
        return pill("null", "Null")
    if state == "detectable":
        return pill("pass", "Detectable")
    if state == "measured":
        return pill("pending", "Measured")
    if state == "registered":
        return pill("pending", "Registered")
    if state == "registered, refused at measurement, unresolved":
        return pill("refused", "Refused at measurement · unresolved")
    return pill("null", state)


def kv(rows: list[tuple[str, str]]) -> str:
    return '<dl class="kv">' + "".join(f"<dt>{esc(k)}</dt><dd>{v}</dd>" for k, v in rows) + "</dl>"


# ---- figures ---------------------------------------------------------------------

def estimate_strip(ev: float, floor: float) -> str:
    """The winner cell's point estimate in net R against the floor declared
    before the run. One scale; every label names a value the strip reaches."""
    lo = min(-0.2, ev - 0.05)
    hi = max(0.3, floor + 0.1, ev + 0.05)
    x0, x1 = 40.0, 600.0

    def x(v: float) -> float:
        return x0 + (v - lo) / (hi - lo) * (x1 - x0)

    parts = [f'<svg viewBox="0 0 640 96" role="img" aria-label="winner cell EV {num(ev, 3, True)} net R against a declared floor of {num(floor, 2, True)} net R">',
             f'<line class="axis" x1="{x0}" y1="56" x2="{x1}" y2="56"/>',
             f'<text x="{x0}" y="86" text-anchor="middle">{num(lo, 2, True)}</text>',
             f'<text x="{x1}" y="86" text-anchor="middle">{num(hi, 2, True)}</text>']
    if lo < 0 < hi:
        parts.append(f'<line class="grid" x1="{x(0):.1f}" y1="30" x2="{x(0):.1f}" y2="70"/>'
                     f'<text x="{x(0):.1f}" y="86" text-anchor="middle">0</text>')
    parts.append(f'<line x1="{x(floor):.1f}" y1="26" x2="{x(floor):.1f}" y2="70" stroke="var(--brass)" stroke-width="2" stroke-dasharray="4 3"/>'
                 f'<text x="{x(floor):.1f}" y="18" text-anchor="middle" fill="var(--brass)">floor {num(floor, 2, True)}</text>')
    tone = "var(--verdigris)" if ev >= floor else "var(--slate)"
    parts.append(f'<circle cx="{x(ev):.1f}" cy="56" r="6" fill="{tone}" stroke="var(--card)" stroke-width="2"/>'
                 f'<text x="{x(ev):.1f}" y="42" text-anchor="middle" class="ink">{num(ev, 3, True)} net R</text></svg>')
    return "".join(parts)


def calendar(series: list[Series], bands: dict[str, tuple[int, int]]) -> str:
    """The partition calendar over the archive's common span, one calendar
    for every name (ADR-0005). Bands are three lightness steps of one hue
    with direct labels; every name starts at its first archived day."""
    cal = [s for s in series if s.calendar]
    if not cal:
        return ""
    lo, hi = min(s.first_day for s in cal), max(s.last_day for s in cal) + 1
    x0, x1 = 60.0, 880.0
    row_h, top = 34, 20
    plot_h = row_h * len(cal) + 10

    def x(d: int) -> float:
        return x0 + (d - lo) / max(1, hi - lo) * (x1 - x0)

    h = plot_h + top + 60
    out = [f'<svg viewBox="0 0 900 {h}" role="img" aria-label="partition calendar over the archive: {", ".join(s.name for s in cal)}">']
    tone = {"definition": "var(--band-1)", "measurement": "var(--band-2)", "reserve": "var(--band-3)"}
    for name in ("definition", "measurement", "reserve"):
        if name in bands:
            a, b = bands[name]
            a, b = max(a, lo), min(b, hi)
            if b > a:
                out.append(f'<rect x="{x(a):.1f}" y="{top}" width="{x(b) - x(a):.1f}" height="{plot_h}" fill="{tone[name]}"/>'
                           f'<text x="{(x(a) + x(b)) / 2:.1f}" y="{top - 6}" text-anchor="middle" class="ink">{name}</text>')
    for i, s in enumerate(cal):
        y = top + 14 + i * row_h
        out.append(f'<text x="8" y="{y + 10}" class="ink">{esc(s.name)}</text>'
                   f'<rect x="{x(s.first_day):.1f}" y="{y}" width="{max(2.0, x(s.last_day + 1) - x(s.first_day)):.1f}" height="12" rx="2" fill="var(--verdigris)"/>')
    ax = top + plot_h + 8
    out.append(f'<line class="axis" x1="{x0}" y1="{ax}" x2="{x1}" y2="{ax}"/>')
    y_lo, y_hi = date.fromordinal(lo).year, date.fromordinal(hi - 1).year
    ticks = []
    for step in (5, 1):   # five-year ticks on a long span, yearly on a short one
        start = ((y_lo + step - 1) // step) * step
        ticks = [date(y, 1, 1).toordinal() for y in range(start, y_hi + 1, step)]
        ticks = [d for d in ticks if lo < d < hi]
        if len(ticks) >= 2:
            break
    for d in ticks:
        out.append(f'<line class="grid" x1="{x(d):.1f}" y1="{ax}" x2="{x(d):.1f}" y2="{ax + 6}"/>'
                   f'<text x="{x(d):.1f}" y="{ax + 20}" text-anchor="middle">{date.fromordinal(d).year}</text>')
    out.append(f'<text x="{x0}" y="{ax + 40}" text-anchor="start">{day(lo)}</text>'
               f'<text x="{x1}" y="{ax + 40}" text-anchor="end">{day(hi - 1)}</text>')
    for b in sorted({b for a, b in bands.values() if lo < b < hi}):
        out.append(f'<text x="{x(b):.1f}" y="{ax + 40}" text-anchor="middle">{day(b)}</text>')
    out.append("</svg>")
    return "".join(out)


# ---- sections --------------------------------------------------------------------

def _stamp(f: Facts, others: tuple = ()) -> str:
    heads = " · ".join(f"P{i} {short(p.head)} ({count(len(p.chain))})" for i, p in enumerate([f, *others], 1)) if others else \
        f"{short(f.head)} · {count(len(f.chain))} records"
    cells = [("Register head" + ("s" if others else ""), f"{heads} · chain verified"),
             ("Repository", short(f.repo_sha) or "not a git checkout"),
             ("Engine sha at measurement", short(f.engine_sha) or "nothing measured yet"),
             ("Config sha", (short(f.config_sha) + (" · author's build" if f.author else " · as stamped in the Register")) if f.config_sha else "none stamped"),
             ("Generated", esc(f.generated)),
             ("Archive", f"{len(f.series)} names · {count(sum(s.bars for s in f.series))} bars" if f.archive_present else "no archive on this machine")]
    return '<div class="stamp">' + "".join(f'<div><div class="k">{esc(k)}</div><div class="v">{v}</div></div>' for k, v in cells) + "</div>"


def _build_note(f: Facts) -> str:
    if f.author:
        return ('<p class="note">Author\'s build: the balances, the falsifier count and the partition split come from the '
                'author\'s configuration. A plain build shows spend only. No money appears on this page and none can: '
                'the renderer reads the Register, which holds none by type, and the configuration reaches it without a field for money.</p>')
    return ('<p class="note">Plain build: no configuration was given, so balances and the falsifier count are not shown — '
            'spend is, from the Register alone. No money appears on this page and none can: the Register holds none by type.</p>')


def _controls(f: Facts) -> str:
    if not f.controls:
        return ('<h2 id="controls">1 · Controls</h2>'
                '<p class="note">Not run for this build. A page without its controls is a page a reader has no reason to trust; '
                'build again without <code>--controls none</code>.</p>')
    cards = []
    for o in f.controls:
        is_null = o.kind.startswith("null")
        ok = (not o.accepted) if is_null else o.accepted
        engine = "day-boxed" if "day_boxed" in o.kind else "synthetic"
        title = ("Null control" if is_null else "Signal control") + " · " + engine
        if ok:
            head_pill = pill("refused", "Refused") if is_null else pill("pass", "Accepted")
        else:
            head_pill = pill("stop", "STOP: guards")
        body = (f'<p>{"A dead world: random entry that loses the spread." if is_null else "A planted edge just above the declared floor."} '
                f'<strong>Winner EV {num(o.winner_ev, 4, True)} net R</strong> over N {count(o.n)} (required {count(o.required_n)}).</p>')
        if is_null:
            body += '<ul class="refusals">' + "".join(f"<li>{esc(r)}</li>" for r in o.refusals) + "</ul>"
            body += f'<p class="note">Checks that passed: {esc(", ".join(o.passes) or "none")}.</p>'
        else:
            body += (f'<p class="note">All five checks passed: {esc(", ".join(o.passes))}.</p>' if o.accepted else
                     '<ul class="refusals">' + "".join(f"<li>{esc(r)}</li>" for r in o.refusals) + "</ul>")
        cards.append(f'<div class="card"><div class="head"><h3>{esc(title)}</h3>{head_pill}</div>{body}'
                     f'<p class="note mono">{esc(o.hypothesis_id)} · spec {short(o.spec_hash)}</p></div>')
    verdict = ('<p class="note">Every null refused and every signal accepted: the instrument is calibrated for this build.</p>'
               if f.controls_ok else
               '<p class="stopline">A control failed. Nothing below should be read until the guards are fixed (S3, S10).</p>')
    return ('<h2 id="controls">1 · Controls</h2>'
            '<p>Run first, and shown first. Nothing below is worth reading until the instrument has demonstrated that it can find '
            'a planted edge and report nothing where there is none. Both controls run through the whole pipeline, register at '
            'alpha 0, and carry none of the author\'s numbers. They recompute on every build; they touch no market data, no key '
            'and no network.</p>'
            f'<div class="grid2">{"".join(cards)}</div>{verdict}')


def _position(f: Facts, sfx: str = "") -> str:
    from collections import Counter

    outcomes = Counter(r["outcome"] for r in f.resolved)
    spent = sum(f.spent_by_axis.values())
    standing = f.falsifier_standing()
    of = f' <span class="of">of {f.author.falsifier_count}</span>' if f.author else ""
    tiles = [(count(len(f.findings)), "questions registered"),
             (count(len(f.resolved)), "resolved · " + (" · ".join(f"{k} {v}" for k, v in sorted(outcomes.items())) or "none")),
             (num(spent, 2), "alpha spent, all axes"),
             (f"{standing}{of}", f"lab falsifier · {esc(f.author.falsifier_outcome if f.author else 'null')} verdicts"),
             (count(len(f.series)), "names archived"),
             (count(f.strategies_past_measured()), "strategies past MEASURED")]
    tiles_html = '<div class="tiles">' + "".join(f'<div class="tile"><div class="big">{big}</div><div class="lab">{lab}</div></div>' for big, lab in tiles) + "</div>"
    closed = ""
    if f.lab_closed:
        closed = (f'<p class="stopline">The lab closed: {count(f.lab_closed["falsifier_count"])} {esc(f.lab_closed["outcome"])} verdicts '
                  f'({esc(", ".join(f.lab_closed["verdicts"]))}). Nothing registers after this record.</p>')
    elif f.stopped:
        closed = f'<p class="stopline">The programme stopped: {esc(describe_stop(f.stopped))}. Nothing registers after this record.</p>'
    if f.author:
        rows = []
        for axis, budget in sorted(f.author.axis_budgets.items(), key=lambda kv_: (-kv_[1], kv_[0])):
            used = f.spent_by_axis.get(axis, 0.0)
            if budget <= 0:
                rows.append(f'<div class="bar zero"><span class="name">{esc(axis)}</span><div class="track"></div><span class="num">no budget</span></div>')
            else:
                width = max(0.0, min(100.0, used / budget * 100))
                rows.append(f'<div class="bar"><span class="name">{esc(axis)}</span><div class="track"><div class="fill" style="width:{width:.1f}%"></div></div>'
                            f'<span class="num">{num(used, 2)} of {num(budget, 2)}</span></div>')
        rows.append(f'<div class="bar"><span class="name">reserve</span><div class="track"></div><span class="num">{num(0.0, 2)} of {num(f.author.reserve, 2)}</span></div>')
        alpha = ('<h5>Alpha by axis · author\'s build</h5><div class="bars">' + "".join(rows) + "</div>"
                 '<p class="note">Spend is replayed from <code>AlphaSpent</code> records: rate × search-space size. The budgets are '
                 'configuration and appear only on the author\'s build. A zero-budget axis is not registrable (ADR-0017).</p>')
        fals = (f'<h5>The lab falsifier</h5><p>The lab closes when the first {f.author.falsifier_count} resolved mechanism verdicts are all '
                f'{esc(f.author.falsifier_outcome)}. {standing} of {f.author.falsifier_count} {"is" if standing == 1 else "are"} in. '
                'The count is the author\'s and was declared before the first question.</p>')
    else:
        rows = "".join(f'<tr><td>{esc(a)}</td><td class="num">{num(v, 4)}</td></tr>' for a, v in sorted(f.spent_by_axis.items())) or \
               '<tr><td colspan="2" class="note">nothing spent</td></tr>'
        alpha = ('<h5>Alpha spent by axis</h5><div class="wrap"><table><tr><th>Axis</th><th class="num">Spent</th></tr>' + rows + "</table></div>"
                 '<p class="note">Budgets are the author\'s configuration and are not shown on a plain build.</p>')
        fals = (f'<h5>The lab falsifier</h5><p>{standing} null mechanism verdict{"" if standing == 1 else "s"} resolved. '
                'The count at which the lab closes is the author\'s configuration and is not shown on a plain build.</p>')
    return f'<h2 id="position{sfx}">2 · Position</h2>' + tiles_html + closed + alpha + fals + _shrinkage_table(f)


def _shrinkage_table(f: Facts) -> str:
    """M12.6: every question registered from a survey, its screen beside its
    verdict. The screen selects; the table says by how much."""
    rows = [fd for fd in f.findings if fd.shrinkage]
    if not rows:
        return ""
    def n3(x):
        return num(x, 3, True) if x is not None else "—"
    trs = "".join(f'<tr><td class="mono">{esc(fd.id)}</td><td class="mono">{esc(fd.shrinkage["survey_cell"])}</td>'
                  f'<td class="num">{count(fd.shrinkage["screened_cells"])}</td><td class="num">{n3(fd.shrinkage["definition_ev_net"])}</td>'
                  f'<td class="num">{n3(fd.shrinkage["measured_ev_net"])}</td><td class="num">{n3(fd.shrinkage["ev_shrinkage"])}</td>'
                  f'<td class="num">{n3(fd.shrinkage["definition_margin_net"])}</td><td class="num">{n3(fd.shrinkage["measured_margin_net"])}</td>'
                  f'<td class="num">{n3(fd.shrinkage["margin_shrinkage"])}</td><td>{esc(fd.state)}</td></tr>' for fd in rows)
    return ('<h5>Shrinkage from screening</h5><div class="wrap"><table><tr><th>Question</th><th>Survey cell</th><th class="num">Screened</th>'
            '<th class="num">EV, definition</th><th class="num">EV, measured</th><th class="num">Δ EV</th><th class="num">Margin, definition</th>'
            '<th class="num">Margin, measured</th><th class="num">Δ margin</th><th>Verdict</th></tr>' + trs + '</table></div>'
            '<p class="note">Net R per trade. The definition numbers are the survey cell\'s (the calibration set, zero alpha); the measured '
            'ones are the winner cell\'s on the measurement partition against always-long at the same geometry. Every cell screened is '
            'counted beside every question registered from it (N6).</p>')


def _finding(fd: Finding) -> str:
    r, m, v = fd.registered, fd.measured, fd.resolved
    head = (f'<div class="head"><div><span class="mono">{esc(r["hypothesis_id"])} · {esc(r["tier"])} · {esc(r["axis"])}'
            f'{" · capability" if r.get("capability") else ""}</span>'
            f'<h3>{esc(r["mechanism"])}</h3></div>{state_pill(fd.state)}</div>')
    body = f'<p class="note">Falsifier: {esc(r["falsifier"])}</p>'
    if v:
        body += f'<figure>{estimate_strip(float(v["ev_net_r"]), float(r["floor_ev_net_r"]))}<figcaption>The winner cell\'s estimate in net R against the floor declared before the run.' + \
                (f' The interval lives in the archived path distribution, {count(fd.paths["draws"])} draws at <code>{short(fd.paths["sha"])}</code>.' if fd.paths else "") + \
                "</figcaption></figure>"
    rows = [("Declared floor", f'{num(r["floor_ev_net_r"], 2)} net R per trade · {num(r["floor_min_trades_per_year"], 0)} trades per year'),
            ("Power at registration", f'required {count(r["required_n"])} per cell · available {count(r["available_n"])}'),
            ("Search space", f'k = {count(r["search_space_size"])} · {num(r["alpha_spent"], 4)} alpha' +
             (f' · {num(fd.spent["rate"], 4)} per cell · {num(fd.spent["remaining_after"], 4)} remaining on {esc(fd.spent["axis"])} after' if fd.spent else ""))]
    if fd.consumed:
        c = fd.consumed[-1]
        rows.append(("Observations consumed", f'{esc(c["partition"])} partition · {day(c["start_day"])} to {day(c["end_day"])} · {esc(", ".join(c["names"]))}'))
    if m:
        rows.append(("Measured", f'{esc(m["engine"])} at {short(m["engine_sha"])} · n {count(m["n"])} · {esc(m["partition"])} partition · seed {esc(m["seed"])} · template {short(m["spec_hash"])}'))
    if v:
        rows.append(("Verdict", f'{esc(v["outcome"])} · EV {num(v["ev_net_r"], 4, True)} net R · {num(v["trades_per_year"], 1)} trades per year · {esc(v.get("cost_basis", "unknown"))} costs'))
        cell = ", ".join(str(i) for i in v.get("winner_cell", ()))
        rows.append(("Winner cell", f'[{esc(cell)}] · spec {short(v["spec_hash"])}' + (f' · family {short(v["family_hash"])} (the template measures, the winner trades)' if v.get("family_hash") else "")))
    if r.get("survey_cell"):   # M12.5: a question from a survey names its cell, and every cell screened is counted beside it (N6)
        rows.append(("From the survey", f'cell <code>{esc(r["survey_cell"])}</code> of results {short(r["survey_results_sha"])} · '
                                        f'{count(r.get("screened_cells", 0))} cells screened · universe {esc(r.get("universe") or "—")}'))
    if fd.shrinkage:
        sh = fd.shrinkage
        rows.append(("Shrinkage from screening",
                     f'definition EV {num(sh["definition_ev_net"], 3, True) if sh["definition_ev_net"] is not None else "—"} → measured '
                     f'{num(sh["measured_ev_net"], 3, True)} net R ({num(sh["ev_shrinkage"], 3, True) if sh["ev_shrinkage"] is not None else "—"}) · '
                     f'margin over always-long {num(sh["definition_margin_net"], 3, True) if sh["definition_margin_net"] is not None else "—"} → '
                     f'{num(sh["measured_margin_net"], 3, True) if sh["measured_margin_net"] is not None else "—"} '
                     f'({num(sh["margin_shrinkage"], 3, True) if sh["margin_shrinkage"] is not None else "—"}) · '
                     f'{count(sh["definition_trades"])} → {count(sh["measured_trades"])} trades'))
    if fd.depth:
        d = fd.depth
        eras = " · ".join(f'era {i + 1} {day(e["bounds"][0])}–{day(e["bounds"][1])}: {count(e["n"])} trades, EV '
                          f'{num(e["ev_net"], 3, True) if e["ev_net"] is not None else "—"}, without it '
                          f'{num(d["leave_one_era_out"][i], 3, True) if d["leave_one_era_out"][i] is not None else "—"}'
                          for i, e in enumerate(d["eras"]))
        rows.append(("Eras on the measurement partition", eras + " · a recorded diagnostic, not a gate (M12.6)"))
        by = ", ".join(f"{esc(k)} {count(v)}" for k, v in sorted(d["missed_by_name"].items(), key=lambda x: -x[1])[:8])
        rows.append(("Missed entries", (f'{count(d["missed"])} the fill auditor refused, not opened (ADR-0041)' + (f': {by}' if by else ""))
                     if d["missed"] else "none: every entry the winner booked was obtainable (ADR-0041)"))
    if r.get("supersedes"):
        rows.append(("Supersedes", esc(r["supersedes"])))
    if r.get("parent_id"):
        rows.append(("Parent", esc(r["parent_id"])))
    rows.append(("Registered by", esc(r["registered_by"] or "—") + (f' · config {short(r["config_sha"])}' if r.get("config_sha") else "")))
    body += kv(rows)
    if v and v["refusals"]:
        items = []
        evidence = {x["reason"]: x for x in fd.refusals}
        for reason in v["refusals"]:
            e = evidence.get(reason)
            ev_txt = ""
            if e and e.get("evidence"):
                ev_txt = ' <span class="note">' + esc("; ".join(f"{k} {vv}" for k, vv in e["evidence"].items())) + "</span>"
            items.append(f"<li>{esc(reason)}{ev_txt}</li>")
        body += '<h5>Refused at MEASURED → FORWARD by</h5><ul class="refusals">' + "".join(items) + "</ul>"
    elif v:
        body += '<p class="note">No refusal fired at MEASURED → FORWARD.</p>'
    states = " → ".join(t["to_state"] for t in fd.transitions)
    if states:
        body += f'<p class="note">Strategy: SPECIFIED → {esc(states)}.</p>'
    body += _rescored(fd)
    return f'<div class="card finding">{head}{body}</div>'


def _rescored(fd: Finding) -> str:
    """M16.19 (ADR-0047): what the corrected rules would have said, under the record and never in its place. The state
    pill, the estimate and every row above are the Register's; this block is the diagnostics store's and says so."""
    from occams.rescored import _check_line, one_line

    p = fd.rescored
    if not p:
        return ""
    md = lambda text: esc(text).replace("**", "")      # noqa: E731 — the report's sentences, without its emphasis marks
    stands = (f'The verdict above stands as reached: <strong>{esc(fd.resolved["outcome"])}</strong>.' if fd.resolved else
              "The record above stands as written: refused at measurement, unresolved.")
    out = ('<h5>Re-scored under the corrected rules — a diagnostic, not a verdict</h5>'
           f'<p class="note">{stands} The rules that judged it were later corrected, for records made after (ADR-0047). '
           'This is what they would have said, from <code>register/diagnostics.jsonl</code>; it changes no outcome, no alpha '
           'balance and no falsifier count. The whole reading is in <a href="RESCORE-2026-10.html">the re-score</a>.</p>')
    rows = [("Reading", f'<strong>{esc(one_line(p))}</strong>')]
    if p["reproduced"]:
        m = p["reproduction"]["measured"]
        rows.append(("Recreated first", f'exactly, at its stamped source {short(p["reproduction"]["source"])}: EV {num(m["ev_net_r"], 4, True)} '
                                        f'net R over {count(m["n"])} trades — the record\'s own numbers'))
        w = p["winner"]
        rows.append(("Winner under those rules", f'cell [{esc(", ".join(str(i) for i in w["cell"]))}] · n {count(w["n"])} · EV '
                                                 f'{num(w["ev_net_r"], 4, True)} · margin {num(w["margin_net_r"], 4, True)} over its passive '
                                                 f'alternative · {"the recorded winner" if w["is_the_recorded_winner"] else "not the recorded winner"}'))
    else:
        rows.append(("Not recreated", esc(p["reproduction"]["reason"])))
    rows.append(("Judged by", f'code {short(p["engine_sha"])} · content {esc(p["engine_code_sha"])} · {esc(", ".join(p["rules"]))} · '
                              f'annotates record #{esc(p["annotates_seq"])} ({short(p["annotates_sha"])})'))
    out += kv(rows)
    if p["checks"]:
        out += '<ul class="refusals">' + "".join(f"<li>{md(_check_line(c))}</li>" for c in p["checks"]) + "</ul>"
    return out


def _findings(f: Facts, sfx: str = "") -> str:
    n = len(f.findings)
    intro = ('<p>One card per registered question. A question shows as resolved only because a resolution record exists '
             'saying so. There is no equity curve on this page and there will not be one: every curve the closed programme '
             'drew came from an entry later proved unobtainable, and the curve looked fine throughout.</p>')
    cards = "".join(_finding(fd) for fd in reversed(f.findings)) if n else \
        '<p class="note">Nothing registered. The Register holds no question yet.</p>'
    prepared = ('<h5>Prepared, not registered</h5><p class="note">A prepare spends nothing and writes nothing, so nothing prepared '
                'appears here until it is registered. What the gates said about a prepared question is in the status log.</p>')
    return f'<h2 id="findings{sfx}">3 · Findings</h2>{intro}<div class="stack">{cards}</div>{prepared}'


def _surveys(f: Facts, sfx: str = "") -> str:
    """The Surveys section (M12.4): every ``SurveyRecorded`` record, with the
    page it was rendered to. A survey is breadth at zero alpha; nothing in
    it is a verdict, and the section says so."""
    if not f.surveys:
        return ""
    items = ""
    for s in f.surveys:
        href = f'surveys/{esc(s["grid_name"])}-seed{esc(str(s["seed"]))}.html'
        items += (f'<article class="card"><h3>{esc(s["grid_name"])} <span class="thin">· grid {short(s["grid_sha"])} · seed {esc(str(s["seed"]))}</span> '
                  f'{pill("note", "zero alpha")}</h3>'
                  f'<p>{count(s["cell_count"])} cells over {esc(", ".join(s["universes"]))} · results {short(s["results_sha"])} · '
                  f'classifier {short(s["classifier_hash"]) or "none"} · <a href="{href}">the survey page</a></p>'
                  f'<p class="sub">{esc(s.get("reason", ""))}</p></article>')
    return (f'<h2 id="surveys{sfx}">Surveys</h2><p>Breadth on the definition partition at zero alpha: every cell screened is counted '
            f'beside every question registered from it (N6). <strong>Nothing in a survey is a verdict.</strong></p><div class="stack">{items}</div>')


def _archive(f: Facts) -> str:
    if not f.archive_present:
        body = ('<p class="note">No archive on this machine. The Register still carries the spans the questions consumed and the '
                'definition the classifier was frozen on, so the calendar below is drawn from records alone where it can be.</p>')
    else:
        rows = "".join(f'<tr><td>{esc(s.name)}</td><td class="num">{count(s.bars)}</td><td>{esc(s.first_at[:10])}</td><td>{esc(s.last_at[:10])}</td>'
                       f'<td class="num">{count(s.actions)}</td><td>{esc(s.source_id)}</td><td class="mono">{short(s.sha)}</td>'
                       f'<td>{esc(s.requested_start or "—")} to {esc(s.requested_end or "—")}</td></tr>' for s in f.series)
        body = ('<div class="wrap"><table><tr><th>Name</th><th class="num">Bars</th><th>First bar</th><th>Last bar</th><th class="num">Actions</th>'
                '<th>Source</th><th>Content hash</th><th>Requested</th></tr>' + rows + "</table></div>"
                '<p class="note">Every series is content-addressed and carries the span that was requested beside the span that was '
                'returned, so a gap between them is visible rather than inferred. Raw bars never leave the archive and never reach this page.</p>')
    cal = calendar(f.series, f.bands())
    fig = (f'<figure>{cal}<figcaption>One calendar for every name: the partitions are cut on the archive\'s common span, so definition '
           'never overlaps measurement across names (ADR-0005). A name listed after a boundary simply has fewer bars in that partition.'
           + ("" if f.author else " Bands from the Register: the classifier\'s definition and the consumed measurement span.")
           + "</figcaption></figure>") if cal else ""
    clf = ""
    if f.classifier:
        c = f.classifier
        shares = " · ".join(f"{esc(k)} {float(v) * 100:.1f} %" for k, v in sorted(c["shares"].items()))
        clf = "<h5>The frozen classifier</h5>" + kv([
            ("Hash", short(c["frozen_hash"]) + (f' · supersedes {short(c["supersedes"])}' if c.get("supersedes") else "")),
            ("Level", f'{esc(c["level"])}, on {esc(c["index_name"])} · short {esc(c["short"])} · long {esc(c["long"])} · band {esc(c["band"])}'),
            ("Calibrated on", f'the definition partition only, {esc(c["definition_first_at"][:10])} to {esc(c["definition_last_at"][:10])} · seed {esc(c["seed"])}'),
            ("Regime shares", f'{shares} · persistence {num(c["persistence"], 3)}'),
            ("Names", esc(", ".join(c["names"]))),
        ] + ([("Reason for supersession", esc(c["reason"]))] if c.get("reason") else []))
    return ('<h2 id="archive">4 · Archive</h2>'
            '<p>What the questions were measured on: names, spans, counts and content hashes. Never the bars.</p>' + body + fig + clf)


def summarise(p: dict) -> str:
    t = p["type"]
    if t == "ClassifierFrozen":
        s = f'{esc(p["level"])}-level on {esc(p["index_name"])} over {esc(", ".join(p["names"]))} · frozen {short(p["frozen_hash"])}'
        return s + (f' · supersedes {short(p["supersedes"])}' if p.get("supersedes") else "")
    if t == "AlphaSpent":
        return f'{esc(p["hypothesis_id"])} · {esc(p["axis"])} · {num(p["rate"], 4)} × {count(p["search_space_size"])} = {num(p["alpha_spent"], 4)} · {num(p["remaining_after"], 4)} remaining after'
    if t == "HypothesisRegistered":
        return (f'{esc(p["hypothesis_id"])} · {esc(p["tier"])} · {esc(p["axis"])} · floor ({num(p["floor_ev_net_r"], 2)} R, {num(p["floor_min_trades_per_year"], 0)}/yr) '
                f'· required {count(p["required_n"])} · available {count(p["available_n"])} · by {esc(p["registered_by"] or "—")}')
    if t == "ObservationsConsumed":
        return f'{esc(p["hypothesis_id"])} · {esc(p["partition"])} partition · {esc(", ".join(p["names"]))} · {day(p["start_day"])} to {day(p["end_day"])}'
    if t == "HypothesisMeasured":
        return f'{esc(p["hypothesis_id"])} · {esc(p["engine"])} · n {count(p["n"])} · k {count(p["search_space_size"])} · seed {esc(p["seed"])} · template {short(p["spec_hash"])}'
    if t == "StrategyTransitioned":
        return f'{short(p["spec_hash"])} · {esc(p["from_state"])} → {esc(p["to_state"])}'
    if t == "PathsArchived":
        return f'{esc(p["hypothesis_id"])} · {count(p["draws"])} draws over {count(p["trades"])} trades · {short(p["spec_hash"])} → {short(p["sha"])}'
    if t == "HypothesisResolved":
        cell = ", ".join(str(i) for i in p.get("winner_cell", ()))
        return (f'{esc(p["hypothesis_id"])} · <strong>{esc(p["outcome"])}</strong> · EV {num(p["ev_net_r"], 4, True)} net R · {num(p["trades_per_year"], 1)}/yr '
                f'· {esc(p.get("cost_basis", "unknown"))} · winner [{esc(cell)}] · {len(p["refusals"])} refusal{"" if len(p["refusals"]) == 1 else "s"}')
    if t == "RefusalRecorded":
        return f'{esc(p.get("hypothesis_id") or "—")} · refused at {esc(p["transition"])}: {esc(p["reason"])}'
    if t == "GuardEvidence":
        seen = p.get("evidence") or {}
        key = next((k for k in ("p_null", "p_baseline", "gap", "ev_net_r", "weakest_score_without") if k in seen), None)
        shown = f' · {esc(key.replace("_", " "))} {num(seen[key], 4)}' if key and isinstance(seen[key], (int, float)) else ""
        return (f'{esc(p["hypothesis_id"])} · {esc(p["check"].replace("_", " "))} · <strong>{"passed" if p["passed"] else "refused"}</strong>'
                f'{shown} · {short(p["spec_hash"])}')
    if t == "UniverseDeclared":
        return (f'{esc(p["name"])} · {len(p["members"])} names · {esc(p["instrument_class"])} · {esc(p["source_id"])} · '
                f'{esc(p["rule"][:90])} · bias: {esc(p["bias"][:60])}')
    if t == "CalendarFrozen":
        return ((f'[{esc(p["universe"])}] ' if p.get("universe") else "") +
                f'calendar {day(p["start_day"])} to {day(p["end_day"])} · definition to {day(p["definition_end_day"])} · '
                f'measurement to {day(p["measurement_end_day"])} · {esc(", ".join(p["names"]))}'
                + (f' · supersedes {esc(p["supersedes"])}' if p.get("supersedes") else ""))
    if t == "LabClosed":
        return f'lab closed · {count(p["falsifier_count"])} {esc(p["outcome"])} verdicts · {esc(", ".join(p["verdicts"]))}'
    if t == "ProgrammeStopped":
        return (f'programme stopped · {esc(p["kind"].replace("_", " "))} · by {esc(p["by"])} · {esc(p["reason"][:120])} · '
                f'{count(p["questions"])} questions, {count(p["surveys"])} surveys, {len(p["verdicts"])} verdicts')
    if t == "SurveyRecorded":
        return (f'survey {esc(p["grid_name"])} · grid {short(p["grid_sha"])} · {count(p["cell_count"])} cells · '
                f'{esc(", ".join(p["universes"]))} · results {short(p["results_sha"])} · seed {esc(str(p["seed"]))} · zero alpha')
    if t == "EraDecomposition":
        return (f'{esc(p["hypothesis_id"])} · winner {short(p["spec_hash"])} · {len(p["eras"])} eras on {esc(p["partition"])}: '
                + " / ".join(f'{count(e["n"])} at {num(e["ev_net"], 3, True) if e["ev_net"] is not None else "—"}' for e in p["eras"])
                + f' · {count(p["missed"])} missed · seed {esc(str(p["seed"]))} · a diagnostic, not a gate')
    if t == "Shrinkage":
        return (f'{esc(p["hypothesis_id"])} · cell {esc(p["survey_cell"])} of {count(p["screened_cells"])} screened · EV '
                f'{num(p["definition_ev_net"], 3, True) if p["definition_ev_net"] is not None else "—"} → {num(p["measured_ev_net"], 3, True)} · margin '
                f'{num(p["definition_margin_net"], 3, True) if p["definition_margin_net"] is not None else "—"} → '
                f'{num(p["measured_margin_net"], 3, True) if p["measured_margin_net"] is not None else "—"}')
    if t == "ReserveLook":
        return f'{esc(p["hypothesis_id"])} · reserve look at {short(p["spec_hash"])}'
    if t == "ForwardWindowOpened":
        return f'{short(p["spec_hash"])} · {count(p["min_trades"])} trades or {count(p["max_duration_days"])} days · {esc(p["venue_kind"])}'
    if t == "ForwardWindowResolved":
        return f'{short(p["spec_hash"])} · {esc(p["outcome"])} · {esc(p["statement"])}'
    skip = {"type", "at"}
    return esc(" · ".join(f"{k} {v}" for k, v in p.items() if k not in skip)[:200])


def _register(f: Facts, sfx: str = "") -> str:
    rows = "".join(f'<tr><td class="num">{line["seq"]}</td><td>{esc(line["payload"]["type"])}</td><td class="mono">{when(line["payload"].get("at", ""))}</td>'
                   f'<td>{summarise(line["payload"])}</td><td class="mono">{short(line["sha"])}</td></tr>' for line in f.chain)
    if not rows:
        rows = '<tr><td colspan="5" class="note">empty</td></tr>'
    from collections import Counter

    kinds = Counter(p["type"] for p in f.records)
    tally = " · ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
    return (f'<h2 id="register{sfx}">5 · The Register</h2>'
            '<p>Every record, in chain order, each carrying the hash of the one before it. A tampered Register fails the build; '
            'this page is not rendered from a chain that does not verify.</p>'
            '<div class="wrap"><table><tr><th class="num">#</th><th>Record</th><th>At (UTC)</th><th>What it says</th><th>Hash</th></tr>' + rows + "</table></div>"
            f'<p class="note">{esc(tally) or "no records"}.</p>')


def _footer(f: Facts) -> str:
    return ('<footer><p><strong>What this page is not.</strong> It is not live: a page that shows whatever the store says when you '
            'load it cannot be cited or shown to disagree with itself later. It is not a dashboard of profit: colour here encodes '
            'trust. It is not public until the publication gate (R7, M11.7): it is built locally and committed, never served.</p>'
            f'<p class="mono">generated {esc(f.generated)} · register head {short(f.head)} · repository {short(f.repo_sha) or "—"}</p></footer>')


# ---- the page --------------------------------------------------------------------

CSS = """
:root{color-scheme:light;
  --bg:#F7F6F2;--card:#FFFFFF;--ink:#182220;--sub:#64757A;--line:#D5DCDA;--rule:#E6EBE9;
  --verdigris:#1E7A6A;--brass:#A3700C;--rust:#A23A1E;--slate:#5F7175;
  --verdigris-band:#1E7A6A1A;--brass-band:#A3700C1A;--rust-band:#A23A1E1A;--slate-band:#5F717514;
  --band-1:#1E7A6A2E;--band-2:#1E7A6A66;--band-3:#1E7A6AB3;--shadow:0 1px 2px #18222012;
  --serif:Charter,"Iowan Old Style","Source Serif Pro",Georgia,"Times New Roman",serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;
  --bg:#121A1B;--card:#192425;--ink:#E4ECEA;--sub:#93A6A8;--line:#2B3A3B;--rule:#22302F;
  --verdigris:#5CB5A4;--brass:#D9A23A;--rust:#D97A55;--slate:#93A6A8;
  --verdigris-band:#5CB5A424;--brass-band:#D9A23A24;--rust-band:#D97A5524;--slate-band:#93A6A81C;
  --band-1:#5CB5A433;--band-2:#5CB5A46B;--band-3:#5CB5A4B8;--shadow:none}}
:root[data-theme="dark"]{color-scheme:dark;
  --bg:#121A1B;--card:#192425;--ink:#E4ECEA;--sub:#93A6A8;--line:#2B3A3B;--rule:#22302F;
  --verdigris:#5CB5A4;--brass:#D9A23A;--rust:#D97A55;--slate:#93A6A8;
  --verdigris-band:#5CB5A424;--brass-band:#D9A23A24;--rust-band:#D97A5524;--slate-band:#93A6A81C;
  --band-1:#5CB5A433;--band-2:#5CB5A46B;--band-3:#5CB5A4B8;--shadow:none}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--serif);font-variant-numeric:tabular-nums}
main{max-width:66rem;margin:0 auto;padding:2.25rem 1.25rem 5rem}
h1{font-size:2rem;line-height:1.15;letter-spacing:-.01em;margin:0 0 .4rem;font-weight:600}
h1 .thin{font-weight:400;color:var(--sub)}
h2{font-size:1.35rem;line-height:1.2;margin:3.25rem 0 .6rem;padding-bottom:.4rem;border-bottom:1px solid var(--line);scroll-margin-top:4rem}
h2.programme{font-size:1.6rem;margin-top:4rem;border-bottom:2px solid var(--ink);display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap}
h2 .thin{font-weight:400;color:var(--sub);font-size:.8em}
h3{font-size:1.05rem;line-height:1.3;margin:0 0 .35rem}
h5{font-size:.72rem;line-height:1.2;text-transform:uppercase;letter-spacing:.08em;color:var(--sub);margin:1.4rem 0 .35rem;font-weight:600}
p{margin:.55rem 0;max-width:46rem}
.lede{color:var(--sub);margin:.2rem 0 1rem}
code,.mono{font-family:var(--mono);font-size:.86em}
.stamp{display:grid;grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));gap:.9rem 1.5rem;margin:1.2rem 0 0;padding:1rem 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.stamp div{min-width:0}
.stamp .k{font-size:.68rem;line-height:1.2;text-transform:uppercase;letter-spacing:.08em;color:var(--sub);font-weight:600}
.stamp .v{font-family:var(--mono);font-size:.84rem;overflow-wrap:anywhere}
nav.toc{position:sticky;top:0;z-index:2;background:var(--bg);display:flex;flex-wrap:wrap;gap:.45rem;padding:.8rem 0;margin-top:1rem;border-bottom:1px solid var(--rule)}
nav.toc a{text-decoration:none;font-size:.82rem;padding:.25rem .7rem;border:1px solid var(--line);border-radius:999px;color:var(--ink);background:var(--card)}
nav.toc a:hover,nav.toc a:focus-visible{border-color:var(--ink);outline:none}
.pill{display:inline-flex;align-items:center;gap:.35rem;font:600 .68rem/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;padding:.3rem .55rem;border-radius:4px;border:1px solid currentColor;white-space:nowrap}
.pill::before{content:"";width:.5rem;height:.5rem;border-radius:999px;background:currentColor;flex:none}
.pass{color:var(--verdigris);background:var(--verdigris-band)}
.refused,.stop{color:var(--rust);background:var(--rust-band)}
.null{color:var(--slate);background:var(--slate-band)}
.pending{color:var(--brass);background:var(--brass-band)}
.stopline{border-left:3px solid var(--rust);padding:.3rem .8rem;background:var(--rust-band);border-radius:0 6px 6px 0;font-weight:600}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(19rem,1fr));gap:1rem;margin-top:1rem}
.stack{display:grid;gap:1rem;margin-top:1rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:1rem 1.15rem;box-shadow:var(--shadow);min-width:0}
.card .head{display:flex;justify-content:space-between;align-items:flex-start;gap:.75rem}
.card p{font-size:.95rem}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:.25rem 1rem;font-size:.9rem;margin:.6rem 0 0}
.kv dt{color:var(--sub);margin:0}
.kv dd{margin:0;font-family:var(--mono);font-size:.84rem;overflow-wrap:anywhere}
ul.refusals{margin:.5rem 0 0;padding-left:1.1rem;font-size:.93rem}
ul.refusals li{margin:.2rem 0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr));gap:.9rem;margin-top:1rem}
.tile{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.85rem 1rem}
.tile .big{font:600 1.9rem/1.1 var(--mono);letter-spacing:-.02em}
.tile .big .of{font-size:1rem;color:var(--sub);font-weight:400}
.tile .lab{font-size:.82rem;color:var(--sub);margin-top:.25rem}
.bars{margin-top:1rem;display:grid;gap:.65rem;max-width:46rem}
.bar{display:grid;grid-template-columns:8.5rem 1fr 7rem;align-items:center;gap:.8rem;font-size:.9rem}
.bar .track{height:12px;background:var(--rule);border-radius:3px;position:relative;overflow:hidden}
.bar .fill{position:absolute;inset:0 auto 0 0;background:var(--brass);border-radius:3px 0 0 3px}
.bar .num{font-family:var(--mono);font-size:.82rem;color:var(--sub);text-align:right}
.bar.zero .track{background:repeating-linear-gradient(135deg,var(--rule) 0 4px,transparent 4px 8px)}
figure{margin:1rem 0 0;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.9rem 1rem;overflow-x:auto}
figure svg{display:block;width:100%;height:auto;min-width:36rem}
figcaption{font-size:.84rem;color:var(--sub);margin-top:.5rem;max-width:46rem}
svg text{font-family:var(--mono);font-size:11px;fill:var(--sub)}
svg .ink{fill:var(--ink)}
svg .grid{stroke:var(--rule);stroke-width:1}
svg .axis{stroke:var(--line);stroke-width:1}
table{width:100%;border-collapse:collapse;font-size:.88rem;margin-top:.8rem}
th{font-size:.68rem;line-height:1.2;text-transform:uppercase;letter-spacing:.08em;color:var(--sub);text-align:left;padding:.45rem .6rem;border-bottom:1px solid var(--line);font-weight:600}
td{padding:.45rem .6rem;border-bottom:1px solid var(--rule);vertical-align:top}
td.mono,th.num,td.num{font-family:var(--mono);font-size:.8rem}
td.num,th.num{text-align:right}
.wrap{overflow-x:auto}
.note{font-size:.88rem;color:var(--sub)}
footer{margin-top:4rem;padding-top:1rem;border-top:1px solid var(--line);font-size:.88rem;color:var(--sub)}
footer p{max-width:46rem}
@media (max-width:640px){.bar{grid-template-columns:6.5rem 1fr 5rem}.kv{grid-template-columns:1fr}}
"""


def _programme_head(f: Facts, n: int) -> str:
    """A programme's banner when more than one shares the page (M12.0)."""
    name = esc(Path(f.register_path).name)
    state = pill("refused", "Closed") if f.lab_closed else pill("refused", "Stopped") if f.stopped else pill("pass", "Open")
    return (f'<h2 id="programme{n}" class="programme">Programme {n} <span class="thin">· {name} · {count(len(f.chain))} records · '
            f'head {short(f.head)}</span> {state}</h2>')


def render(f: Facts, others: tuple = ()) -> str:
    progs = [f, *others]
    multi = len(progs) > 1
    nav_items = ['<a href="#controls">Controls</a>']
    for i, p in enumerate(progs, 1):
        sfx = f"-{i}" if multi else ""
        label = f"P{i} " if multi else ""
        nav_items += [f'<a href="#position{sfx}">{label}Position</a>', f'<a href="#findings{sfx}">{label}Findings ({len(p.findings)})</a>']
        if p.surveys:
            nav_items.append(f'<a href="#surveys{sfx}">{label}Surveys ({len(p.surveys)})</a>')
        nav_items.append(f'<a href="#register{sfx}">{label}Register</a>')
    nav_items.append('<a href="#archive">Archive</a>')
    nav = '<nav class="toc" aria-label="Sections">' + "".join(nav_items) + "</nav>"
    head = ('<h1>Occams <span class="thin">research console</span></h1>'
            '<p class="lede">A falsifiable record: what was asked, what was measured, and what the instrument was doing when it '
            'measured it. Rendered from the Register. <strong>A dated artifact, not a live view.</strong></p>')
    body = ""
    for i, p in enumerate(progs, 1):
        sfx = f"-{i}" if multi else ""
        body += (_programme_head(p, i) if multi else "") + _position(p, sfx) + _findings(p, sfx) + _surveys(p, sfx) + _register(p, sfx)
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{esc(TITLE)}</title><style>{CSS}</style></head><body><main>"
            + head + _stamp(f, others) + _build_note(f) + nav
            + _controls(f) + body + _archive(f) + _footer(f)
            + "</main></body></html>\n")
