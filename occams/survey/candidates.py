"""From a recorded survey to registration, still a human act (M12.5).

    python -m occams survey candidates GRID --out DIR --register PATH [--config PATH]
                                       [--top N] [--ids a,b,…] [--drafts DIR | --no-drafts]
    python -m occams question prepare  --from-survey DIR --grid GRID --ids a,b,… --archive DIR --register PATH
                                       [--config PATH] --floor-ev X --floor-frequency Y [--sigma S] [--seed N] …
    python -m occams question register --from-survey DIR --grid GRID --ids a,b,… … --by NAME --yes

``candidates`` lists the survey's gate-ready cells — one per family, its
best cell by tier then margin — with what registering each would cost in
alpha, and writes a generated Draft document per candidate under
``docs/drafts/survey/`` (no standing). ``register --from-survey`` registers
the named cells' families as questions through the accountant as now: the
cell's mechanism sentence is the R4.9 distinction, the family's sweep is
the search space, the universe's own frozen calendar and members are the
measurement set, and every ``HypothesisRegistered`` is stamped with the
survey's screened-cell count (N6). Nothing registers without ``--yes``
naming the ids; a survey the Register does not hold is refused; a plateau
the sweep cannot hold, a set below three names or an underpowered floor
is refused before any spend, as now.

The floor is the author's: ``--floor-ev`` and ``--floor-frequency`` have
no default. The cell's own σ on the definition partition is the plan's
sigma unless ``--sigma`` says otherwise, with its provenance written.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import replace
from pathlib import Path

from occams.config import InformationAxis
from occams import inference
from occams.inference import format_p
from occams.survey.grid import REGIME_NONE, Cell, Family, Grid, GridRefused, load as load_grid
from occams.survey.page import MIN_TRADES, TIERS, family_of, geometry, mechanism_key, tier_of
from occams.survey.run import INDEX_FILE, World, _engine_for, build_world, engine_code_sha

DRAFTS_ROOT = Path("docs") / "drafts" / "survey"
TOP = 20
ID_PREFIXES = {"register": "Q-"}        # programme 1's Register by name; programme N's is programme-N.jsonl -> QN-


def default_id_prefix(register_path) -> str | None:
    """The question-id prefix a Register's name implies: ``register.jsonl``
    is programme 1's (``Q-``), ``programme-N.jsonl`` is programme N's
    (``QN-``). A Register named otherwise implies none — the caller passes
    ``--id-prefix`` or is refused, so a third programme's questions are
    never numbered as the second's."""
    stem = Path(register_path).stem
    if stem in ID_PREFIXES:
        return ID_PREFIXES[stem]
    m = re.fullmatch(r"programme-(\d+)", stem)
    return f"Q{m.group(1)}-" if m else None


def _n(x) -> str:
    return f"{int(x):,}"


def _ev(x) -> str:
    return "—" if x is None else f"{x:+.3f}"


# ---- the survey, as the Register holds it ---------------------------------------------

def load_index(out: Path) -> dict:
    return json.loads((out / INDEX_FILE).read_text(encoding="utf-8"))


def grid_sentence(fam: Family, row: dict) -> str:
    """The cell's mechanism sentence as the grid and the proposer build it
    now (``Cell.hypothesis``). A survey's cell file records the sentence the
    proposer wrote on the day it ran; the R4.9 distinction a question is
    registered with is the grid's, and the recorded one is stamped beside it
    when the two differ — the file is the record, the sentence is the claim."""
    return Cell(fam, hold=float(row["hold"]), stop=float(row["stop"]), target=float(row.get("target") or 0)).hypothesis


def survey_record(register, index: dict) -> dict | None:
    """The ``SurveyRecorded`` record whose results hash is this index's, with its seq."""
    for line in register.chain():
        p = line["payload"]
        if p["type"] == "SurveyRecorded" and p["results_sha"] == index["results_sha"]:
            return {**p, "seq": line["seq"]}
    return None


def survey_engine(index: dict, out: Path | None = None) -> str:
    """The engine code hash the survey's cells were computed by: the index's,
    else the first cell file's (an index written before the stamp)."""
    then = (index.get("engine_shas") or {}).get("engine_code_sha", "")
    if not then and out is not None:
        for f in sorted((out / "cells").glob("*.json"))[:1]:
            then = json.loads(f.read_text(encoding="utf-8")).get("engine_code_sha", "")
    return then


def engine_note(index: dict, out: Path | None = None) -> str:
    then = survey_engine(index, out)
    now = engine_code_sha()
    if then == now:
        return f"engine {now}, the survey's own"
    return (f"the survey was computed on engine {then or 'unstamped: the box ran before the stamp existed'}; the engine is now {now} "
            f"(ADR-0040, ADR-0041): the screen's numbers are that engine's, the measurement will be this one's, and the shrinkage is "
            f"recorded per question (M12.6)")


# ---- gate-ready cells, one per family ---------------------------------------------------

def gate_ready(row: dict) -> tuple[bool, str]:
    """Whether a cell is registrable as it stands, in the survey's own terms
    — the readiness triple and an affordable floor at k = 4 — and why not.
    No floor is chosen here; the author declares one at registration."""
    if row.get("refused"):
        return False, "refused by name"
    rd = row.get("readiness") or {}
    if not rd.get("names_ok"):
        return False, "fewer than three names"
    if not rd.get("plateau_ok"):
        return False, "the plateau does not fit the sweep"
    if row.get("margin_net") is None:
        return False, "no margin: the baseline was refused"
    if not ((row.get("ev_net") or 0.0) > 0 and row["margin_net"] > 0):
        return False, "EV or margin over always-long is not positive"
    if (row.get("trades") or 0) < MIN_TRADES:
        return False, f"fewer than {MIN_TRADES} trades on the definition partition"
    if not (row.get("lowest_affordable_floor") or {}).get("4"):
        return False, "no floor in the table is affordable on the measurement partition at k = 4"
    return True, ""


def candidates(index: dict, grid: Grid, *, budget=None) -> list[dict]:
    """One candidate per family — its best gate-ready cell by tier, then
    margin — best first, priced by the accountant when a budget is given."""
    from occams.hypothesis import Tier

    best: dict[str, tuple] = {}
    for r in index["cells"]:
        ok, _why = gate_ready(r)
        if not ok:
            continue
        fam = family_of(grid, r)
        if fam is None:
            continue
        key = fam.describe()
        rank = (TIERS.index(tier_of(r)), -float(r["margin_net"]))
        if key not in best or rank < best[key][0]:
            best[key] = (rank, r, fam)
    out = []
    for _rank, r, fam in sorted(best.values(), key=lambda x: x[0]):
        alpha = None
        if budget is not None:
            try:
                alpha = budget.spend_for(InformationAxis(r["axis"]), Tier.MECHANISM, fam.size)
            except Exception:   # noqa: BLE001 — an axis with no budget is a sentence, not a crash
                alpha = None
        out.append({"cell": r["cell"], "tier": tier_of(r), "row": r, "family": fam, "sweep": fam.size, "alpha": alpha,
                    "hypothesis": grid_sentence(fam, r), "survey_hypothesis": r["hypothesis"]})
    return out


# ---- the generated Draft document ----------------------------------------------------------

def draft_document(c: dict, index: dict, record: dict, *, out: Path, grid_path: Path) -> str:
    r, fam = c["row"], c["family"]
    eras = " / ".join(_ev(e) for e in (r.get("eras") or []))
    floor = r.get("lowest_affordable_floor") or {}
    price = (f"the accountant prices it at **{c['alpha']:.4g}** alpha on the {r['axis']} axis (rate × {c['sweep']} cells)"
             if c.get("alpha") is not None else "the accountant prices it at registration from the programme's config")
    sweep = ", ".join(f"{k} {', '.join(f'{x:g}' for x in v)}" for k, v in fam.sweep.axes)
    sentence = c.get("hypothesis") or grid_sentence(fam, r)
    recorded = ("" if r["hypothesis"] == sentence else
                f"\n\nThe survey's cell file recorded the sentence as: *{r['hypothesis']}* — the proposer's wording on the day it ran; "
                f"the sentence above is the grid's now, and registration stamps the recorded one beside it.")
    status = (f"CANDIDATE — generated by `python -m occams survey candidates` from survey record #{record['seq']} ({index['grid']}, "
              f"seed {index['seed']}); no standing, no alpha spent; registration is the author's `--yes` naming this cell's id (M12.5)")
    return f"""---
status: {status}
tier: mechanism
axis: {r['axis']}
relates_to: "TASKS-v4.md M12.5 · docs/adr/0039 · docs/surveys/{index['grid']}-seed{index['seed']}.html#cell-{r['cell']}"
---

# Survey candidate {r['cell']} — {r['kind']} on {r['universe']}

A **Draft**: a proposed Hypothesis carrying a mechanism and a falsifier,
with **no standing until a human confirms its registration**, which is the
act that spends alpha. Nothing here has been measured on the measurement
partition. Nothing here has cost anything. It was generated from a survey
cell; the screen is not a verdict, and the shrinkage from screening
{_n(index['cell_count'])} cells is recorded per question (N6, M12.6).

## Mechanism

{sentence}{recorded}

Universe **{r['universe']}**, regime gate **{r['regime']}**, `{mechanism_key(r)}`, {geometry(r)}.

## Both interpretations

- **If true:** the winner cell clears the declared floor and beats random
  entry at the corrected alpha on the measurement partition — the
  mechanism the survey screened is real after costs on this universe.
- **If false:** the winner cell is not distinguishable from random entry
  after costs, or does not clear the floor — the screen's margin was
  selection, and the shrinkage says by how much.

## Falsifier

The winner cell's EV in net R at or below the null's corrected quantile,
or below the floor the author declares at registration, on the
measurement partition.

## What the survey showed — definition partition only, zero alpha, not a verdict

- tier **{c['tier']}** · {_n(r['trades'])} trades · EV gross {_ev(r.get('ev_gross'))}, net {_ev(r['ev_net'])} at bounded costs
- always-long at this geometry {_ev(r.get('baseline_ev_net'))} over {_n(r.get('baseline_trades') or 0)} · **margin {_ev(r['margin_net'])}**
- eras {eras} · weakest name held out {_ev(r.get('leave_one_name_out_min'))} · missed entries {_n(r.get('missed') or 0)}
- same-day ρ {('—' if r.get('rho') is None else f"{r['rho']:.2f}")} · N eff on the measurement partition {_n(r.get('n_eff_measurement') or 0)}
- lowest affordable floor at k = 4: {floor.get('4') or '—'} R; at k = 9: {floor.get('9') or '—'} R

## Search space

The family's sweep — {sweep} — {c['sweep']} cells; {price}.

## Registration — the author's act

```
python -m occams question register --from-survey {out} --grid {grid_path} --ids {r['cell']} \\
    --archive archive --register register/programme-2.jsonl --config configs/programme-2.toml \\
    --floor-ev FLOOR --floor-frequency TRADES_PER_YEAR --by NAME --yes
```

The floor is declared there, by the author; this document supplies none.
"""


def write_drafts(cands: list[dict], index: dict, record: dict, *, root: Path, out: Path, grid_path: Path) -> list[Path]:
    d = root / f"{index['grid']}-seed{index['seed']}"
    d.mkdir(parents=True, exist_ok=True)
    paths = []
    for c in cands:
        p = d / f"{c['cell']}.md"
        p.write_text(draft_document(c, index, record, out=out, grid_path=grid_path), encoding="utf-8")
        paths.append(p)
    return paths


# ---- from a candidate to a question ----------------------------------------------------------

def family_template(fam: Family, classifier_hash: str):
    """The family's template — the first hold, its order and stop kind —
    gated like its cells (M12.3), with the capabilities every cell of the
    sweep needs: a family with targets rests an order at the venue in each
    of its target cells, so the template declares it (ADR-0018), or the
    cells would not compile at measurement."""
    from occams.question import apply_cell
    from occams.spec.compile import derived_capabilities
    from occams.spec.spec import Regime, RegimeGate

    spec = fam.template()
    if fam.regime != REGIME_NONE:
        spec = spec.replace(regime=RegimeGate(classifier_hash, Regime(fam.regime), fam.regime_index), axis=InformationAxis.REGIME)
    widest = apply_cell(spec, {"target": float(fam.targets[0])}) if fam.targets else spec
    return spec.replace(required_capabilities=derived_capabilities(widest))


def precommit_on(template, world: World, *, ctx, seed: int) -> dict:
    """What registration needs, from the universe's definition partition
    only (D13): the signal rate, the trades its measurement partition
    therefore affords, and the measured clustering. Never its bars."""
    from occams.proposers.clustering import measure_clustering
    from occams.proposers.regime import ClusterLevel
    from occams.spec.compile import to_engine

    engine = _engine_for(template.horizon)
    trades = engine.run(to_engine(template), world.definition, seed=seed, actions=world.actions,
                        regime=ctx if template.regime is not None else None)
    def_bars = sum(b.n for b in world.definition.values())
    rate = len(trades) / max(1, def_bars)
    available = int(rate * world.measurement_days * len(world.names_in_measurement) * (252 / 365.25))
    level = ctx.classifier.level if ctx is not None and template.regime is not None else \
        (ClusterLevel.INDEX if len(world.definition) > 1 else ClusterLevel.INSTRUMENT)
    cm = None
    if len({t.day for t in trades}) >= 2 and len(trades) >= 3:
        cm = measure_clustering([t.as_trade() for t in trades], level=level,
                                provenance=f"{world.universe} definition partition {world.definition_bounds}, {len(trades)} signals")
    return {"definition_trades": len(trades), "missed": len(getattr(trades, "missed", ())), "rate_per_name_day": rate,
            "available_n": available, "clustering": cm, "names": tuple(world.names_in_measurement),
            "measurement_bounds": world.measurement_bounds, "definition_days": world.definition_days,
            "measurement_days": world.measurement_days, "definition_bars": def_bars}


def bound_by_thinnest_cell(pre: dict, kin: list[dict]) -> dict:
    """The guard at measurement counts the *winner's own* trades against the
    power plan (M8.2), and the winner may be any cell of the sweep — so the
    trades registration promises are the sweep's thinnest cell's, not the
    template's signals: a hold-1 template fires on every signal day, a
    hold-20 cell boxes most of them out (Q3-001, 2026-09-20: 2,187 template
    signals, 863 winner trades against 1,068 required). The survey holds
    every cell's definition-partition count; the thinnest, scaled as the
    template's rate is, bounds ``available_n`` from above."""
    cells = [r for r in kin if not r.get("refused") and r.get("trades")]
    if not cells or not pre.get("definition_bars"):
        return pre
    thin = min(cells, key=lambda r: r["trades"])
    scaled = int(thin["trades"] / pre["definition_bars"] * pre["measurement_days"] * len(pre["names"]) * (252 / 365.25))
    return {**pre, "template_available_n": pre["available_n"], "available_n": min(pre["available_n"], scaled),
            "thinnest_cell": {"geometry": geometry(thin), "definition_trades": int(thin["trades"]), "available_n": scaled}}


def question_from_cell(row: dict, fam: Family, *, qid: str, index: dict, record: dict, template, pre: dict, budget,
                       floor, sigma: float | None, power: float, gates):
    from occams.measurement import Floor
    from occams.proposers.base import Draft
    from occams.question import from_draft

    s = sigma if sigma is not None else row.get("sigma_net")
    if s is None or s <= 0:
        raise ValueError(f"cell {row['cell']} has no σ on the definition partition (fewer than two trades); pass --sigma with its provenance")
    provenance = (f"σ of net R over {row['trades']} definition-partition trades of survey cell {row['cell']} "
                  f"(record #{record['seq']}, {index['grid']} seed {index['seed']})" if sigma is None else "declared with --sigma")
    sentence = grid_sentence(fam, row)
    d = Draft(proposer="survey", axis=InformationAxis(fam.axis), mechanism=sentence,
              if_true="the winner cell clears the declared floor and beats random entry at the corrected alpha on the measurement "
                      "partition — the mechanism the survey screened is real after costs on this universe",
              if_false="the winner cell is not distinguishable from random entry after costs, or does not clear the floor — "
                       "the screen's margin was selection, and the shrinkage says by how much",
              falsifier="the winner cell's EV in net R at or below the null's corrected quantile, or below the declared floor, "
                        "on the measurement partition",
              floor=Floor(float(floor[0]), float(floor[1])), sweep=fam.sweep, sigma_r=float(s), sigma_provenance=provenance,
              power=power, gates=gates)
    q = from_draft(d, id=qid, template=template, budget=budget, available_n=pre["available_n"])
    if pre["clustering"] is not None:
        q = replace(q, hypothesis=replace(q.hypothesis, power_plan=q.hypothesis.power_plan.with_clustering(pre["clustering"])))
    stamp = {"grid_name": index["grid"], "grid_sha": index["grid_sha"], "results_sha": index["results_sha"],
             "record_seq": record["seq"], "seed": index["seed"], "cell": row["cell"], "universe": fam.universe,
             "screened_cells": int(index["cell_count"]), "engine_code_sha": survey_engine(index),
             "definition": {"trades": row["trades"], "ev_net": row["ev_net"], "margin_net": row["margin_net"],
                            "baseline_ev_net": row.get("baseline_ev_net"), "tier": tier_of(row)}}
    if row["hypothesis"] != sentence:
        stamp["survey_hypothesis"] = row["hypothesis"]     # what the cell file recorded; the claim registered is the grid's
    q = replace(q, hypothesis=replace(q.hypothesis, distinction=f"{sentence} — on {fam.universe}", survey=stamp))
    return q


# ---- the fifth check on the definition partition (ADR-0043) ---------------------------------------

def fifth_check_readiness(cands: list[dict], index: dict, *, archive, register, cfg, seed: int, draws: int = 4000) -> list[dict]:
    """What the fifth check would say of each candidate on the definition
    partition, at zero alpha (D13): the cell's trades and always-long at the
    cell's geometry and gate, both run now on the current engine; the
    comparison the guard makes — the two resampled together by calendar day
    at the cell's own count, with the clustered standard error beside it
    (ADR-0048, ADR-0049) — at the axis's corrected alpha; and the margin over
    always-long in each definition era, which the survey's tiers pooled.
    A screen is not a verdict; this is the gate shown passable, or not,
    before alpha moves. It tests each candidate alone: twenty candidates are
    the best of thousands of cells, and nothing here corrects for that.

    """
    from occams.costs.equity import EquityCosts, InstrumentClass
    from occams.data.partitions import Partitions
    from occams.engine import probes
    from occams.engine.regime_gate import RegimeContext
    from occams.measurement import Cell as MeasuredCell
    from occams.proposers.regime import frozen
    from occams.spec.compile import to_engine
    from occams.survey.grid import Cell
    from occams.survey.run import _eras, _mean, baseline_spec, gated_spec

    clf = frozen(register)
    classifier_hash = clf.frozen_hash if clf is not None else ""
    ctx = RegimeContext.from_register(register, archive) if any(c["family"].regime != REGIME_NONE for c in cands) else None
    parts = Partitions.from_config(cfg)
    latest = archive.latest_bars()
    costs = EquityCosts.declared(InstrumentClass.US_LARGE, instrument_currency="USD", account_currency=cfg.capital.currency).bound()
    worlds: dict[str, World] = {}
    out = []
    for c in cands:
        row, fam = c["row"], c["family"]
        if fam.universe not in worlds:
            worlds[fam.universe] = build_world(fam.universe, latest=latest, register=register, parts=parts)
        world = worlds[fam.universe]
        cell = Cell(fam, float(row["hold"]), float(row["stop"]), float(row.get("target") or 0.0))
        spec = gated_spec(cell, classifier_hash)
        engine = _engine_for(spec.horizon)
        regime = ctx if spec.regime is not None else None
        trades = engine.run(to_engine(baseline_spec(cell, classifier_hash)), world.definition, seed=seed, actions=world.actions,
                            costs=costs, regime=regime)
        net = [t.net_r for t in trades]
        base_now = _mean(net)
        eras_base = [_mean(t.net_r for t in trades if lo <= t.day < hi) for lo, hi in _eras(world.definition_bounds)]
        eras_cell = list(row.get("eras") or [])
        eras_margin = [(a - b) if a is not None and b is not None else None for a, b in zip(eras_cell, eras_base, strict=False)]
        alpha_c = float(cfg.alpha.axes[InformationAxis(row["axis"])].mechanism_test_alpha)
        ev = float(row["ev_net"])
        # M16.9, M16.15: the guard's own comparison and the guard's own test, neither re-implemented here — the cell's trades,
        # re-run now, against the passive alternative at their side mix, resampled together by calendar day (ADR-0048, ADR-0049)
        compiled = to_engine(spec)
        cell_trades = engine.run(compiled, world.definition, seed=seed, actions=world.actions, costs=costs, regime=regime)
        ev_now = _mean(t.net_r for t in cell_trades)
        share = probes.long_share(cell_trades)
        base = (probes.Baseline(base_now, (), 1.0, tuple(trades), None) if share >= 1.0 else
                probes.baseline_of(compiled, world.definition, cell_trades, seed=seed, cost_in_r=0.0, actions=world.actions, costs=costs,
                                   regime=regime))
        dist, p_b, verdict, need = (), None, "thin", inference.draws_needed(alpha_c)
        if net and cell_trades:
            cmp = probes.against_passive(compiled, world.definition, cell_trades, base, draws=draws, seed=seed)
            dist = cmp.draws
            state, p_mc, need = inference.exceedance(dist, ev_now, alpha_c)
            if state != "thin":
                p_b = inference.guard_p(p_mc, cmp.stats(), MeasuredCell((0,), (), tuple(t.as_trade() for t in cell_trades)))
                verdict = "pass" if p_b <= alpha_c else "refuse"
        out.append({"cell": row["cell"], "universe": fam.universe, "tier": c["tier"], "family": fam.describe(), "ev_net": ev,
                    "ev_now": ev_now, "trades_now": len(cell_trades), "long_share": share,
                    "baseline_survey": row.get("baseline_ev_net"), "baseline_now": base_now, "baseline_trades_now": len(trades),
                    "margin_now": (ev - base_now) if base_now is not None else None, "p_baseline": p_b, "alpha_corrected": alpha_c,
                    "draws": len(dist), "needed": need, "fifth_check": verdict, "eras_cell": eras_cell, "eras_baseline": eras_base,
                    "eras_margin": eras_margin, "sweep": c["sweep"], "alpha": c.get("alpha")})
    return out


def readiness_p(dist, ev: float) -> float:
    """The fifth check's p on the definition partition, as the guard counts it: plus one
    (ADR-0048 §4). No draw reaching the cell is `at most one in draws + 1`, never zero."""
    return inference.monte_carlo_p(dist, ev)


def _f(x, places: int = 3) -> str:
    return "—" if x is None else f"{x:+.{places}f}"


def readiness_document(rows: list[dict], index: dict, record: dict, *, register, draws: int, seed: int,
                       prior_registers=()) -> str:
    """One Markdown table, committed beside the survey page: the fifth check
    on the definition partition per candidate, the margin per era, and the
    measured priors — every ``Shrinkage`` record in this Register and in any
    earlier programme's Register given read-only (ADR-0046)."""
    from occams.survey.run import engine_code_sha

    priors = [(register, r) for r in register.records() if r["type"] == "Shrinkage"]
    for other in prior_registers:
        priors += [(other, r) for r in other.records() if r["type"] == "Shrinkage"]
    screened_on = "`" + survey_engine(index) + "`" if survey_engine(index) else "unstamped: the box ran before the stamp existed"
    head = [f"# Readiness under the fifth check — {index['grid']} seed {index['seed']}", "",
            f"**Dated {__import__('datetime').date.today().isoformat()}. Zero alpha; the definition partition only (D13); nothing here is a verdict.** "
            f"Survey record #{record['seq']}, {_n(index['cell_count'])} cells screened, results `{index['results_sha'][:12]}`; "
            f"always-long re-run now on engine `{engine_code_sha()}` (the survey's screen was {screened_on}); "
            f"{_n(draws)} draws, seed {seed}. *Fifth check* is ADR-0043's test as the guard would apply it here: the cell's trades "
            f"against the passive alternative at the same geometry, gate and side mix, resampled together by calendar day, at the axis's "
            f"corrected alpha (ADR-0048, ADR-0049). It tests each candidate alone and corrects nothing for their being the best of "
            f"{_n(index['cell_count'])} cells. *Margin by era* is "
            f"the cell's EV less always-long's in each third of the definition partition, oldest first — the survey's tiers pooled these.", ""]
    if priors:
        head.append("**Measured priors** — every question registered from a survey and resolved, screen beside measurement (M12.6), "
                    "this programme's and the earlier programmes' read-only:")
        head.append("")
        for reg, r in priors:
            head.append(f"- `{r['hypothesis_id']}` ({Path(reg.path).name}) from cell `{r['survey_cell']}`: definition margin "
                        f"{_f(r['definition_margin_net'])} → measured margin {_f(r['measured_margin_net'])} (Δ {_f(r['margin_shrinkage'])}); "
                        f"EV {_f(r['definition_ev_net'])} → {_f(r['measured_ev_net'])}.")
        head.append("")
    table = ["| # | Cell | Universe | Tier | EV | Always-long, survey → now | Margin now | p vs α | Fifth check | Margin by era | Sweep · alpha |",
             "|---:|---|---|---|---:|---|---:|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        p = "—" if r["p_baseline"] is None else f"{format_p(r['p_baseline'])} vs {r['alpha_corrected']:.4g}"
        eras = " / ".join(_f(x) for x in r["eras_margin"])
        price = f"{r['sweep']} · {r['alpha']:.4g}" if r.get("alpha") is not None else f"{r['sweep']} · unpriced"
        table.append(f"| {i} | `{r['cell']}` | {r['universe']} | {r['tier']} | {_f(r['ev_net'])} | {_f(r['baseline_survey'])} → {_f(r['baseline_now'])} "
                     f"| {_f(r['margin_now'])} | {p} | **{r['fifth_check']}** | {eras} | {price} |")
    passing = sum(1 for r in rows if r["fifth_check"] == "pass")
    latest_neg = sum(1 for r in rows if r["eras_margin"] and r["eras_margin"][-1] is not None and r["eras_margin"][-1] <= 0)
    tail = ["", f"{passing} of {len(rows)} candidates pass the fifth check on the definition partition; {latest_neg} of {len(rows)} have no "
            f"margin over always-long in the latest definition era. A pass here is the gate shown passable before alpha moves, not a "
            f"verdict; the measurement partition decides, once, at registration's cost. Registration is the author's `--yes`.", ""]
    return "\n".join(head + table + tail)


# ---- the commands ----------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="python -m occams survey candidates")
    ap.add_argument("grid", type=Path)
    ap.add_argument("--out", required=True, type=Path, help="the survey's results directory (survey.json and cells/)")
    ap.add_argument("--register", required=True, type=Path)
    ap.add_argument("--config", default=None, help="prices each candidate in alpha when given")
    ap.add_argument("--top", type=int, default=TOP, help=f"how many candidates to list and draft (default {TOP})")
    ap.add_argument("--ids", default="", help="comma-separated cell ids to list instead of the top N")
    ap.add_argument("--drafts", type=Path, default=DRAFTS_ROOT, help=f"where the Draft documents go (default {DRAFTS_ROOT})")
    ap.add_argument("--no-drafts", action="store_true")
    ap.add_argument("--fifth-check", action="store_true",
                    help="ADR-0043 on the definition partition: always-long at each candidate's geometry and gate, the guard's Monte Carlo, "
                         "the margin per era; needs --archive and --config; zero alpha")
    ap.add_argument("--archive", type=Path, default=None, help="the archive, for --fifth-check")
    ap.add_argument("--draws", type=int, default=4000, help="Monte Carlo draws for --fifth-check")
    ap.add_argument("--seed", type=int, default=None, help="seed for --fifth-check (default: the survey's)")
    ap.add_argument("--readiness-out", type=Path, default=None, help="write the --fifth-check table as Markdown here")
    ap.add_argument("--priors-register", type=Path, action="append", default=[],
                    help="an earlier programme's Register whose Shrinkage records are cited as priors, read-only (ADR-0046); repeatable")
    a = ap.parse_args(argv)
    if a.fifth_check and (a.archive is None or a.config is None):
        print("REFUSED: --fifth-check needs --archive (the bars) and --config (the corrected alpha per axis)")
        return 2

    from occams.register import Register

    reg = Register(a.register)
    try:
        grid = load_grid(a.grid, register=reg)
        index = load_index(a.out)
    except (GridRefused, OSError) as e:
        print(f"REFUSED: {e}")
        return 1
    if index.get("grid_sha") != grid.sha:
        print(f"REFUSED: the results in {a.out} are for grid {str(index.get('grid_sha'))[:12]}, not {grid.sha[:12]}")
        return 1
    record = survey_record(reg, index)
    if record is None:
        print(f"REFUSED: results {index['results_sha'][:12]} are not a SurveyRecorded record in {a.register}; a candidate from a "
              f"survey the Register does not hold is refused — run `survey record` first (M12.3)")
        return 1
    budget = cfg = None
    if a.config:
        from occams.config import ConfigRefused, load
        from occams.ledger.alpha_budget import AlphaBudget
        from occams.whatif import config_sha

        try:
            cfg = load(a.config)
        except ConfigRefused as e:
            print("REFUSED: the configuration does not load.")
            for r in e.reasons:
                print(f"  - {r}")
            return 2
        budget = AlphaBudget(cfg, reg, config_sha=config_sha(cfg))
    cands = candidates(index, grid, budget=budget)
    if a.ids.strip():
        wanted = [x.strip() for x in a.ids.split(",") if x.strip()]
        by = {c["cell"]: c for c in cands}
        missing = [w for w in wanted if w not in by]
        if missing:
            print(f"REFUSED: not gate-ready candidates of this survey: {missing}")
            return 1
        cands = [by[w] for w in wanted]
    else:
        cands = cands[:a.top]
    print(f"survey {index['grid']} · seed {index['seed']} · record #{record['seq']} · {_n(index['cell_count'])} cells screened · "
          f"{len(cands)} candidate(s) shown, one per family, best first · {engine_note(index, a.out)}")
    print("Nothing here is a verdict. Registration is the author's `--yes` naming the ids; the floor is declared there.")
    for i, c in enumerate(cands, 1):
        r = c["row"]
        fl = (r.get("lowest_affordable_floor") or {}).get("4")
        price = f"{c['alpha']:.4g} alpha" if c.get("alpha") is not None else "unpriced"
        print(f"[{i:>2}] {r['cell']} · {c['tier']:<8} · {r['universe']} · {r['regime']} · {mechanism_key(r)} · {geometry(r)}")
        print(f"      {_n(r['trades'])} trades · EV {_ev(r['ev_net'])} · always-long {_ev(r.get('baseline_ev_net'))} · margin {_ev(r['margin_net'])} · "
              f"eras {' / '.join(_ev(e) for e in (r.get('eras') or []))} · one name out {_ev(r.get('leave_one_name_out_min'))} · "
              f"N eff {_n(r.get('n_eff_measurement') or 0)} · floor@k4 {fl} R · sweep {c['sweep']} cells · {price} on {r['axis']}")
    if not a.no_drafts and cands:
        paths = write_drafts(cands, index, record, root=a.drafts, out=a.out, grid_path=a.grid)
        print(f"{len(paths)} Draft document(s) written under {paths[0].parent} — no standing, no alpha spent")
    if a.fifth_check and cands:
        from occams.data.archive import BarArchive

        seed = int(a.seed if a.seed is not None else index["seed"])
        rows = fifth_check_readiness(cands, index, archive=BarArchive(a.archive), register=reg, cfg=cfg, seed=seed, draws=a.draws)
        print(f"beats-always-long on the definition partition (ADR-0043), {_n(a.draws)} draws, seed {seed} — the gate shown passable "
              f"before alpha moves; a screen is not a verdict:")
        for i, r in enumerate(rows, 1):
            p = "thin" if r["p_baseline"] is None else f"p {format_p(r['p_baseline'])} vs α {r['alpha_corrected']:.4g}"
            print(f"[{i:>2}] {r['cell']} · {r['universe']} · {r['tier']:<8} · EV {_f(r['ev_net'])} · always-long {_f(r['baseline_survey'])} "
                  f"(survey) → {_f(r['baseline_now'])} (now, {_n(r['baseline_trades_now'])} trades) · margin now {_f(r['margin_now'])} · "
                  f"{p} · {r['fifth_check'].upper()} · margin by era {' / '.join(_f(x) for x in r['eras_margin'])}")
        passing = sum(1 for r in rows if r["fifth_check"] == "pass")
        print(f"{passing} of {len(rows)} pass the fifth check on the definition partition")
        if a.readiness_out is not None:
            a.readiness_out.parent.mkdir(parents=True, exist_ok=True)
            others = [Register(p) for p in a.priors_register]
            a.readiness_out.write_text(readiness_document(rows, index, record, register=reg, draws=a.draws, seed=seed, prior_registers=others),
                                       encoding="utf-8")
            print(f"readiness table written to {a.readiness_out}")
    print("nothing registered, nothing spent. Next: python -m occams question prepare --from-survey "
          f"{a.out} --grid {a.grid} --ids … --archive DIR --register {a.register} --config … --floor-ev X --floor-frequency Y")
    return 0


def register_main(argv: list[str]) -> int:  # noqa: C901 — the author's command: prepare, price, refuse or register, one screen to read in order
    from occams.config import ConfigRefused, load
    from occams.data.archive import BarArchive
    from occams.data.partitions import Partitions
    from occams.engine.regime_gate import RegimeContext
    from occams.guards import Refused
    from occams.guards.leave_one_out import MIN_GROUPS
    from occams.hypothesis import Confirmation, Gates
    from occams.ledger.alpha_budget import AlphaBudget, Consumed, SearchBudget
    from occams.proposers.regime import axis_sensitivity, frozen
    from occams.question import QuestionQueue, max_plateau_neighbourhood, register_question
    from occams.register import Register
    from occams.whatif import config_sha

    cmd = argv[0]
    ap = argparse.ArgumentParser(prog=f"python -m occams question {cmd} --from-survey")
    ap.add_argument("--from-survey", required=True, type=Path, help="the survey's results directory")
    ap.add_argument("--grid", required=True, type=Path)
    ap.add_argument("--ids", required=True, help="comma-separated cell ids; each names its family, one question per family")
    ap.add_argument("--archive", required=True, type=Path)
    ap.add_argument("--register", required=True, type=Path)
    ap.add_argument("--queue", type=Path, default=None, help="default: <register>-queue.jsonl beside the Register")
    ap.add_argument("--config", default=None)
    ap.add_argument("--floor-ev", type=float, required=True, help="the declared floor, EV per trade in net R — the author's")
    ap.add_argument("--floor-frequency", type=float, required=True, help="the declared floor, trades per year — the author's")
    ap.add_argument("--sigma", type=float, default=None, help="default: the cell's own σ on the definition partition, with provenance")
    ap.add_argument("--power", type=float, default=0.8)
    ap.add_argument("--plateau-cells", type=int, default=4)
    ap.add_argument("--plateau-slack", type=float, default=0.10)
    ap.add_argument("--loo-min-fraction", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--id-prefix", default=None, help="question ids; derived from the Register's name when not given (programme-N.jsonl -> QN-)")
    if cmd == "register":
        ap.add_argument("--by", required=True)
        ap.add_argument("--yes", action="store_true", help="the human confirmation, naming every id; without it nothing is registered")
    a = ap.parse_args(argv[1:])

    try:
        cfg = load(a.config)
    except ConfigRefused as e:
        print("REFUSED: the configuration does not load.")
        for r in e.reasons:
            print(f"  - {r}")
        return 2
    reg = Register(a.register)
    archive = BarArchive(a.archive)
    from occams.stopping import describe, stopping_record

    stop = stopping_record(reg)
    if stop:   # ADR-0033, M12.8
        head = "LAB CLOSED (ADR-0033)" if stop["type"] == "LabClosed" else "PROGRAMME STOPPED (M12.8)"
        print(f"{head}: {describe(stop)}; nothing prepares or registers after that record in this Register")
        return 1
    try:
        grid = load_grid(a.grid, register=reg)
        index = load_index(a.from_survey)
    except (GridRefused, OSError) as e:
        print(f"REFUSED: {e}")
        return 1
    if index.get("grid_sha") != grid.sha:
        print(f"REFUSED: the results in {a.from_survey} are for grid {str(index.get('grid_sha'))[:12]}, not {grid.sha[:12]}")
        return 1
    record = survey_record(reg, index)
    if record is None:
        print(f"REFUSED: results {index['results_sha'][:12]} are not a SurveyRecorded record in {a.register}; a candidate from a "
              f"survey the Register does not hold is refused")
        return 1
    rows = {r["cell"]: r for r in index["cells"]}
    ids = [x.strip() for x in a.ids.split(",") if x.strip()]
    if not ids:
        print("REFUSED: --ids names no cell")
        return 1
    unknown = [i for i in ids if i not in rows]
    if unknown:
        print(f"REFUSED: not cells of this survey: {unknown}")
        return 1
    fams: dict[str, tuple[str, Family]] = {}
    for i in ids:
        fam = family_of(grid, rows[i])
        if fam is None:
            print(f"REFUSED: cell {i}'s family is not in grid {grid.name}")
            return 1
        key = fam.describe()
        if key in fams:
            print(f"REFUSED: cells {fams[key][0]} and {i} are one family ({key}) and would be one question; name one of them")
            return 1
        fams[key] = (i, fam)
    for i in ids:
        ok, why = gate_ready(rows[i])
        if not ok:
            print(f"REFUSED: cell {i} is not gate-ready as the survey stands: {why}")
            return 1
    clf = frozen(reg)
    classifier_hash = clf.frozen_hash if clf is not None else ""
    gated = [f for _i, f in fams.values() if f.regime != REGIME_NONE]
    if gated and (clf is None or index.get("classifier_hash") != classifier_hash):
        print(f"REFUSED: the survey's classifier {str(index.get('classifier_hash'))[:12] or 'none'} is not the Register's frozen one "
              f"{classifier_hash[:12] or 'none'}; a gated cell registers against the classifier it was screened with")
        return 1
    ctx = RegimeContext.from_register(reg, archive) if gated else None
    parts = Partitions.from_config(cfg)
    latest = archive.latest_bars()
    worlds: dict[str, World] = {}
    for _i, fam in fams.values():
        if fam.universe not in worlds:
            worlds[fam.universe] = build_world(fam.universe, latest=latest, register=reg, parts=parts)
    budget = AlphaBudget(cfg, reg, config_sha=config_sha(cfg))
    existing = sum(1 for r in reg.records() if r["type"] == "HypothesisRegistered")
    prefix = a.id_prefix or default_id_prefix(a.register)
    if prefix is None:
        print(f"REFUSED: {a.register} does not name its programme (register.jsonl, or programme-N.jsonl); pass --id-prefix so its "
              f"questions are numbered as this programme's and never another's")
        return 1
    gates = Gates(a.plateau_cells, a.plateau_slack, a.loo_min_fraction)
    print(f"survey {index['grid']} · seed {index['seed']} · record #{record['seq']} · {_n(index['cell_count'])} cells screened · "
          f"{engine_note(index, a.from_survey)}")
    prepared = []
    all_clean = True
    for n, (cid, fam) in enumerate(fams.values(), 1):
        row = rows[cid]
        qid = f"{prefix}{existing + n:03d}"
        template = family_template(fam, classifier_hash)
        world = worlds[fam.universe]
        pre = precommit_on(template, world, ctx=ctx, seed=a.seed)
        pre = bound_by_thinnest_cell(pre, [r for r in index["cells"] if family_of(grid, r) is fam])
        try:
            q = question_from_cell(row, fam, qid=qid, index=index, record=record, template=template, pre=pre, budget=budget,
                                   floor=(a.floor_ev, a.floor_frequency), sigma=a.sigma, power=a.power, gates=gates)
        except ValueError as e:
            print(f"REFUSED: {e}")
            return 1
        h = q.hypothesis
        lo, hi = pre["measurement_bounds"]
        declared = Consumed(qid, h.axis, "measurement", lo, hi, frozenset(pre["names"]))
        overlap = SearchBudget(reg).gate(declared, threshold=cfg.lab.overlap_threshold, supersedes=None, distinction=h.distinction)
        # the outcome-based measure (the share of trades whose result changes along an axis), re-run on the current
        # engine — the index's count-based proxy cannot see a stop that only changes exits
        sens = axis_sensitivity(template, q.sweep, world.definition, ctx=ctx if template.regime is not None else None, seed=a.seed)
        inert = [ax for ax, v in sens.items() if v == 0.0]
        powered = h.power_plan.available_n >= h.required_n
        supportable = len(pre["names"]) >= MIN_GROUPS
        cap = max_plateau_neighbourhood(q.sweep)
        plateau_ok = h.gates.plateau_cells <= cap
        alpha_refusal = budget.check(h.axis, h.tier, h.search_space_size)
        print(f"[{n}] {qid} · cell {cid} · {fam.universe} · {fam.regime} · {mechanism_key(row)} · {geometry(row)}")
        kin = [r for r in index["cells"] if family_of(grid, r) is fam and not r.get("refused") and r.get("margin_net") is not None]
        if kin:
            bm, be = max(kin, key=lambda r: r["margin_net"]), max(kin, key=lambda r: r["ev_net"] or float("-inf"))
            print(f"    the screen's winner in this family by margin over always-long (ADR-0045): {geometry(bm)} — margin {_ev(bm['margin_net'])}, "
                  f"EV {_ev(bm['ev_net'])}; by EV: {geometry(be)} — EV {_ev(be['ev_net'])}, margin {_ev(be['margin_net'])}")
        print(f"    the survey's screen: tier {tier_of(row)}, {_n(row['trades'])} trades, EV {_ev(row['ev_net'])} net R, always-long "
              f"{_ev(row.get('baseline_ev_net'))}, margin {_ev(row['margin_net'])}, one name out {_ev(row.get('leave_one_name_out_min'))}")
        print(f"    hypothesis (the R4.9 distinction): {h.distinction}")
        if h.survey.get("survey_hypothesis"):
            print(f"    the survey's cell file recorded it as: {h.survey['survey_hypothesis']} — the proposer's wording on the day it ran, "
                  f"stamped beside the claim")
        print(f"    template {template.hash[:12]} on {h.axis.value}; sweep {q.sweep.as_dict()} -> k = {h.search_space_size}")
        print(f"    pre-committed on {fam.universe}'s definition partition ({pre['definition_days']} days): {pre['definition_trades']} signals"
              f" ({pre['missed']} missed), rate {pre['rate_per_name_day']:.4f} per name-day; measurement {pre['measurement_days']} days over "
              f"{len(pre['names'])} names")
        print(f"    available_n {pre['available_n']}" + (f" -> effective {h.power_plan.available_n} at measured rho {h.power_plan.rho:.3f}"
                                                        if h.power_plan.rho is not None else " (clustering not measurable on the definition signals)"))
        if pre.get("thinnest_cell"):
            tc = pre["thinnest_cell"]
            print(f"    the sweep's thinnest cell on the definition partition: {tc['geometry']} — {_n(tc['definition_trades'])} trades, "
                  f"≈{_n(tc['available_n'])} on the measurement partition, against {_n(pre['template_available_n'])} from the template's signals; "
                  f"available_n is the lesser, because the guard at measurement counts the winner's own trades (M8.2)")
        print(f"    required_n per cell {h.required_n} at per-cell alpha {budget.rate(h.axis, h.tier):.4g}; floor {a.floor_ev:g} R at "
              f"{a.floor_frequency:g}/year; σ {h.power_plan.sigma_r:.3f} ({'declared' if a.sigma is not None else 'the cell'})")
        print(f"    spend {budget.spend_for(h.axis, h.tier, h.search_space_size):.4g} of {budget.remaining(h.axis):.4g} remaining on {h.axis.value}"
              + (f" — REFUSED: {alpha_refusal.reason}" if alpha_refusal is not None else ""))
        print("    " + ("POWERED" if powered else "UNDERPOWERED — registration would be refused (M8.2)"))
        if not supportable:
            print(f"    UNSUPPORTABLE — {len(pre['names'])} name(s); leave-one-out needs {MIN_GROUPS}")
        if not plateau_ok:
            print(f"    UNSUPPORTABLE — a plateau of {h.gates.plateau_cells} cells cannot fit this sweep (largest neighbourhood {cap})")
        print("    axis sensitivity on the definition partition (share of trades whose outcome changes along the axis): "
              + ", ".join(f"{ax} {v:.1%}" for ax, v in sens.items()))
        if inert:
            print(f"    INERT AXIS — {inert}: every cell along it produces the same trades; k charges for cells that are not distinct questions")
        if overlap is not None:
            print(f"    OVERLAP — {overlap.reason}")
        clean = powered and supportable and plateau_ok and not inert and overlap is None and alpha_refusal is None
        all_clean = all_clean and clean
        prepared.append((q, declared, pre))
    if cmd == "prepare":
        print("nothing registered, nothing spent." + ("" if all_clean else " Not every candidate is clean; registration would be refused."))
        return 0 if all_clean else 1
    if not all_clean:
        print("REFUSED: prepare is not clean for every id; a batch registers whole or not at all, before any spend")
        return 1
    if not a.yes:
        print("REFUSED: registration is a human act; pass --yes to confirm every id named (R4.8)")
        return 2
    queue = QuestionQueue(a.queue or a.register.with_name(f"{a.register.stem}-queue.jsonl"))
    for q, declared, pre in prepared:
        try:
            q = register_question(q, confirmation=Confirmation(a.by, human=True), budget=budget, register=reg,
                                  declared=declared, names=frozenset(pre["names"]))
        except Refused as e:
            print(f"REFUSED at {q.id}: {e}; earlier ids in this batch stand registered")
            return 1
        queue.enqueue(q)
        print(f"REGISTERED {q.id} by {a.by}: alpha spent {q.hypothesis.alpha_spent:.4g}; screened {_n(index['cell_count'])} cells stamped (N6); "
              f"queued at {queue.path}")
    print(f"Next: python -m occams loop {a.register} {a.archive} {queue.path} --config … --seed N")
    return 0


if __name__ == "__main__":
    sys.exit(main())
