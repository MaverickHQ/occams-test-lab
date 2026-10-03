"""The survey page (M12.4): one static file per survey in the console's
shape — no script, no network, both themes — so a reader with no code can
say, for any cell, what was asked, on what, what it showed against random
entry, whether it held across eras, and whether it is registrable.

    python -m occams survey page GRID --out DIR [--register PATH] [--config PATH] [--html PATH]

Colour encodes *trust*, never profit: a cell is **held** when its EV and
its margin over the always-long baseline at the same geometry are
positive, positive in every era of the definition partition, positive
with every name held out, over at least a hundred trades; **positive**
when EV and margin are positive over a hundred trades; **margin** when
only the margin is; **refused** when the run was refused by name. An
entry the fill auditor refused is a *missed* trade, counted beside the
trade count (ADR-0041), never a refusal of the cell. With a
Register the page names the ``SurveyRecorded`` record it renders; with a
config it prices what registering a cell would cost in alpha — the axis
rate times the family's sweep — which is the accountant's arithmetic,
never a recommendation. Nothing on the page is a verdict.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, UTC
from pathlib import Path

from occams.console.render import CSS, count, esc, num, pill, short
from occams.survey.grid import Grid, GridRefused, load as load_grid
from occams.survey.run import INDEX_FILE

TIERS = ("held", "positive", "margin", "none", "refused")
TIER_LABEL = {"held": "held", "positive": "positive", "margin": "margin", "none": "—", "refused": "refused"}
TOP_ROWS = 20
CARDS = 4
MIN_TRADES = 100

PAGE_CSS = """
table.matrix td,table.matrix th{text-align:center}
table.matrix td.t-held{background:var(--band-3);color:#fff;font-weight:600}
table.matrix td.t-positive{background:var(--band-2)}
table.matrix td.t-margin{background:var(--band-1)}
table.matrix td.t-none{color:var(--sub)}
table.matrix td.t-refused{background:var(--rust-band);color:var(--rust)}
table.matrix td small{display:block;font-size:12px;opacity:.85}
.eras{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0}
.eras div{border:1px solid var(--line);border-radius:6px;padding:6px 8px;font-size:14px}
.eras .neg{border-color:var(--rust);color:var(--rust)}
.eras .pos{border-color:var(--verdigris)}
.hyp{font-style:italic;margin:6px 0 10px}
.legend span{display:inline-block;margin-right:12px;padding:1px 8px;border-radius:4px;font-size:13px}
"""


def tier_of(r: dict) -> str:
    if r.get("refused"):
        return "refused"
    ev, m, n = r.get("ev_net"), r.get("margin_net"), r.get("trades") or 0
    if ev is None or m is None:
        return "none"
    eras = [e["ev_net"] if isinstance(e, dict) else e for e in (r.get("eras") or [])]   # index rows carry numbers, cell files dicts
    loo = r.get("leave_one_name_out_min")
    if ev > 0 and m > 0 and n >= MIN_TRADES and eras and all(e is not None and e > 0 for e in eras) and loo is not None and loo > 0:
        return "held"
    if ev > 0 and m > 0 and n >= MIN_TRADES:
        return "positive"
    if m > 0:
        return "margin"
    return "none"


def mechanism_key(r: dict) -> str:
    p = r["params"] if isinstance(r["params"], dict) else dict(r["params"])
    return f"{r['kind']}({', '.join(f'{k}={float(v):g}' for k, v in sorted(p.items()))}) · {r['order']}"


def family_of(grid: Grid, r: dict):
    p = r["params"] if isinstance(r["params"], dict) else dict(r["params"])
    for f in grid.families:
        if (f.universe == r["universe"] and f.regime == r["regime"] and f.kind.value == r["kind"] and dict(f.params) == {k: float(v) for k, v in p.items()}
                and f.order.value == r["order"] and f.horizon.value == r["horizon"] and f.stop_kind.value == r["stop_kind"]
                and bool(f.targets) == bool(r.get("target"))):
            return f
    return None


def geometry(r: dict) -> str:
    t = "no target" if not r.get("target") else f"target {float(r['target']):g}R"
    return f"{r['horizon']} · hold {float(r['hold']):g} · stop {r['stop_kind']} {float(r['stop']):g} · {t}"


def _ev(x) -> str:
    return "—" if x is None else num(x, 3, sign=True)


# ---- sections ------------------------------------------------------------------

def _head(index: dict, grid: Grid, record: dict | None) -> str:
    plat = index.get("platform", {})
    rec = (f'Register record <strong>#{record["seq"]}</strong> (<code>SurveyRecorded</code>)' if record
           else "not yet a Register record")
    return (f'<h1>Survey <span class="thin">{esc(index["grid"])} · seed {esc(str(index["seed"]))}</span></h1>'
            f'<p class="lede">Every cell of the grid on the <strong>definition partition only</strong>, at zero alpha, '
            f'against the always-long baseline at the same geometry. Colour is trust, never profit. '
            f'<strong>Nothing here is a verdict</strong>; a cell becomes a question only by the author\'s registration (M12.5).</p>'
            f'<p class="mono">grid {short(index["grid_sha"])} · results {short(index["results_sha"])} · {count(index["cell_count"])} cells · '
            f'classifier {short(index.get("classifier_hash") or "") or "none"} · computed on {esc(plat.get("machine", "?"))} {esc(plat.get("system", ""))} '
            f'python {esc(plat.get("python", "?"))} numpy {esc(plat.get("numpy", "?"))} · {rec}</p>')


def _grid_in_words(grid: Grid) -> str:
    mech = "".join(f"<li><code>{esc(k.value)}</code> as a {esc(o.value)} order, {len(ps)} parameterisation{'s' if len(ps) != 1 else ''}: "
                   + esc("; ".join(", ".join(f"{a}={b:g}" for a, b in p) for p in ps)) + f" · horizons {esc(', '.join(h.value for h in hs))}</li>"
                   for k, o, hs, ps in grid.mechanisms)
    unis = "".join(f"<li><strong>{esc(n)}</strong> — {esc(s)}; regime read on {esc(ri)}</li>" for n, s, ri in grid.universes)
    stops = " · ".join(f"{k.value} {', '.join(f'{x:g}' for x in v)}" + (f" over {lb} bars" if lb else "") for k, v, lb in grid.stops)
    hh = dict(grid.horizon_holds)
    ht = dict(grid.horizon_targets)
    return (f'<h2 id="grid">1 · The grid in words</h2>'
            f'<p><strong>{esc(grid.name)}</strong>, declared {esc(grid.declared_on)}, sha <code>{short(grid.sha)}</code>; '
            f'{count(len(grid.families))} families, {count(grid.count)} cells. A family is the cells that share everything but the swept geometry: '
            f'the sweep a registered question would carry.</p>'
            f'<p>Mechanisms — every kind on the closed entry enum with a mechanism sentence:</p><ul>{mech}</ul>'
            f'<p>Regimes: {esc(", ".join(grid.regimes))} (none is no gate; the rest read one frozen classifier). '
            f'Holds {esc(", ".join(f"{x:g}" for x in grid.holds))}'
            + "".join(f"; {esc(h)}: holds {esc(', '.join(f'{x:g}' for x in v))}" + (f", targets {esc(', '.join(f'{t:g}R' for t in ht[h]))}" if h in ht else "") for h, v in hh.items())
            + f'. Stops {esc(stops)}. Targets {esc(", ".join("none" if t == 0 else f"{t:g}R" for t in grid.targets))}.</p>'
            f'<p>Universes, each a Register record with its calendar frozen:</p><ul>{unis}</ul>')


def _legend() -> str:
    return ('<p class="legend"><span class="t-held" style="background:var(--band-3);color:#fff">held</span> EV and margin positive, '
            f'positive in every era and with every name held out, ≥{MIN_TRADES} trades · '
            '<span style="background:var(--band-2)">positive</span> EV and margin positive over ≥100 trades · '
            '<span style="background:var(--band-1)">margin</span> only the margin over always-long is positive · '
            '<span style="background:var(--rust-band);color:var(--rust)">refused</span> the run was refused by name — '
            'a family with no auditor, or the whole-run refusal that preceded ADR-0041</p>')


def _matrix(grid: Grid, rows: list[dict]) -> str:
    unis = [u for u, _s, _r in grid.universes]
    mechs = []
    for k, o, _hs, ps in grid.mechanisms:
        for p in ps:
            mechs.append(f"{k.value}({', '.join(f'{a}={b:g}' for a, b in sorted(p))}) · {o.value}")
    best: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (mechanism_key(r), r["universe"])
        t = tier_of(r)
        b = best.setdefault(key, {"tier": "refused", "held": 0, "margin": None, "n": 0, "refused": 0})
        b["n"] += 1
        if t == "refused":
            b["refused"] += 1
        else:
            if TIERS.index(t) < TIERS.index(b["tier"]) or b["tier"] == "refused":
                b["tier"] = t
            if t == "held":
                b["held"] += 1
            if r.get("margin_net") is not None and (b["margin"] is None or r["margin_net"] > b["margin"]):
                b["margin"] = r["margin_net"]
    head = "".join(f"<th>{esc(u)}</th>" for u in unis)
    body = ""
    for m in mechs:
        cells = ""
        for u in unis:
            b = best.get((m, u))
            if not b:
                cells += '<td class="t-none">—</td>'
                continue
            if b["n"] == b["refused"]:
                cells += f'<td class="t-refused">refused<small>{count(b["refused"])} cells</small></td>'
                continue
            label = TIER_LABEL[b["tier"]]
            cells += (f'<td class="t-{b["tier"]}">{esc(label)}<small>best margin {_ev(b["margin"])} · {count(b["held"])} held'
                      + (f' · {count(b["refused"])} refused' if b["refused"] else "") + '</small></td>')
        body += f"<tr><th>{esc(m)}</th>{cells}</tr>"
    return (f'<h2 id="matrix">2 · Mechanism × universe, by trust</h2>{_legend()}'
            f'<div class="scroll"><table class="matrix"><thead><tr><th>mechanism · order</th>{head}</tr></thead><tbody>{body}</tbody></table></div>'
            f'<p class="sub">Each cell is the best tier the mechanism reached in that universe across regimes and geometry, its best margin over '
            f'always-long in net R, and how many of its cells are held. Refused means the fill auditor (M5.5) refused every cell.</p>')


def _refusals(rows: list[dict], u: str) -> str:
    rs = [r for r in rows if r["universe"] == u and r.get("refused")]
    bs = [r for r in rows if r["universe"] == u and r.get("baseline_refused")]
    out = ""
    if rs or bs:
        by: dict[str, int] = {}
        for r in rs:
            why = r["refused"].split(":")[0]
            by[why] = by.get(why, 0) + 1
        fam = ", ".join(f"{esc(k)} {count(v)}" for k, v in sorted(by.items(), key=lambda x: -x[1]))
        out += (f'<p class="sub"><strong>Refused by name:</strong> {count(len(rs))} cells ({fam}); '
                f'{count(len(bs))} cells have a refused baseline and therefore no margin.</p>')
    return out + _missed(rows, u)


def _missed(rows: list[dict], u: str) -> str:
    """ADR-0041: the entries the fill auditor refused, counted by name — a
    missed trade is not a refusal of the cell."""
    ms = [r for r in rows if r["universe"] == u and r.get("missed")]
    bm = sum(r.get("baseline_missed") or 0 for r in rows if r["universe"] == u)
    if not ms and not bm:
        return ""
    by: dict[str, int] = {}
    for r in ms:
        for n, k in (r.get("missed_by_name") or {}).items():
            by[n] = by.get(n, 0) + int(k)
    names = ", ".join(f"{esc(n)} {count(k)}" for n, k in sorted(by.items(), key=lambda x: -x[1])[:8])
    return (f'<p class="sub"><strong>Missed trades:</strong> the fill auditor refused an entry in {count(len(ms))} cells, '
            f'{count(sum(r["missed"] for r in ms))} entries in all, not opened and counted beside the trade count (ADR-0041)'
            + (f' — by name, {names}' if names else "") + (f'; {count(bm)} in the always-long baselines' if bm else "") + '.</p>')


def _universe_table(rows: list[dict], u: str) -> str:
    rs = sorted((r for r in rows if r["universe"] == u and not r.get("refused") and r.get("margin_net") is not None),
                key=lambda r: -r["margin_net"])[:TOP_ROWS]
    if not rs:
        return f'<p class="sub">No cell in {esc(u)} has a margin: every baseline or every cell was refused.</p>'
    trs = ""
    for r in rs:
        eras = " / ".join(_ev(e) for e in (r.get("eras") or []))
        floor = (r.get("lowest_affordable_floor") or {}).get("4")
        trs += (f'<tr><td>{pill("pass" if tier_of(r) == "held" else "note", TIER_LABEL[tier_of(r)])}</td><td>{esc(r["regime"])}</td>'
                f'<td>{esc(mechanism_key(r))}</td><td>{esc(geometry(r))}</td><td>{count(r["trades"])}'
                + (f'<small> · {count(r["missed"])} missed</small>' if r.get("missed") else "") + f'</td><td>{_ev(r["ev_net"])}</td>'
                f'<td>{_ev(r.get("baseline_ev_net"))}</td><td><strong>{_ev(r["margin_net"])}</strong></td><td>{esc(eras)}</td>'
                f'<td>{_ev(r.get("leave_one_name_out_min"))}</td><td>{count(r.get("n_eff_measurement") or 0)}</td>'
                f'<td>{esc(floor + " R" if floor else "—")}</td></tr>')
    return (f'<div class="scroll"><table><thead><tr><th>tier</th><th>regime</th><th>mechanism</th><th>geometry</th><th>trades</th>'
            f'<th>EV net R</th><th>always-long</th><th>margin</th><th>eras</th><th>min, one name out</th><th>N eff, measurement</th>'
            f'<th>lowest floor, k=4</th></tr></thead><tbody>{trs}</tbody></table></div>')


def _card(cell: dict, family, cost: str, seq: int) -> str:
    t = tier_of(cell)
    eras = "".join(f'<div class="{"pos" if (e["ev_net"] or 0) > 0 else "neg"}"><strong>era {i + 1}</strong> {esc(date.fromordinal(e["bounds"][0]).isoformat())} → '
                   f'{esc(date.fromordinal(e["bounds"][1]).isoformat())}<br>{count(e["n"])} trades · EV {_ev(e["ev_net"])}<br>'
                   f'without it {_ev(cell["leave_one_era_out"][i])}</div>' for i, e in enumerate(cell["eras"]))
    per = sorted(cell["per_name"].items(), key=lambda x: x[1]["ev_net"])
    names = (f'{count(cell["names_traded"])} names traded; weakest {esc(per[0][0])} {_ev(per[0][1]["ev_net"])} over {count(per[0][1]["n"])}, '
             f'strongest {esc(per[-1][0])} {_ev(per[-1][1]["ev_net"])} over {count(per[-1][1]["n"])}' if per else "no trades")
    if cell.get("missed"):
        by = cell.get("missed_by_name") or {}
        names += (f'. <strong>{count(cell["missed"])} entries missed</strong> — the fill auditor refused them and no position was opened (ADR-0041): '
                  + ", ".join(f"{esc(n)} {count(k)}" for n, k in sorted(by.items(), key=lambda x: -x[1])[:6]))
    req = cell.get("required_n") or {}
    floors = ", ".join(f'{f} R needs {count(v["4"])}' for f, v in sorted(req.items(), key=lambda x: float(x[0])))
    rd = cell.get("readiness", {})
    ready = ("registrable in principle: three names or more, the sweep holds the plateau, and the measurement partition affords a floor of "
             f'{esc((cell.get("lowest_affordable_floor") or {}).get("4"))} R at k = 4' if rd.get("names_ok") and rd.get("plateau_ok")
             and (cell.get("lowest_affordable_floor") or {}).get("4") else "not registrable as it stands: "
             + ("fewer than three names" if not rd.get("names_ok") else "the plateau does not fit" if not rd.get("plateau_ok")
                else "no floor in the table is affordable on the measurement partition"))
    sweep = f'{count(family.size)} cells' if family else "?"
    return (f'<article class="card" id="cell-{esc(cell["cell"])}"><h3>{seq} · {esc(cell["universe"])} · {esc(cell["regime"])} · {esc(mechanism_key(cell))} '
            f'{pill("pass" if t == "held" else "note", TIER_LABEL[t])}</h3>'
            f'<p class="hyp">{esc(cell["hypothesis"])}</p>'
            f'<p class="mono">cell {esc(cell["cell"])} · spec {short(cell["spec_hash"])} · {esc(geometry(cell))} · axis {esc(cell["axis"])}</p>'
            f'<p><strong>{count(cell["trades"])} trades</strong> on the definition partition; EV gross {_ev(cell["ev_gross"])}, '
            f'<strong>net {_ev(cell["ev_net"])}</strong> at bounded costs; always-long at this geometry {_ev(cell["baseline"]["ev_net"])} '
            f'over {count(cell["baseline"]["trades"])}; <strong>margin {_ev(cell["margin_net"])}</strong>. {names}. '
            f'Every name held out: at worst {_ev(cell["leave_one_name_out_min"])}.</p>'
            f'<div class="eras">{eras}</div>'
            f'<p>Same-day ρ {esc("—" if cell["rho"] is None else f"{cell[chr(114)+chr(104)+chr(111)]:.2f}")}, design effect {num(cell["design_effect"], 2)}; '
            f'the measurement partition would afford about {count(cell["n_eff_measurement"])} effective trades at this firing rate; '
            f'at the cell\'s own σ ({num(cell["sigma_used"], 2)}) and k = 4, {esc(floors) or "the axis has no alpha"}.</p>'
            f'<p><strong>Registering it:</strong> {ready}. The question would carry the family\'s sweep of {sweep}; {cost}.</p></article>')


def _cards(rows: list[dict], out: Path, grid: Grid, u: str, pricer) -> str:
    rs = [r for r in rows if r["universe"] == u and not r.get("refused") and r.get("margin_net") is not None]
    rs.sort(key=lambda r: (TIERS.index(tier_of(r)), -r["margin_net"]))
    html = ""
    for i, r in enumerate(rs[:CARDS], 1):
        cell = json.loads((out / "cells" / f"{r['cell']}.json").read_text(encoding="utf-8"))
        fam = family_of(grid, r)
        html += _card(cell, fam, pricer(cell, fam), i)
    return f'<div class="stack">{html}</div>' if html else ""


def _footer(index: dict, generated: str) -> str:
    return ('<footer><p><strong>What this page is not.</strong> It is not a verdict: every number is from the definition partition, '
            'the calibration set the lab may read, at zero alpha. It is not a dashboard of profit: colour is trust — a positive margin over '
            'random entry at the same geometry, held across eras and names. It is not public until the publication gate (R7).</p>'
            f'<p class="mono">generated {esc(generated)} · results {short(index["results_sha"])}</p></footer>')


def render_page(grid: Grid, out: Path, *, register=None, cfg=None, generated: str | None = None) -> str:
    index = json.loads((out / INDEX_FILE).read_text(encoding="utf-8"))
    if index.get("grid_sha") != grid.sha:
        raise GridRefused(f"the results in {out} are for grid {str(index.get('grid_sha'))[:12]}, not {grid.sha[:12]}")
    rows = index["cells"]
    record = None
    if register is not None:
        for line in register.chain():
            p = line["payload"]
            if p["type"] == "SurveyRecorded" and p["results_sha"] == index["results_sha"]:
                record = {**p, "seq": line["seq"]}
    pricer = _pricer(cfg, register)
    unis = [u for u, _s, _r in grid.universes]
    nav = ('<nav class="toc" aria-label="Sections"><a href="#grid">Grid</a><a href="#matrix">Matrix</a>'
           + "".join(f'<a href="#u-{esc(u)}">{esc(u)}</a>' for u in unis) + "</nav>")
    body = _head(index, grid, record) + nav + _grid_in_words(grid) + _matrix(grid, rows)
    for n, u in enumerate(unis, 3):
        summary = index.get("universes", {}).get(u, {})
        run = [r for r in rows if r["universe"] == u]
        held = sum(1 for r in run if tier_of(r) == "held")
        body += (f'<h2 id="u-{esc(u)}">{n} · {esc(u)}</h2>'
                 f'<p>{count(len(summary.get("names", [])))} names on the definition partition, {count(len(run))} cells, '
                 f'{count(held)} held; {count(summary.get("measurement_days", 0))} days of measurement partition untouched.</p>'
                 + _refusals(rows, u) + f'<h3>Top {TOP_ROWS} by margin over always-long</h3>' + _universe_table(rows, u)
                 + '<h3>Cells, in full</h3>' + _cards(rows, out, grid, u, pricer))
    gen = generated or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>Survey {esc(index['grid'])} · seed {esc(str(index['seed']))}</title><style>{CSS}{PAGE_CSS}</style></head><body><main>"
            + body + _footer(index, gen) + "</main></body></html>\n")


def _pricer(cfg, register):
    """What registering a cell would cost in alpha: the axis rate times the
    family's sweep, from the accountant — with a config and a Register;
    otherwise the sentence says who prices it."""
    if cfg is None or register is None:
        return lambda cell, fam: "the accountant prices it at registration from the programme's config"
    from occams.config import InformationAxis
    from occams.hypothesis import Tier
    from occams.ledger.alpha_budget import AlphaBudget
    from occams.whatif import config_sha

    budget = AlphaBudget(cfg, register, config_sha=config_sha(cfg))

    def price(cell, fam):
        if fam is None:
            return "its family is not in this grid"
        try:
            a = budget.spend_for(InformationAxis(cell["axis"]), Tier.MECHANISM, fam.size)
        except Exception as e:  # noqa: BLE001 — an axis with no budget, or a refused config, is a sentence not a crash
            return f"the accountant refuses to price it: {esc(str(e))}"
        return f"the accountant prices it at <strong>{num(a, 4)}</strong> alpha on the {esc(cell['axis'])} axis (rate × {count(fam.size)} cells)"
    return price


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="python -m occams survey page")
    ap.add_argument("grid", type=Path)
    ap.add_argument("--out", required=True, type=Path, help="the survey's results directory (survey.json and cells/)")
    ap.add_argument("--register", default=None, type=Path)
    ap.add_argument("--config", default=None)
    ap.add_argument("--html", default=None, type=Path, help="default: docs/surveys/<grid>-seed<seed>.html")
    a = ap.parse_args(argv)
    reg = cfg = None
    if a.register:
        from occams.register import Register

        reg = Register(a.register)
    if a.config:
        from occams.config import ConfigRefused, load

        try:
            cfg = load(a.config)
        except ConfigRefused as e:
            print("REFUSED: the configuration does not load.")
            for r in e.reasons:
                print(f"  - {r}")
            return 2
    try:
        grid = load_grid(a.grid, register=reg)
        page = render_page(grid, a.out, register=reg, cfg=cfg)
    except (GridRefused, OSError) as e:
        print(f"REFUSED: {e}")
        return 1
    index = json.loads((a.out / INDEX_FILE).read_text(encoding="utf-8"))
    html = a.html or Path("docs") / "surveys" / f"{index['grid']}-seed{index['seed']}.html"
    html.parent.mkdir(parents=True, exist_ok=True)
    html.write_text(page, encoding="utf-8")
    print(f"survey page: {html} ({len(page.encode('utf-8')):,} bytes) — {index['grid']} seed {index['seed']}, {index['cell_count']:,} cells, "
          f"results {index['results_sha'][:12]}" + ("; priced" if cfg is not None and reg is not None else "; unpriced"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
