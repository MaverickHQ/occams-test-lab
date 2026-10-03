"""The batch survey runner (M12.3): every cell of a committed grid on the
**definition partition only**, at zero alpha, seeded, parallel across
cells, resumable from content-addressed results, and recorded in the
Register as ``SurveyRecorded`` when complete.

    python -m occams survey run GRID --archive DIR --register PATH --config PATH --out DIR --seed N
                               [--workers K] [--universe NAME] [--regime LABEL] [--limit N] [--dry-run] [--no-record]
    python -m occams survey record GRID --out DIR --register PATH --seed N

``run --no-record`` computes and writes the index but appends nothing, so
the compute can happen on any machine (a burst instance, M12.3); ``record``
verifies the results hash over the cell files on the machine that keeps
the Register and appends ``SurveyRecorded`` there. The index carries the
platform the cells were computed on; the cell files carry no platform.

The runner has no code path to the measurement partition: it slices the
definition partition and reads the measurement partition's *bounds* — day
counts for the power arithmetic — and nothing else (D13). Per cell: the
trades, EV gross and at bounded costs, the always-long baseline at the
same geometry and the margin over it, per-name and per-era breakdown,
measured ρ, the trades the measurement partition would afford after the
design effect, the trades each floor would need, and gate readiness. A
cell's file carries no timestamp, so the same grid, seed and archive give
byte-identical results. Nothing in a survey is a verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, pstdev

from occams.config import InformationAxis
from occams.data.actions import ActionSeries
from occams.spec.compile import derived_capabilities, to_engine
from occams.spec.spec import Entry, EntryKind, Horizon, OrderType, Regime, RegimeGate, Side
from occams.survey.grid import REGIME_NONE, Cell, Grid, GridRefused, load as load_grid
from occams.whatif import CELLS, FLOORS_WIDE, SIGMA_R

ERAS = 3
INDEX_FILE = "survey.json"
def engine_code_sha() -> str:
    """The hash of the engine's own code — what a cell's numbers depend on —
    so two surveys are byte-identical across commits that leave the engine
    alone. The commit is provenance and lives in the index, not the cells.
    Since M16.10 (ADR-0055) it is the import closure of the modules that
    measure, not a list kept by hand."""
    from occams import identity

    return identity.own_code_sha()


class SurveyRefused(RuntimeError):
    pass


@dataclass(frozen=True)
class World:
    """One universe's definition partition, and the numbers about the
    measurement partition that the power arithmetic needs — never its bars."""

    universe: str
    members: tuple[str, ...]
    span: tuple[int, int]
    definition_bounds: tuple[int, int]
    measurement_bounds: tuple[int, int]
    definition: dict
    actions: ActionSeries
    names_in_measurement: tuple[str, ...]

    @property
    def definition_days(self) -> int:
        return self.definition_bounds[1] - self.definition_bounds[0]

    @property
    def measurement_days(self) -> int:
        return self.measurement_bounds[1] - self.measurement_bounds[0]


def survey_names(grid, register) -> frozenset[str]:
    """Every series a survey of ``grid`` reads: the members of its universes
    (the latest ``UniverseDeclared`` under each name) and the frozen
    classifier's index. What the burst uploads and what the runner asks the
    archive for — nothing else (M14.7)."""
    from occams.data.partitions import declared_universe

    names: set[str] = set()
    for u, _s, _r in grid.universes:
        d = declared_universe(register, u)
        if d is None:
            raise SurveyRefused(f"universe {u!r} has no UniverseDeclared record in this Register (M12.1)")
        names.update(d["members"])
    clf = [r for r in register.records() if r["type"] == "ClassifierFrozen"]
    if clf:
        names.add(clf[-1]["index_name"])
    return frozenset(names)


def survey_inputs(grid, register, archive) -> list[Path]:
    """The files a survey box needs: the manifest whole (it is a chain) and the
    latest bars of every name in ``survey_names`` (M14.7)."""
    return [archive.root / "manifest.jsonl", *archive.bar_paths(survey_names(grid, register))]


def _inputs_main(argv: list[str]) -> int:
    from occams.data.archive import BarArchive, NotArchived
    from occams.register import Register

    ap = argparse.ArgumentParser(prog="python -m occams survey inputs")
    ap.add_argument("grid", type=Path)
    ap.add_argument("--register", required=True, type=Path)
    ap.add_argument("--archive", required=True, type=Path)
    a = ap.parse_args(argv)
    reg = Register(a.register)
    try:
        grid = load_grid(a.grid, register=reg)
        paths = survey_inputs(grid, reg, BarArchive(a.archive))
    except (GridRefused, SurveyRefused, NotArchived) as e:
        print(f"REFUSED: {e}")
        return 1
    for p in paths:
        print(p)
    return 0


def build_world(name: str, *, latest, register, parts) -> World:
    from occams.data.partitions import declared_universe, span_for

    u = declared_universe(register, name)
    if u is None:
        raise SurveyRefused(f"universe {name!r} has no UniverseDeclared record in this Register (M12.1)")
    members = tuple(u["members"])
    missing = [m for m in members if m not in latest]
    if missing:
        raise SurveyRefused(f"universe {name!r} has members not in the archive: {missing}; ingest them first")
    bars = {m: latest[m][0] for m in members}
    span = span_for(register, bars, parts, universe=name)          # the universe's frozen calendar (ADR-0038)
    b = parts.bounds_over(*span)
    definition, actions = {}, ActionSeries()
    for m in members:
        sliced, _bounds = parts.slice(bars[m], "definition", span=span)   # the only slice the runner ever takes (D13)
        if sliced.n:
            definition[m] = sliced
            actions = ActionSeries(actions.actions + latest[m][1].actions)
    if not definition:
        raise SurveyRefused(f"universe {name!r}: no member has bars in the definition partition")
    lo, hi = b["measurement"]
    in_meas = tuple(m for m in members if bars[m].day[0] < hi and bars[m].day[-1] >= lo)   # from day numbers, not bars
    return World(name, members, span, b["definition"], (lo, hi), definition, actions, in_meas)


# ---- one cell --------------------------------------------------------------

def _engine_for(horizon: Horizon):
    from occams.engine import day_boxed, position_boxed

    return position_boxed if horizon is Horizon.MULTI_DAY else day_boxed


def gated_spec(cell: Cell, classifier_hash: str):
    spec = cell.spec
    if cell.family.regime == REGIME_NONE:
        return spec
    return spec.replace(regime=RegimeGate(classifier_hash, Regime(cell.family.regime), cell.family.regime_index),
                        axis=InformationAxis.REGIME)


def baseline_spec(cell: Cell, classifier_hash: str):
    """Always-long at the cell's geometry: the same exits, stop, horizon and
    gate, a market order on every box."""
    spec = gated_spec(cell, classifier_hash)
    spec = spec.replace(entries=(Entry(EntryKind.ALWAYS, Side.LONG, ()),), order_type=OrderType.MARKET)
    return spec.replace(required_capabilities=derived_capabilities(spec))


def baseline_key(cell: Cell) -> str:
    f = cell.family
    body = [f.universe, f.regime, f.regime_index if f.regime != REGIME_NONE else "", f.horizon.value, f.stop_kind.value,
            f.stop_lookback, cell.hold, cell.stop, cell.target]
    return hashlib.sha256(json.dumps(body).encode("utf-8")).hexdigest()[:16]


def _run(spec, world: World, *, seed: int, costs, ctx):
    """The engine's trades, with every entry the fill auditor refused — a
    halt, a flat bar, an unexplained gap (M5.5) — carried as ``missed``
    rather than opened (ADR-0041). Only a family with no auditor refuses
    the run, and a survey records that as the cell's outcome by name
    rather than stopping the batch."""
    from occams.costs.auditors import UnauditedFamily

    compiled = to_engine(spec)
    try:
        trades = _engine_for(spec.horizon).run(compiled, world.definition, seed=seed, actions=world.actions, costs=costs,
                                               regime=ctx if spec.regime is not None else None)
    except UnauditedFamily as e:
        return compiled, None, str(e)
    return compiled, trades, ""


def _missed(trades) -> dict:
    """The entries the auditor refused, counted and named (ADR-0041)."""
    missed = tuple(getattr(trades, "missed", ()))
    by: dict[str, int] = {}
    for m in missed:
        by[m.name] = by.get(m.name, 0) + 1
    return {"missed": len(missed), "missed_by_name": dict(sorted(by.items())),
            "missed_trades": [{"name": m.name, "day": m.day, "bar": m.bar_index, "reason": m.reason} for m in missed]}


def _eras(bounds: tuple[int, int]) -> list[tuple[int, int]]:
    lo, hi = bounds
    step = (hi - lo) / ERAS
    return [(int(lo + i * step), int(lo + (i + 1) * step) if i < ERAS - 1 else hi) for i in range(ERAS)]


def _mean(xs) -> float | None:
    xs = list(xs)
    return fmean(xs) if xs else None


def summarise_trades(trades, world: World) -> dict:
    net = [t.net_r for t in trades]
    gross = [t.gross_r for t in trades]
    by_name: dict[str, list[float]] = {}
    for t in trades:
        by_name.setdefault(t.name, []).append(t.net_r)
    per_name = {n: {"n": len(v), "ev_net": fmean(v)} for n, v in sorted(by_name.items())}
    loo = None
    if len(by_name) >= 3:
        loo = min(_mean(t.net_r for t in trades if t.name != n) for n in by_name)
    eras = []
    for lo, hi in _eras(world.definition_bounds):
        v = [t.net_r for t in trades if lo <= t.day < hi]
        eras.append({"bounds": [lo, hi], "n": len(v), "ev_net": _mean(v)})
    loeo = [_mean(t.net_r for t in trades if not (e["bounds"][0] <= t.day < e["bounds"][1])) for e in eras]
    return {"trades": len(trades), "names_traded": len(by_name), "ev_gross": _mean(gross), "ev_net": _mean(net),
            "sigma_net": pstdev(net) if len(net) >= 2 else None, "per_name": per_name, "leave_one_name_out_min": loo,
            "eras": eras, "leave_one_era_out": loeo,
            "reasons": {r: sum(1 for t in trades if t.reason == r) for r in sorted({t.reason for t in trades})},
            **_missed(trades)}


def power_arithmetic(trades, world: World, *, axis: str, cfg, names: int) -> dict:
    from occams.core import power
    from occams.proposers.clustering import measure_clustering
    from occams.proposers.regime import ClusterLevel

    def_bars = sum(b.n for b in world.definition.values())
    rate = len(trades) / max(1, def_bars)
    n_raw = int(rate * world.measurement_days * len(world.names_in_measurement) * (252 / 365.25))
    rho = cluster = None
    try:
        cm = measure_clustering([t.as_trade() for t in trades], level=ClusterLevel.INDEX if names > 1 else ClusterLevel.INSTRUMENT,
                                provenance="survey: definition partition")
        rho, cluster = cm.rho, cm.cluster_size
    except ValueError:
        pass
    deff = 1.0 + (max(1.0, cluster) - 1.0) * min(max(0.0, rho), 0.999) if rho is not None else 1.0
    n_eff = int(n_raw / deff) if deff > 1.0 else n_raw
    a = cfg.alpha.axes.get(InformationAxis(axis))
    alpha = a.mechanism_test_alpha if a is not None else 0.0
    net = [t.net_r for t in trades]
    sigma = pstdev(net) if len(net) >= 2 and pstdev(net) > 0 else SIGMA_R
    required = {}
    if alpha > 0:
        for f in FLOORS_WIDE:
            required[f"{f:g}"] = {str(k): power.n_for_mean_shift(f / sigma, alpha=alpha / k, power=0.8) for k in CELLS}
    affordable = {str(k): next((f"{f:g}" for f in FLOORS_WIDE if required.get(f"{f:g}", {}).get(str(k), 10**12) <= n_eff), None)
                  for k in CELLS} if required else {}
    return {"rate_per_name_day": rate, "definition_bars": def_bars, "measurement_days": world.measurement_days,
            "names_in_measurement": len(world.names_in_measurement), "n_raw_measurement": n_raw, "rho": rho,
            "cluster_size": cluster, "design_effect": deff, "n_eff_measurement": n_eff, "sigma_used": sigma,
            "alpha_axis_has_budget": alpha > 0, "required_n": required, "lowest_affordable_floor": affordable}


def compute_cell(cell: Cell, world: World, *, seed: int, costs, ctx, classifier_hash: str, cfg, baseline: dict,
                 registered_questions: int) -> dict:
    from occams.question import max_plateau_neighbourhood

    spec = gated_spec(cell, classifier_hash)
    compiled, trades, refused = _run(spec, world, seed=seed, costs=costs, ctx=ctx)
    f = cell.family
    s = summarise_trades(trades or (), world)
    p = power_arithmetic(trades or (), world, axis=f.axis, cfg=cfg, names=len(world.definition))
    margin = None if refused or s["ev_net"] is None or baseline["ev_net"] is None else s["ev_net"] - baseline["ev_net"]
    return {
        "cell": cell.id, "refused": refused, "universe": f.universe, "regime": f.regime, "regime_index": f.regime_index if f.regime != REGIME_NONE else "",
        "classifier": classifier_hash if f.regime != REGIME_NONE else "", "kind": f.kind.value, "params": dict(f.params),
        "order": f.order.value, "horizon": f.horizon.value, "hold": cell.hold, "stop_kind": f.stop_kind.value, "stop": cell.stop,
        "stop_lookback": f.stop_lookback, "target": cell.target, "axis": f.axis, "spec_hash": compiled.spec_hash,
        "engine": compiled.engine, "engine_code_sha": engine_code_sha(), "seed": seed, "hypothesis": cell.hypothesis,
        "partition": {"name": "definition", "bounds": list(world.definition_bounds), "days": world.definition_days,
                      "names": sorted(world.definition)},
        **s, "baseline": baseline, "margin_net": margin, **p,
        "readiness": {"names_ok": len(world.definition) >= 3, "plateau_ok": max_plateau_neighbourhood(f.sweep) >= 4,
                      "registered_questions_in_register": registered_questions},
    }


def compute_baseline(cell: Cell, world: World, *, seed: int, costs, ctx, classifier_hash: str) -> dict:
    spec = baseline_spec(cell, classifier_hash)
    compiled, trades, refused = _run(spec, world, seed=seed, costs=costs, ctx=ctx)
    trades = trades or ()
    net = [t.net_r for t in trades]
    m = _missed(trades)
    return {"key": baseline_key(cell), "spec_hash": compiled.spec_hash, "trades": len(trades),
            "ev_gross": _mean(t.gross_r for t in trades), "ev_net": _mean(net), "refused": refused,
            "missed": m["missed"], "missed_by_name": m["missed_by_name"]}


# ---- the batch -------------------------------------------------------------------

def _dump(path: Path, obj: dict) -> str:
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _header_ok(path: Path, *, grid_sha: str, seed: int) -> bool:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return d.get("grid_sha") == grid_sha and d.get("seed") == seed


_STATE: dict = {}


def _init(state: dict) -> None:
    _STATE.update(state)


def _task_baseline(args):
    fi, hold, stop, target = args
    st = _STATE
    cell = Cell(st["grid"].families[fi], hold, stop, target)
    out = st["out"] / "baselines" / f"{baseline_key(cell)}.json"
    if out.exists() and _header_ok(out, grid_sha=st["grid_sha"], seed=st["seed"]):
        return baseline_key(cell), False
    row = compute_baseline(cell, st["worlds"][cell.family.universe], seed=st["seed"], costs=st["costs"], ctx=st["ctx"],
                           classifier_hash=st["classifier_hash"])
    _dump(out, {**row, "grid_sha": st["grid_sha"], "seed": st["seed"]})
    return row["key"], True


def _task_cell(args):
    fi, hold, stop, target = args
    st = _STATE
    cell = Cell(st["grid"].families[fi], hold, stop, target)
    out = st["out"] / "cells" / f"{cell.id}.json"
    if out.exists() and _header_ok(out, grid_sha=st["grid_sha"], seed=st["seed"]):
        return cell.id, False
    base = json.loads((st["out"] / "baselines" / f"{baseline_key(cell)}.json").read_text(encoding="utf-8"))
    row = compute_cell(cell, st["worlds"][cell.family.universe], seed=st["seed"], costs=st["costs"], ctx=st["ctx"],
                       classifier_hash=st["classifier_hash"], cfg=st["cfg"],
                       baseline={**{k: base.get(k, "") for k in ("key", "spec_hash", "trades", "ev_gross", "ev_net", "refused")},
                                 "missed": base.get("missed", 0), "missed_by_name": base.get("missed_by_name", {})},
                       registered_questions=st["registered_questions"])
    _dump(out, {**row, "grid_sha": st["grid_sha"]})
    return cell.id, True


def _map(fn, tasks, *, workers: int, state: dict):
    if workers <= 1:
        _init(state)
        for t in tasks:
            yield fn(t)
        return
    import multiprocessing as mp

    ctx = mp.get_context("fork")
    with ctx.Pool(processes=workers, initializer=_init, initargs=(state,)) as pool:
        yield from pool.imap_unordered(fn, tasks, chunksize=4)


def results_sha(out: Path) -> tuple[str, int]:
    files = sorted((out / "cells").glob("*.json"))
    h = hashlib.sha256()
    for f in files:
        h.update(f.stem.encode("utf-8") + b" " + hashlib.sha256(f.read_bytes()).hexdigest().encode("utf-8") + b"\n")
    return h.hexdigest(), len(files)


def axis_sensitivity_rows(rows: list[dict]) -> None:
    """Per cell, for each swept axis, the largest relative change in trade
    count across that axis's values with the other axes held at the cell's
    point — from the family's own cells, no re-run. Written into the index."""
    fam: dict[tuple, list[dict]] = {}
    for r in rows:
        key = (r["universe"], r["regime"], r["kind"], json.dumps(r["params"], sort_keys=True), r["order"], r["horizon"],
               r["stop_kind"], r["target"] > 0)
        fam.setdefault(key, []).append(r)
    for members in fam.values():
        for r in members:
            sens = {}
            for axis in ("hold", "stop", "target"):
                if axis == "target" and not r["target"]:
                    continue
                same = [m for m in members if all(m[o] == r[o] for o in ("hold", "stop", "target") if o != axis)]
                counts = [m["trades"] for m in same]
                if len(counts) >= 2 and max(counts) > 0:
                    sens[axis] = (max(counts) - min(counts)) / max(counts)
            r["axis_sensitivity"] = sens


def write_index(out: Path, *, grid: Grid, seed: int, classifier_hash: str, worlds: dict, engine_shas: dict) -> dict:
    rows = []
    for f in sorted((out / "cells").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        rows.append({k: d.get(k) for k in ("cell", "refused", "universe", "regime", "kind", "params", "order", "horizon", "hold", "stop_kind",
                                        "stop", "target", "axis", "spec_hash", "trades", "names_traded", "ev_gross", "ev_net",
                                        "sigma_net", "margin_net", "leave_one_name_out_min", "leave_one_era_out", "rho",
                                        "n_eff_measurement", "lowest_affordable_floor", "readiness", "hypothesis")}
                    | {"baseline_ev_net": d["baseline"]["ev_net"], "baseline_trades": d["baseline"]["trades"],
                       "baseline_refused": d["baseline"].get("refused", ""), "eras": [e["ev_net"] for e in d["eras"]],
                       "missed": d.get("missed", 0), "missed_by_name": d.get("missed_by_name", {}),
                       "baseline_missed": d["baseline"].get("missed", 0)})
    axis_sensitivity_rows(rows)
    rows.sort(key=lambda r: r["cell"])
    sha, n = results_sha(out)
    refused = {u: sum(1 for r in rows if r["universe"] == u and r["refused"]) for u in worlds}
    base_refused = {u: sum(1 for r in rows if r["universe"] == u and r["baseline_refused"]) for u in worlds}
    # ADR-0041: an unobtainable entry is a missed trade, counted per universe beside the trade count
    missed = {u: sum(r["missed"] for r in rows if r["universe"] == u) for u in worlds}
    cells_missed = {u: sum(1 for r in rows if r["universe"] == u and r["missed"]) for u in worlds}
    base_missed = {u: sum(r["baseline_missed"] for r in rows if r["universe"] == u) for u in worlds}
    import platform as _platform

    import numpy as _np

    index = {"grid": grid.name, "grid_sha": grid.sha, "results_sha": sha, "cell_count": n, "seed": seed,
             "platform": {"python": _platform.python_version(), "numpy": _np.__version__, "machine": _platform.machine(),
                          "system": _platform.system()},
             "refused_cells": refused, "cells_with_refused_baseline": base_refused,
             "missed_trades": missed, "cells_with_missed": cells_missed, "baselines_missed_trades": base_missed,
             "classifier_hash": classifier_hash, "engine_shas": engine_shas,
             "universes": {u: {"names": list(w.definition), "definition_bounds": list(w.definition_bounds),
                               "measurement_days": w.measurement_days} for u, w in worlds.items()},
             "cells": rows}
    _dump(out / INDEX_FILE, index)
    return index


def record_survey(grid: Grid, *, out: Path, register, seed: int, log=print) -> dict:
    """Verify a complete survey's results on disk and append ``SurveyRecorded``
    here: every cell file carries this grid's hash and this seed, the count is
    the grid's, and the results hash recomputed over the files is the index's."""
    from occams.stopping import describe, stopping_record

    stop = stopping_record(register)
    if stop:   # ADR-0033, M12.8: a stopped programme records nothing more
        raise SurveyRefused(f"the programme is stopped — {describe(stop)}; nothing is recorded after that record")
    index_path = out / INDEX_FILE
    if not index_path.exists():
        raise SurveyRefused(f"no {INDEX_FILE} in {out}: the run did not complete")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("grid_sha") != grid.sha or int(index.get("seed", -1)) != int(seed):
        raise SurveyRefused(f"the index in {out} is for grid {str(index.get('grid_sha'))[:12]} seed {index.get('seed')}, "
                            f"not {grid.sha[:12]} seed {seed}")
    sha, n = results_sha(out)
    if sha != index["results_sha"] or n != index["cell_count"]:
        raise SurveyRefused(f"the cell files in {out} do not match the index: {n} files, results {sha[:12]} against "
                            f"{index['cell_count']} and {index['results_sha'][:12]}")
    if n != grid.count:
        raise SurveyRefused(f"{n} cell files for a grid of {grid.count} cells: the survey is not complete or the directory mixes runs")
    foreign = [f.name for f in (out / "cells").glob("*.json") if not _header_ok(f, grid_sha=grid.sha, seed=seed)]
    if foreign:
        raise SurveyRefused(f"{len(foreign)} cell files carry another grid or seed, e.g. {foreign[0]}")
    dup = [r for r in register.records() if r["type"] == "SurveyRecorded" and r["grid_sha"] == grid.sha
           and r["results_sha"] == sha and r["seed"] == int(seed)]
    if dup:
        log("already recorded: the same grid, seed and results")
        return {**index, "recorded": False}
    universes = tuple(index["universes"])
    calendars = tuple((u, int(v["definition_bounds"][0]), int(v["definition_bounds"][1])) for u, v in index["universes"].items())
    register.append(register.SurveyRecorded(
        grid.name, grid.sha, sha, n, universes, calendars, index.get("classifier_hash", ""), index.get("engine_shas", {}),
        int(seed), str(out), reason="definition partition only; zero alpha; nothing here is a verdict (M12.3); computed on "
        + " ".join(f"{k} {v}" for k, v in index.get("platform", {}).items())))
    log("SurveyRecorded appended: definition partition only, zero alpha")
    return {**index, "recorded": True}


def run_survey(grid: Grid, *, archive, register, cfg, out: Path, seed: int, workers: int = 1, universe: str | None = None,
               regime: str | None = None, limit: int | None = None, dry_run: bool = False, record: bool = True,
               log=print) -> dict:
    from occams.costs.equity import EquityCosts, InstrumentClass
    from occams.data.partitions import Partitions
    from occams.engine.regime_gate import RegimeContext
    from occams.proposers.regime import frozen

    if not dry_run:
        from occams import identity

        identity.require_clean("a survey")     # ADR-0055: dirty or unknown code does not screen either
    parts = Partitions.from_config(cfg)
    latest = archive.latest_bars(names=survey_names(grid, register))     # M14.7: the grid's names, nothing else
    wanted = [u for u, _s, _r in grid.universes if universe is None or u == universe]
    if not wanted:
        raise SurveyRefused(f"universe {universe!r} is not in the grid")
    worlds = {u: build_world(u, latest=latest, register=register, parts=parts) for u in wanted}
    clf = frozen(register)
    ctx = RegimeContext.from_register(register, archive) if clf is not None else None
    classifier_hash = clf.frozen_hash if clf is not None else ""
    if ctx is not None:
        for u, _s, ridx in grid.universes:
            if u in worlds and ridx != ctx.index_name:
                raise SurveyRefused(f"the frozen classifier labels {ctx.index_name!r}; the grid reads {ridx!r} for {u}")
    costs = EquityCosts.declared(InstrumentClass.US_LARGE, instrument_currency="USD", account_currency=cfg.capital.currency).bound()
    registered = sum(1 for r in register.records() if r["type"] == "HypothesisRegistered")

    families = [(i, f) for i, f in enumerate(grid.families) if f.universe in worlds and (regime is None or f.regime == regime)]
    waiting = [f for _i, f in families if f.regime != REGIME_NONE and ctx is None]
    families = [(i, f) for i, f in families if not (f.regime != REGIME_NONE and ctx is None)]
    tasks = [(i, c.hold, c.stop, c.target) for i, f in families for c in f.cells()]
    if limit is not None:
        tasks = tasks[:limit]
    partial = universe is not None or regime is not None or limit is not None or bool(waiting)
    (out / "cells").mkdir(parents=True, exist_ok=True)
    (out / "baselines").mkdir(parents=True, exist_ok=True)
    state = {"grid": grid, "grid_sha": grid.sha, "seed": seed, "worlds": worlds, "costs": costs, "ctx": ctx,
             "classifier_hash": classifier_hash, "cfg": cfg, "out": out, "registered_questions": registered}
    bkeys = {}
    for t in tasks:
        cell = Cell(grid.families[t[0]], t[1], t[2], t[3])
        bkeys.setdefault(baseline_key(cell), t)
    log(f"survey {grid.name} · grid {grid.sha[:12]} · seed {seed} · {len(worlds)} universe(s) · {len(tasks):,} cells, "
        f"{len(bkeys):,} baselines · classifier {classifier_hash[:12] or 'none (gated cells wait)'} · workers {workers} · out {out}")
    if waiting:
        log(f"gated cells wait on a ClassifierFrozen for their regime index: {sum(f.size for f in waiting):,} cells not run")
    if dry_run:
        return {"cells": len(tasks), "baselines": len(bkeys), "waiting": sum(f.size for f in waiting), "dry_run": True}
    done = skipped = 0
    for _key, computed in _map(_task_baseline, list(bkeys.values()), workers=workers, state=state):
        done += computed
        skipped += not computed
    log(f"baselines: {done:,} computed, {skipped:,} already there")
    done = skipped = 0
    for n, (_cid, computed) in enumerate(_map(_task_cell, tasks, workers=workers, state=state), 1):
        done += computed
        skipped += not computed
        if n % 500 == 0:
            log(f"  {n:,}/{len(tasks):,} cells ({done:,} computed, {skipped:,} already there)")
    log(f"cells: {done:,} computed, {skipped:,} already there")
    engine_shas = {"engine_code_sha": engine_code_sha()}
    for h in {f.horizon for _i, f in families}:
        fam = next(f for _i, f in families if f.horizon is h)
        c = to_engine(next(fam.cells()).spec)
        engine_shas[c.engine] = c.engine_sha   # the commit, as provenance
    index = write_index(out, grid=grid, seed=seed, classifier_hash=classifier_hash, worlds=worlds, engine_shas=engine_shas)
    log(f"results {index['results_sha'][:12]} over {index['cell_count']:,} cell files · index {out / INDEX_FILE}")
    if any(index["refused_cells"].values()) or any(index["cells_with_refused_baseline"].values()):
        log(f"refused by name (no auditor for the family), per universe — cells: {index['refused_cells']} · baselines: {index['cells_with_refused_baseline']}")
    if any(index["missed_trades"].values()) or any(index["baselines_missed_trades"].values()):
        log(f"missed trades — entries the fill auditor refused, not opened (ADR-0041), per universe — in cells: {index['missed_trades']} "
            f"over {index['cells_with_missed']} cells · in baselines: {index['baselines_missed_trades']}")
    if partial:
        log("partial run (a filter, a limit, or gated cells waiting): nothing recorded; a complete run records SurveyRecorded")
        return {**index, "recorded": False}
    if not record:
        log("complete; not recorded here (--no-record): run `survey record` on the machine that keeps the Register")
        return {**index, "recorded": False}
    return record_survey(grid, out=out, register=register, seed=seed, log=log)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "record":
        return _record_main(argv[1:])
    if argv and argv[0] == "inputs":
        return _inputs_main(argv[1:])
    if argv and argv[0] == "run":
        argv = argv[1:]
    ap = argparse.ArgumentParser(prog="python -m occams survey run")
    ap.add_argument("grid", type=Path)
    ap.add_argument("--archive", required=True, type=Path)
    ap.add_argument("--register", required=True, type=Path)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default=None, type=Path, help="default: <archive>/surveys/<grid>-seed<N>")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--universe", default=None)
    ap.add_argument("--regime", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-record", action="store_true", help="write the index, append nothing: record on the Register's machine")
    a = ap.parse_args(argv)

    from occams.config import ConfigRefused, load
    from occams.data.archive import BarArchive
    from occams.register import Register

    try:
        cfg = load(a.config)
    except ConfigRefused as e:
        print("REFUSED: the configuration does not load.")
        for r in e.reasons:
            print(f"  - {r}")
        return 2
    reg = Register(a.register)
    try:
        grid = load_grid(a.grid, register=reg, plateau_cells=4)
    except GridRefused as e:
        print(f"REFUSED: {e}")
        return 1
    out = a.out or (a.archive / "surveys" / f"{grid.name}-seed{a.seed}")
    try:
        res = run_survey(grid, archive=BarArchive(a.archive), register=reg, cfg=cfg, out=out, seed=a.seed, workers=a.workers,
                         universe=a.universe, regime=a.regime, limit=a.limit, dry_run=a.dry_run, record=not a.no_record)
    except SurveyRefused as e:
        print(f"REFUSED: {e}")
        return 1
    return 0 if res.get("recorded") or res.get("dry_run") or a.universe or a.regime or a.limit or a.no_record else 1


def _record_main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m occams survey record")
    ap.add_argument("grid", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--register", required=True, type=Path)
    ap.add_argument("--seed", type=int, required=True)
    a = ap.parse_args(argv)
    from occams.register import Register

    reg = Register(a.register)
    try:
        grid = load_grid(a.grid, register=reg, plateau_cells=4)
        res = record_survey(grid, out=a.out, register=reg, seed=a.seed)
    except (GridRefused, SurveyRefused) as e:
        print(f"REFUSED: {e}")
        return 1
    return 0 if res.get("recorded") else 1


if __name__ == "__main__":
    sys.exit(main())
