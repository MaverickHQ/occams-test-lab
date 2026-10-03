"""``to_engine(spec)`` — the authoritative compiler (F2). It refuses what a
venue would refuse and what the donor learned the hard way:

* a spec without a positive stop (D5, ADR-0003);
* an order type that contradicts its entry geometry — the v1.8 defect, a
  buy stop below market, which a hand-written engine and a hand-written
  renderer agreed on for nine versions (A4, M3.4);
* a capability the spec needs but did not declare (ADR-0018 — capabilities
  are identity, so deriving them silently would change the hash behind the
  author's back);
* a horizon routed to the wrong simulator (D6, M9.3).

The compiled object is deterministic and carries ``engine_sha``; the seed
is run context and is passed at run time, never baked in.
"""

from __future__ import annotations

from dataclasses import dataclass

from occams.config import InformationAxis
from occams.spec.spec import (Capability, EntryKind, ExitKind, Horizon, OrderType, Side, StopKind,
                              StrategySpec)


class CompileError(ValueError):
    pass


# Where the entry level sits relative to the market at decision time.
ABOVE, BELOW, NONE = "above", "below", "none"
GEOMETRY = {
    EntryKind.BREAKOUT_HIGH: {Side.LONG: ABOVE, Side.SHORT: ABOVE},
    EntryKind.BREAKOUT_LOW: {Side.LONG: BELOW, Side.SHORT: BELOW},
    EntryKind.CLOSE_ABOVE_MA: {Side.LONG: NONE, Side.SHORT: NONE},
    EntryKind.CLOSE_BELOW_MA: {Side.LONG: NONE, Side.SHORT: NONE},
    EntryKind.ALWAYS: {Side.LONG: NONE, Side.SHORT: NONE},
    EntryKind.COIN_FLIP: {Side.LONG: NONE, Side.SHORT: NONE},
    # ADR-0037: market entries on the next open; no level, so nothing for a stop or limit to sit at
    EntryKind.DOWN_RUN: {Side.LONG: NONE, Side.SHORT: NONE},
    EntryKind.RETURN_BELOW: {Side.LONG: NONE, Side.SHORT: NONE},
    EntryKind.PULLBACK_IN_TREND: {Side.LONG: NONE, Side.SHORT: NONE},
}
REQUIRED_PARAMS = {
    EntryKind.BREAKOUT_HIGH: ("lookback",), EntryKind.BREAKOUT_LOW: ("lookback",),
    EntryKind.CLOSE_ABOVE_MA: ("lookback",), EntryKind.CLOSE_BELOW_MA: ("lookback",),
    EntryKind.ALWAYS: (), EntryKind.COIN_FLIP: ("seed",),
    EntryKind.DOWN_RUN: ("runs",), EntryKind.RETURN_BELOW: ("lookback", "percent"),
    EntryKind.PULLBACK_IN_TREND: ("short", "long"),
}


@dataclass(frozen=True)
class CompiledStrategy:
    spec: StrategySpec
    spec_hash: str
    engine: str
    engine_sha: str

    def run(self, bars_by_name, *, seed: int, cost_in_r: float = 0.0, **kw):
        """Dispatch by the horizon's engine (D6, M9.3)."""
        if self.engine == "position_boxed":
            from occams.engine import position_boxed as eng
        else:
            from occams.engine import day_boxed as eng
        return eng.run(self, bars_by_name, seed=seed, cost_in_r=cost_in_r, **kw)


def _geometry_check(spec: StrategySpec) -> None:
    ot = spec.order_type
    for e in spec.entries:
        where = GEOMETRY[e.kind][e.side]
        for p in REQUIRED_PARAMS[e.kind]:
            if p not in dict(e.params):
                raise CompileError(f"{e.kind.value} entry needs parameter {p!r}")
        if where == NONE:
            if ot is not OrderType.MARKET:
                raise CompileError(f"{e.kind.value} names no level, so its order must be market, not {ot.value}")
            continue
        if ot is OrderType.MARKET:
            continue  # enter at the next open once the rule has fired: no level, no geometry
        # level-based entries: buy above = stop, buy below = limit; mirrored for sells
        if e.side is Side.LONG:
            if where == BELOW and ot in (OrderType.STOP, OrderType.STOP_LIMIT):
                raise CompileError("a buy stop below market triggers instantly — the v1.8 defect (A4); "
                                   "a level below market is a limit, not a stop")
            if where == ABOVE and ot is OrderType.LIMIT:
                raise CompileError("a buy limit above market fills immediately at market, not at the level")
        else:
            if where == ABOVE and ot in (OrderType.STOP, OrderType.STOP_LIMIT):
                raise CompileError("a sell stop above market triggers instantly; a level above market is a limit for a sell")
            if where == BELOW and ot is OrderType.LIMIT:
                raise CompileError("a sell limit below market fills immediately at market, not at the level")


def derived_capabilities(spec: StrategySpec) -> frozenset[Capability]:
    caps = {Capability.NATIVE_STOP}  # the protective stop is measured as a native stop
    if spec.order_type is not OrderType.MARKET:
        caps.add(Capability.RESTING_ORDERS)  # any non-market entry rests at the venue until it triggers
    if any(x.kind is ExitKind.TARGET_R for x in spec.exits):
        caps.add(Capability.RESTING_ORDERS)
    return frozenset(caps)


def validate(spec: StrategySpec) -> None:
    if spec.stop.value <= 0:
        raise CompileError("stop must be positive — a spec without a stop fails to compile (D5)")
    if spec.stop.kind is StopKind.ATR and spec.stop.lookback < 1:
        raise CompileError("an ATR stop needs a lookback of at least one bar")
    if not spec.entries:
        raise CompileError("a Strategy has at least one entry rule")
    if not spec.exits:
        raise CompileError("a Strategy has at least one exit rule beside its stop")
    for x in spec.exits:
        if x.kind is ExitKind.TIME and dict(x.params).get("bars", 0) < 1:
            raise CompileError("a time exit needs bars >= 1")
        if x.kind is ExitKind.TARGET_R and dict(x.params).get("multiple", 0) <= 0:
            raise CompileError("a target needs a positive multiple of R")
    _geometry_check(spec)
    for e in spec.entries:   # presence is _geometry_check's; these are the values a kind cannot take (ADR-0037)
        if e.kind is EntryKind.PULLBACK_IN_TREND and e.param("short") >= e.param("long"):
            raise CompileError("pullback_in_trend needs short < long: a dip is measured against a shorter average than the trend (ADR-0037)")
        if e.kind is EntryKind.DOWN_RUN and e.param("runs") < 1:
            raise CompileError("down_run needs runs >= 1")
        if e.kind is EntryKind.RETURN_BELOW and (e.param("lookback") < 1 or e.param("percent") <= 0):
            raise CompileError("return_below needs lookback >= 1 and percent > 0")
    if spec.regime is not None and spec.axis is not InformationAxis.REGIME:
        raise CompileError("a regime-gated Strategy belongs to the regime axis (F11); it spends from that budget")
    missing = derived_capabilities(spec) - spec.required_capabilities
    if missing:
        raise CompileError("spec needs capabilities it does not declare: "
                           + ", ".join(sorted(c.value for c in missing))
                           + " — capabilities are identity (ADR-0018), so declare them")


# M14.3: the sha a run stamps on everything it compiles — the tree as the run found it,
# read once. M16.10 (ADR-0055): it is read by ``occams.identity``, on the code paths only,
# so a Register the run appends to no longer marks the engine dirty; the vendored
# ``core/archive.engine_sha`` is no longer asked. The content hash beside it on every
# measured, resolved and surveyed record is ``identity.code_closure_sha()``.
_STAMPED_ENGINE_SHA: str | None = None


def stamp_engine_sha() -> str:
    """Take the commit (and dirtiness) of the tree *now* and stamp it on every
    ``to_engine`` until ``clear_engine_sha``; returns the stamp."""
    global _STAMPED_ENGINE_SHA
    from occams import identity

    _STAMPED_ENGINE_SHA = identity.engine_sha()
    return _STAMPED_ENGINE_SHA


def clear_engine_sha() -> None:
    global _STAMPED_ENGINE_SHA
    _STAMPED_ENGINE_SHA = None


def current_engine_sha() -> str:
    from occams import identity

    return _STAMPED_ENGINE_SHA if _STAMPED_ENGINE_SHA is not None else identity.engine_sha()


def to_engine(spec: StrategySpec) -> CompiledStrategy:
    """Deterministic; stamps ``engine_sha`` and the engine the horizon selects
    (D6, M9.3): INTRADAY -> day_boxed, MULTI_DAY -> position_boxed. The sha is
    the run's stamp when one was taken (M14.3), else the tree's now."""
    validate(spec)
    engine = "position_boxed" if spec.horizon is Horizon.MULTI_DAY else "day_boxed"  # D6: by type
    return CompiledStrategy(spec=spec, spec_hash=spec.hash, engine=engine, engine_sha=current_engine_sha())
