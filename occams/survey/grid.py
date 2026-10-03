"""The survey grid (M12.2): a committed TOML under ``surveys/`` naming
mechanisms (entry kind and fixed params), regimes, universes, horizons and
the geometry every mechanism is swept across. **The file's sha256 is the
grid's identity**; a grid is never edited, only superseded by a new file
that names it. This module loads a grid or refuses it by name, expands it
into cells, and prints the count and the hash. It writes nothing and runs
nothing: the runner is M12.3, on the definition partition only.

    python -m occams survey show  GRID --register PATH [--plateau-cells N]
    python -m occams survey cells GRID --register PATH [--universe NAME] [--regime LABEL] [--limit N]
    python -m occams survey run|record|page …        (occams.survey.run, occams.survey.page)

A **cell** is one point: universe × regime × mechanism (kind, fixed params,
order, horizon) × hold × stop × target. Its hypothesis is the proposer's
mechanism sentence with the cell's numbers and the universe's subject
filled in; its id is the hash of that content, so the same cell in a later
grid has the same id. A **family** is the cells that share everything but
the swept geometry — the sweep a question registered from the survey would
carry (M12.5) — so the plateau guard (a plateau the sweep cannot hold,
found by Q-004) is applied to every family here, before anything runs, at
the plateau size the question command applies at registration (its default
is 4). The grid reads no config; the runner takes ``--config`` (M12.3).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterator

from occams.proposers.base import Sweep
from occams.proposers.price import PRICE_ENTRIES, entry_params, mechanism_sentence, price_template
from occams.spec.compile import CompileError, derived_capabilities, to_engine
from occams.spec.spec import EntryKind, Horizon, OrderType, Regime, Stop, StopKind, StrategySpec

REGIME_NONE = "none"
REGIME_LABELS = (REGIME_NONE,) + tuple(r.value for r in Regime)
ORDERS = {EntryKind.BREAKOUT_HIGH: ("stop", "market"), EntryKind.BREAKOUT_LOW: ("limit", "market")}  # else market only
NO_TARGET = 0.0


class GridRefused(ValueError):
    pass


def grid_sha(path: Path) -> str:
    """The grid's identity: the sha256 of the file's bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass(frozen=True)
class Family:
    """Cells that share everything but the swept geometry."""

    universe: str
    subject: str
    regime: str
    regime_index: str
    kind: EntryKind
    params: tuple[tuple[str, float], ...]
    order: OrderType
    horizon: Horizon
    stop_kind: StopKind
    stop_lookback: int
    holds: tuple[float, ...]
    stops: tuple[float, ...]
    targets: tuple[float, ...]      # () is the no-target family: the time exit alone

    @property
    def axis(self) -> str:
        return "regime" if self.regime != REGIME_NONE else "price_daily"

    @property
    def sweep(self) -> Sweep:
        axes = [("hold", self.holds), ("stop", self.stops)] + ([("target", self.targets)] if self.targets else [])
        return Sweep(tuple(axes))

    @property
    def size(self) -> int:
        return self.sweep.size

    def template(self) -> StrategySpec:
        spec = price_template(self.kind, hold_bars=int(self.holds[0]), horizon=self.horizon, **dict(self.params))
        spec = spec.replace(order_type=self.order)
        if self.stop_kind is StopKind.ATR:
            spec = spec.replace(stop=Stop(StopKind.ATR, spec.stop.value, self.stop_lookback))
        return spec

    def cells(self) -> Iterator[Cell]:
        for hold in self.holds:
            for stop in self.stops:
                for target in (self.targets or (NO_TARGET,)):
                    yield Cell(self, float(hold), float(stop), float(target))

    def describe(self) -> str:
        p = ", ".join(f"{k}={v:g}" for k, v in self.params)
        return (f"{self.universe} · {self.regime} · {self.kind.value}({p}) · {self.order.value} · {self.horizon.value} · "
                f"stop {self.stop_kind.value}" + (f"({self.stop_lookback})" if self.stop_kind is StopKind.ATR else "")
                + f" · target {'none' if not self.targets else 'R'} · sweep " + " × ".join(str(len(v)) for _, v in self.sweep.axes))


@dataclass(frozen=True)
class Cell:
    family: Family
    hold: float
    stop: float
    target: float       # 0 = none

    @property
    def spec(self) -> StrategySpec:
        """The cell's Strategy, ungated: the regime gate names a frozen
        classifier, which the runner attaches when one is (M12.3)."""
        from occams.question import apply_cell

        point = {"hold": self.hold, "stop": self.stop}
        if self.target:
            point["target"] = self.target
        spec = apply_cell(self.family.template(), point)
        return spec.replace(required_capabilities=derived_capabilities(spec))

    @property
    def id(self) -> str:
        f = self.family
        body = {"universe": f.universe, "regime": f.regime, "regime_index": f.regime_index if f.regime != REGIME_NONE else "",
                "spec": self.spec.identity()}
        return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    @property
    def hypothesis(self) -> str:
        f = self.family
        s = mechanism_sentence(f.kind, hold=int(self.hold), subject=f.subject, **dict(f.params))
        if f.horizon is Horizon.INTRADAY:
            s += " — day-boxed: the position ends at the close of the entry day"
        if f.regime != REGIME_NONE:
            s += f" — inside the {f.regime} regime of the classifier frozen on {f.regime_index} (F11)"
        return s

    def describe(self) -> str:
        f = self.family
        p = ", ".join(f"{k}={v:g}" for k, v in f.params)
        return (f"{self.id} · {f.universe} · {f.regime} · {f.kind.value}({p}) · {f.order.value} · {f.horizon.value} · "
                f"hold {self.hold:g} · stop {f.stop_kind.value} {self.stop:g} · target "
                f"{'none' if not self.target else f'{self.target:g}R'} · {self.hypothesis}")


@dataclass(frozen=True)
class Grid:
    path: Path
    sha: str
    name: str
    programme: int
    declared_on: str
    partition: str
    side: str
    baseline: str
    supersedes: str
    universes: tuple[tuple[str, str, str], ...]     # (name, subject, regime_index)
    regimes: tuple[str, ...]
    horizon_default: Horizon
    horizon_holds: tuple[tuple[str, tuple[float, ...]], ...]
    horizon_targets: tuple[tuple[str, tuple[float, ...]], ...]
    holds: tuple[float, ...]
    targets: tuple[float, ...]
    stops: tuple[tuple[StopKind, tuple[float, ...], int], ...]
    mechanisms: tuple[tuple[EntryKind, OrderType, tuple[Horizon, ...], tuple[tuple[tuple[str, float], ...], ...]], ...]
    families: tuple[Family, ...]

    @property
    def count(self) -> int:
        return sum(f.size for f in self.families)

    def cells(self) -> Iterator[Cell]:
        for f in self.families:
            yield from f.cells()

    def counts(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for f in self.families:
            row = out.setdefault(f.universe, {r: 0 for r in self.regimes})
            row[f.regime] += f.size
        return out

    def per_axis(self) -> dict[str, int]:
        out = {"price_daily": 0, "regime": 0}
        for f in self.families:
            out[f.axis] += f.size
        return out


# ---- loading ------------------------------------------------------------------

def _refuse(msg: str):
    raise GridRefused(msg)


def _kind(name: str) -> EntryKind:
    try:
        k = EntryKind(name)
    except ValueError:
        _refuse(f"kind {name!r} is not on the closed entry enum (M3.2); a kind is added only by ADR (ADR-0037)")
    if k not in PRICE_ENTRIES:
        _refuse(f"kind {name!r} is not a grid kind: it carries no mechanism sentence (the apparatus kinds are controls)")
    return k


def _numbers(v, *, what: str, positive: bool = True) -> tuple[float, ...]:
    if not isinstance(v, list) or not v:
        _refuse(f"{what} must be a non-empty list of numbers")
    out = tuple(float(x) for x in v)
    if positive and any(x <= 0 for x in out):
        _refuse(f"{what} must be positive; got {list(out)}")
    if len(set(out)) != len(out):
        _refuse(f"{what} repeats a value: {list(out)}")
    return out


def load(path: str | Path, *, register=None, plateau_cells: int | None = None) -> Grid:  # noqa: C901 — one refusal per way a grid can be wrong
    """Load a grid or refuse it by name. With ``register``, every universe
    must be a ``UniverseDeclared`` record; with ``plateau_cells``, every
    family's sweep must hold a plateau of that size. Every distinct template
    compiles."""
    path = Path(path)
    if not path.exists():
        _refuse(f"no grid at {path}")
    with open(path, "rb") as f:
        d = tomllib.load(f)
    g = d.get("grid") or _refuse("a grid has a [grid] table")
    for key in ("name", "programme", "declared_on", "partition", "side", "baseline"):
        if key not in g:
            _refuse(f"[grid] lacks {key!r}")
    if g["partition"] != "definition":
        _refuse(f"a survey reads the definition partition and nothing else (D13); got partition {g['partition']!r}")
    if g["side"] != "long":
        _refuse(f"the grid's templates are long-only; side {g['side']!r} is a new template by ADR")
    if g["baseline"] != "always_long":
        _refuse(f"the baseline is always_long at the cell's geometry (M12.3); got {g['baseline']!r}")

    universes = d.get("universes") or _refuse("a grid names at least one universe")
    us = []
    for name, u in universes.items():
        if not isinstance(u, dict) or "subject" not in u or "regime_index" not in u:
            _refuse(f"universe {name!r} needs a subject and a regime_index")
        if register is not None:
            from occams.data.partitions import declared_universe

            if declared_universe(register, name) is None:
                _refuse(f"universe {name!r} has no UniverseDeclared record in this Register (M12.1); declare it first")
        us += [(name, str(u["subject"]), str(u["regime_index"]))]

    labels = tuple(str(x) for x in (d.get("regimes") or {}).get("labels") or (REGIME_NONE,))
    for lab in labels:
        if lab not in REGIME_LABELS:
            _refuse(f"regime label {lab!r} is not one of {list(REGIME_LABELS)}")
    if len(set(labels)) != len(labels):
        _refuse("a regime label repeats")

    hz = d.get("horizons") or {}
    try:
        h_default = Horizon(hz.get("default", Horizon.MULTI_DAY.value))
    except ValueError:
        _refuse(f"horizon {hz.get('default')!r} is not one of {[h.value for h in Horizon]}")
    geo = d.get("geometry") or _refuse("a grid has a [geometry] table")
    holds = _numbers(geo.get("holds"), what="geometry.holds")
    targets = _numbers(geo.get("targets"), what="geometry.targets", positive=False)
    if any(t < 0 for t in targets):
        _refuse("a target is a positive multiple of R, or 0 for none")
    h_holds, h_targets = [], []
    for name, spec in hz.items():
        if name == "default":
            continue
        try:
            Horizon(name)
        except ValueError:
            _refuse(f"horizon {name!r} is not one of {[h.value for h in Horizon]}")
        if not isinstance(spec, dict) or "holds" not in spec:
            _refuse(f"[horizons.{name}] declares its holds")
        h_holds += [(name, _numbers(spec["holds"], what=f"horizons.{name}.holds"))]
        if "targets" in spec:
            t = _numbers(spec["targets"], what=f"horizons.{name}.targets", positive=False)
            if any(x < 0 for x in t):
                _refuse("a target is a positive multiple of R, or 0 for none")
            h_targets += [(name, t)]
    stops = []
    for s in geo.get("stops") or _refuse("geometry declares at least one stop kind"):
        try:
            sk = StopKind(str(s.get("kind")))
        except ValueError:
            _refuse(f"stop kind {s.get('kind')!r} is not one of {[k.value for k in StopKind]}")
        lb = int(s.get("lookback", 0))
        if sk is StopKind.ATR and lb < 1:
            _refuse("an ATR stop declares its lookback (at least one bar)")
        stops += [(sk, _numbers(s.get("values"), what=f"stops.{sk.value}.values"), lb)]

    mechs = []
    for m in d.get("mechanisms") or _refuse("a grid names at least one mechanism"):
        k = _kind(str(m.get("kind")))
        allowed = ORDERS.get(k, ("market",))
        order = str(m.get("order", "market"))
        if order not in allowed:
            _refuse(f"{k.value} enters as {'/'.join(allowed)}, not {order!r}: a level above the market rests as a stop, "
                    f"below as a limit, and no level is a market order (the v1.8 defect, A4)")
        hs = tuple(Horizon(h) for h in m.get("horizons", [h_default.value])) if all(
            h in {x.value for x in Horizon} for h in m.get("horizons", [h_default.value])) else _refuse(
            f"{k.value}: horizons must be among {[h.value for h in Horizon]}")
        ps = []
        for p in m.get("params") or _refuse(f"{k.value} declares its params"):
            try:
                ps += [entry_params(k, **{str(a): b for a, b in dict(p).items()})]
            except ValueError as e:
                _refuse(f"{k.value}: {e}")
        mechs += [(k, OrderType(order), hs, tuple(ps))]

    hold_by_horizon, targets_by_horizon = dict(h_holds), dict(h_targets)
    families = []
    for (uname, subject, ridx) in us:
        for lab in labels:
            for (k, order, hs, ps) in mechs:
                for p in ps:
                    for h in hs:
                        fh = hold_by_horizon.get(h.value, holds)
                        ft = targets_by_horizon.get(h.value, targets)
                        for (sk, vals, lb) in stops:
                            with_t = tuple(t for t in ft if t > 0)
                            fams = ([()] if NO_TARGET in ft else []) + ([with_t] if with_t else [])
                            for tg in fams:
                                families += [Family(uname, subject, lab, ridx, k, p, order, h, sk, lb, fh, vals, tg)]

    grid = Grid(path, grid_sha(path), str(g["name"]), int(g["programme"]), str(g["declared_on"]), str(g["partition"]),
                str(g["side"]), str(g["baseline"]), str(g.get("supersedes", "")), tuple(us), labels, h_default,
                tuple(h_holds), tuple(h_targets), holds, targets, tuple(stops), tuple(mechs), tuple(families))
    _compile_each_template(grid)
    if plateau_cells is not None:
        _plateau_each_family(grid, int(plateau_cells))
    return grid


def _compile_each_template(grid: Grid) -> int:
    """Every distinct template (universe- and regime-independent) compiles
    at its first geometry point, or the grid is refused by name."""
    seen: dict[str, str] = {}
    for f in grid.families:
        first = next(f.cells())
        key = first.spec.hash
        if key in seen:
            continue
        try:
            to_engine(first.spec)
        except CompileError as e:
            _refuse(f"family {f.describe()} does not compile: {e}")
        seen[key] = f.describe()
    return len(seen)


def _plateau_each_family(grid: Grid, cells: int) -> None:
    from occams.question import max_plateau_neighbourhood

    for f in grid.families:
        cap = max_plateau_neighbourhood(f.sweep)
        if cap < cells:
            _refuse(f"a plateau of {cells} cells cannot fit the sweep of family {f.describe()} (largest neighbourhood {cap}); "
                    f"a gate that cannot pass is decoration (Q-004)")


def readiness(grid: Grid, register) -> dict[str, str | None]:
    """Per universe: the frozen classifier's hash for its regime index, or
    None — gated cells wait on it (the runner attaches the gate, M12.3)."""
    rows = [r for r in register.records() if r["type"] == "ClassifierFrozen"]
    out = {}
    for name, _s, ridx in grid.universes:
        hits = [r for r in rows if r.get("index_name") == ridx]
        out[name] = hits[-1]["frozen_hash"] if hits else None
    return out


# ---- the command -----------------------------------------------------------------

def summary(grid: Grid, register=None, *, plateau_cells: int | None = None) -> list[str]:
    lines = [f"{grid.name} · sha {grid.sha[:12]} ({grid.sha}) · declared {grid.declared_on} · programme {grid.programme} · "
             f"{grid.partition} partition only · {grid.side} · baseline {grid.baseline}"
             + (f" · supersedes {grid.supersedes}" if grid.supersedes else "")]
    ready = readiness(grid, register) if register is not None else {}
    for name, subject, ridx in grid.universes:
        u = None
        if register is not None:
            from occams.data.partitions import declared_universe

            u = declared_universe(register, name)
        clf = ready.get(name)
        lines += [f"universe {name}: {len(u['members']) if u else '?'} names · subject \"{subject}\" · regime index {ridx}: "
                  + (f"classifier {clf[:12]} frozen" if clf else "no classifier frozen — gated cells wait")]
    mech = "; ".join(f"{k.value} {o.value} ×{len(ps)} [{', '.join(h.value for h in hs)}]" for k, o, hs, ps in grid.mechanisms)
    lines += [f"mechanisms ({len({k for k, *_ in grid.mechanisms})} kinds, {sum(len(ps) for *_, ps in grid.mechanisms)} parameterisations): {mech}"]
    ht = dict(grid.horizon_targets)
    hh = "; ".join(f"{h}: holds {', '.join(f'{x:g}' for x in v)}"
                   + (f", targets {', '.join('none' if t == 0 else f'{t:g}R' for t in ht[h])}" if h in ht else "")
                   for h, v in grid.horizon_holds)
    lines += [f"regimes: {', '.join(grid.regimes)} · horizons: {grid.horizon_default.value} holds {', '.join(f'{x:g}' for x in grid.holds)}"
              + (f"; {hh}" if hh else "")]
    st = " · ".join(f"{k.value} {', '.join(f'{x:g}' for x in v)}" + (f" (lookback {lb})" if k is StopKind.ATR else "") for k, v, lb in grid.stops)
    lines += [f"geometry: stops {st} · targets {', '.join('none' if t == 0 else f'{t:g}R' for t in grid.targets)}"]
    ax = grid.per_axis()
    lines += [f"families {len(grid.families):,} · cells {grid.count:,} · price_daily {ax['price_daily']:,} · regime {ax['regime']:,}"]
    lines += ["| universe | " + " | ".join(grid.regimes) + " | total |", "|---|" + "---|" * (len(grid.regimes) + 1)]
    for name, row in grid.counts().items():
        lines += [f"| {name} | " + " | ".join(f"{row[r]:,}" for r in grid.regimes) + f" | {sum(row.values()):,} |"]
    n = _compile_each_template(grid)
    lines += [f"compiled: {n} distinct templates, every one compiles at its first geometry point"]
    if plateau_cells is not None:
        lines += [f"plateau: every family's sweep holds a plateau of {int(plateau_cells)} cells (the question command's default is 4)"]
    else:
        lines += ["plateau: not checked — pass --plateau-cells to check every family's sweep"]
    waiting = sum(v for k, v in ax.items() if k == "regime") if ready and not all(ready.values()) else 0
    if waiting:
        lines += [f"gated cells ({waiting:,}) wait on a ClassifierFrozen for their regime index in this Register"]
    lines += ["nothing runs here: the runner is `python -m occams survey run` (M12.3), definition partition only, zero alpha"]
    return lines


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("run", "record", "inputs"):
        from occams.survey.run import main as run_main

        return run_main(argv)
    if argv and argv[0] == "page":
        from occams.survey.page import main as page_main

        return page_main(argv[1:])
    if argv and argv[0] == "candidates":
        from occams.survey.candidates import main as candidates_main

        return candidates_main(argv[1:])
    ap = argparse.ArgumentParser(prog="python -m occams survey")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("grid", type=Path)
    s.add_argument("--register", required=True, type=Path)
    s.add_argument("--plateau-cells", type=int, default=4, help="the plateau every family's sweep must hold (question's default: 4)")
    c = sub.add_parser("cells")
    c.add_argument("grid", type=Path)
    c.add_argument("--register", required=True, type=Path)
    c.add_argument("--universe", default=None)
    c.add_argument("--regime", default=None)
    c.add_argument("--limit", type=int, default=20)
    a = ap.parse_args(argv)

    from occams.register import Register

    reg = Register(a.register)
    plateau = getattr(a, "plateau_cells", None)
    try:
        grid = load(a.grid, register=reg, plateau_cells=plateau)
    except GridRefused as e:
        print(f"REFUSED: {e}")
        return 1
    if a.cmd == "show":
        for line in summary(grid, reg, plateau_cells=plateau):
            print(line)
        return 0
    shown = 0
    for cell in grid.cells():
        if a.universe and cell.family.universe != a.universe:
            continue
        if a.regime and cell.family.regime != a.regime:
            continue
        print(cell.describe())
        shown += 1
        if shown >= a.limit:
            break
    print(f"{shown} of {grid.count:,} cells shown · grid {grid.name} sha {grid.sha[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
