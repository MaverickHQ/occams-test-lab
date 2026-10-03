"""The frozen, declarative definition of a Strategy — the single source of
truth from which every other representation is generated (CONTEXT:
StrategySpec). Every enum here is closed (M3.2, A6): a free-text value
raises at construction, not at the first use that happens to notice.

Identity is the D4 set — entries, exits, stop, sizing, order type, horizon,
universe rule, required capabilities, axis. Window, seed, ``engine_sha``
and cost-model version are context and live in the Verdict, never here.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass, fields
from typing import Any

from occams.config import InformationAxis
from occams.strategy import spec_hash as _hash_mapping


class OrderType(enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class Horizon(enum.Enum):
    INTRADAY = "intraday"      # day-boxed simulator (M3.7)
    MULTI_DAY = "multi_day"    # position-boxed simulator (M9.1)


class Side(enum.Enum):
    LONG = "long"
    SHORT = "short"


class Capability(enum.Enum):
    """What a Strategy needs from any venue to behave as measured (ADR-0018)."""

    NATIVE_STOP = "native_stop"
    RESTING_ORDERS = "resting_orders"
    FRACTIONAL_SHARES = "fractional_shares"
    WHOLE_SHARES = "whole_shares"


class EntryKind(enum.Enum):
    ALWAYS = "always"                  # apparatus: every box, declared side
    COIN_FLIP = "coin_flip"            # apparatus: every box, side by a seeded coin (the null)
    BREAKOUT_HIGH = "breakout_high"    # level = highest high of the prior `lookback` bars
    BREAKOUT_LOW = "breakout_low"      # level = lowest low of the prior `lookback` bars
    CLOSE_ABOVE_MA = "close_above_ma"  # prior close above its `lookback` moving average
    CLOSE_BELOW_MA = "close_below_ma"  # prior close below its `lookback` moving average
    # ADR-0037 (adopted 2026-09-12): three kinds added by decision, each a conjunction the six above cannot state
    DOWN_RUN = "down_run"                    # each of the last `runs` closes lower than the one before
    RETURN_BELOW = "return_below"            # close[-1] / close[-1-`lookback`] - 1 <= -`percent`/100
    PULLBACK_IN_TREND = "pullback_in_trend"  # prior close below its `short` average and above its `long` average


class ExitKind(enum.Enum):
    TIME = "time"          # after `bars` bars, at that bar's close
    TARGET_R = "target_r"  # a limit at `multiple` x stop distance


class StopKind(enum.Enum):
    PERCENT = "percent"    # `value` percent of the entry price
    ATR = "atr"            # `value` x ATR over `lookback` prior bars


class SizingKind(enum.Enum):
    FIXED_R = "fixed_r"    # size = R / stop_distance (D5, ADR-0003)


class Regime(enum.Enum):
    """The classifier's closed label set (F11, ADR-0005)."""

    UP = "up"
    DOWN = "down"
    RANGING = "ranging"


def _params(p) -> tuple[tuple[str, float], ...]:
    return tuple(sorted((str(k), float(v)) for k, v in dict(p).items()))


@dataclass(frozen=True)
class Entry:
    kind: EntryKind
    side: Side
    params: tuple[tuple[str, float], ...] = ()

    def __post_init__(self):
        _closed(self, "kind", EntryKind)
        _closed(self, "side", Side)
        object.__setattr__(self, "params", _params(self.params))

    def param(self, name: str) -> float:
        return dict(self.params)[name]


@dataclass(frozen=True)
class Exit:
    kind: ExitKind
    params: tuple[tuple[str, float], ...] = ()

    def __post_init__(self):
        _closed(self, "kind", ExitKind)
        object.__setattr__(self, "params", _params(self.params))

    def param(self, name: str) -> float:
        return dict(self.params)[name]


@dataclass(frozen=True)
class Stop:
    kind: StopKind
    value: float
    lookback: int = 0

    def __post_init__(self):
        _closed(self, "kind", StopKind)


@dataclass(frozen=True)
class Sizing:
    kind: SizingKind = SizingKind.FIXED_R

    def __post_init__(self):
        _closed(self, "kind", SizingKind)


@dataclass(frozen=True)
class UniverseRule:
    """A rule, not a list (D8, ADR-0025): terms evaluated point-in-time by
    M4.10. One changed term is a different Strategy."""

    terms: tuple[tuple[str, Any], ...]

    def __post_init__(self):
        object.__setattr__(self, "terms", tuple(sorted((str(k), v) for k, v in dict(self.terms).items())))

    def term(self, name: str) -> Any:
        return dict(self.terms)[name]


@dataclass(frozen=True)
class RegimeGate:
    """Trade only in one regime of one frozen classifier (F11). The frozen
    hash is identity (ADR-0007): a different classifier is a different
    Strategy. ``index_name`` says which series is labelled at index level."""

    classifier_hash: str
    label: Regime
    index_name: str

    def __post_init__(self):
        _closed(self, "label", Regime)
        if not str(self.classifier_hash).strip():
            raise ValueError("a regime gate names the frozen classifier it reads")


def _closed(obj, field_name: str, enum_type) -> None:
    v = getattr(obj, field_name)
    if not isinstance(v, enum_type):
        raise TypeError(f"{type(obj).__name__}.{field_name} must be {enum_type.__name__}, "
                        f"got {v!r} — the enum is closed (M3.2)")


@dataclass(frozen=True)
class StrategySpec:
    entries: tuple[Entry, ...]
    exits: tuple[Exit, ...]
    stop: Stop                                   # mandatory (D5)
    sizing: Sizing
    order_type: OrderType                        # validated against entry geometry at compile
    horizon: Horizon                             # selects the simulator, by type (D6)
    universe: UniverseRule                       # a rule, not a list (D8)
    required_capabilities: frozenset[Capability] # identity; the venue is context (ADR-0018)
    axis: InformationAxis                        # closed enum
    regime: RegimeGate | None = None             # the frozen classifier it references, if any (ADR-0007)

    def __post_init__(self):
        _closed(self, "order_type", OrderType)
        if self.regime is not None and not isinstance(self.regime, RegimeGate):
            raise TypeError("StrategySpec.regime must be a RegimeGate or None")
        _closed(self, "horizon", Horizon)
        _closed(self, "axis", InformationAxis)
        if not isinstance(self.stop, Stop):
            raise TypeError("StrategySpec.stop must be a Stop — every Strategy declares one (D5)")
        if not isinstance(self.sizing, Sizing):
            raise TypeError("StrategySpec.sizing must be a Sizing")
        if not isinstance(self.universe, UniverseRule):
            raise TypeError("StrategySpec.universe must be a UniverseRule")
        object.__setattr__(self, "entries", tuple(self.entries))
        object.__setattr__(self, "exits", tuple(self.exits))
        for e in self.entries:
            if not isinstance(e, Entry):
                raise TypeError("entries must be Entry")
        for x in self.exits:
            if not isinstance(x, Exit):
                raise TypeError("exits must be Exit")
        caps = frozenset(self.required_capabilities)
        for c in caps:
            if not isinstance(c, Capability):
                raise TypeError(f"required_capabilities must be Capability, got {c!r}")
        object.__setattr__(self, "required_capabilities", caps)

    # ---- identity ---------------------------------------------------------

    def identity(self) -> dict:
        """The D4 mapping, and nothing else."""
        return {
            "entries": [{"kind": e.kind.value, "side": e.side.value, "params": list(map(list, e.params))} for e in self.entries],
            "exits": [{"kind": x.kind.value, "params": list(map(list, x.params))} for x in self.exits],
            "stop": {"kind": self.stop.kind.value, "value": self.stop.value, "lookback": self.stop.lookback},
            "sizing": {"kind": self.sizing.kind.value},
            "order_type": self.order_type.value,
            "horizon": self.horizon.value,
            "universe": [[k, v] for k, v in self.universe.terms],
            "required_capabilities": sorted(c.value for c in self.required_capabilities),
            "axis": self.axis.value,
            "regime": None if self.regime is None else {"classifier": self.regime.classifier_hash,
                                                        "label": self.regime.label.value,
                                                        "index": self.regime.index_name},
        }

    @property
    def hash(self) -> str:
        return _hash_mapping(self.identity())

    # ---- JSON round trip --------------------------------------------------

    def to_json(self) -> str:
        return json.dumps(self.identity(), sort_keys=True, indent=1)

    @classmethod
    def from_json(cls, text: str) -> "StrategySpec":
        d = json.loads(text)
        return cls(
            entries=tuple(Entry(EntryKind(e["kind"]), Side(e["side"]), tuple((k, v) for k, v in e["params"])) for e in d["entries"]),
            exits=tuple(Exit(ExitKind(x["kind"]), tuple((k, v) for k, v in x["params"])) for x in d["exits"]),
            stop=Stop(StopKind(d["stop"]["kind"]), float(d["stop"]["value"]), int(d["stop"]["lookback"])),
            sizing=Sizing(SizingKind(d["sizing"]["kind"])),
            order_type=OrderType(d["order_type"]),
            horizon=Horizon(d["horizon"]),
            universe=UniverseRule(tuple((k, v) for k, v in d["universe"])),
            required_capabilities=frozenset(Capability(c) for c in d["required_capabilities"]),
            axis=InformationAxis(d["axis"]),
            regime=None if not d.get("regime") else RegimeGate(d["regime"]["classifier"], Regime(d["regime"]["label"]),
                                                               d["regime"]["index"]),
        )

    def replace(self, **changes) -> "StrategySpec":
        current = {f.name: getattr(self, f.name) for f in fields(self)}
        current.update(changes)
        return StrategySpec(**current)
