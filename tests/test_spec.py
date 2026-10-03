"""M3.1 constructible, frozen, JSON round-trips · M3.2 closed enums · M3.5
hash is identity, not context."""

from __future__ import annotations

import dataclasses

import pytest

from occams.config import InformationAxis
from occams.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing,
                         Stop, StopKind, StrategySpec, UniverseRule)


def spec(**kw) -> StrategySpec:
    base = dict(entries=(Entry(EntryKind.BREAKOUT_HIGH, Side.LONG, (("lookback", 20),)),),
                exits=(Exit(ExitKind.TIME, (("bars", 1),)), Exit(ExitKind.TARGET_R, (("multiple", 2),))),
                stop=Stop(StopKind.PERCENT, 2.0), sizing=Sizing(), order_type=OrderType.STOP,
                horizon=Horizon.INTRADAY, universe=UniverseRule((("venue", "US"), ("min_adv_shares", 1e6))),
                required_capabilities=frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS}),
                axis=InformationAxis.PRICE_DAILY)
    base.update(kw)
    return StrategySpec(**base)


def test_constructible_and_frozen():
    s = spec()
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.order_type = OrderType.MARKET  # type: ignore[misc]


def test_json_round_trips_to_an_equal_spec_with_the_same_hash():
    s = spec()
    back = StrategySpec.from_json(s.to_json())
    assert back == s and back.hash == s.hash


def test_a_free_text_axis_raises_at_construction():
    with pytest.raises(TypeError, match="closed"):
        spec(axis="technical")  # type: ignore[arg-type]


@pytest.mark.parametrize("field,value", [("order_type", "stop"), ("horizon", "intraday"),
                                         ("required_capabilities", frozenset({"native_stop"}))])
def test_every_enum_field_is_closed(field, value):
    with pytest.raises(TypeError):
        spec(**{field: value})


def test_entry_and_exit_kinds_are_closed():
    with pytest.raises(TypeError):
        Entry("breakout_high", Side.LONG)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Exit("time")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        EntryKind("magic")


def test_a_spec_without_a_stop_cannot_be_constructed():
    kw = dict(entries=(Entry(EntryKind.ALWAYS, Side.LONG),), exits=(Exit(ExitKind.TIME, (("bars", 1),)),),
              sizing=Sizing(), order_type=OrderType.MARKET, horizon=Horizon.INTRADAY,
              universe=UniverseRule(()), required_capabilities=frozenset({Capability.NATIVE_STOP}),
              axis=InformationAxis.PRICE_DAILY)
    with pytest.raises(TypeError):
        StrategySpec(**kw)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        StrategySpec(stop=None, **kw)  # type: ignore[arg-type]


def test_hash_is_identity_not_context():
    """Window, seed, engine_sha and cost version are not fields of the spec
    at all, so they cannot move the hash; the test shows the only levers are
    the D4 identity fields."""
    a = spec()
    assert a.hash == spec().hash
    assert set(a.identity()) == {"entries", "exits", "stop", "sizing", "order_type", "horizon",
                                 "universe", "required_capabilities", "axis", "regime"}  # ADR-0007: the classifier referenced
    for k in ("window", "seed", "engine_sha", "cost_version", "venue"):
        assert k not in a.identity()


def test_changing_one_universe_term_changes_the_hash():
    a = spec()
    b = spec(universe=UniverseRule((("venue", "US"), ("min_adv_shares", 2e6))))
    assert a.hash != b.hash
    assert a.universe.term("venue") == b.universe.term("venue")


def test_changing_a_capability_changes_the_hash():
    a = spec()
    b = spec(required_capabilities=frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS,
                                              Capability.FRACTIONAL_SHARES}))
    assert a.hash != b.hash


def test_param_order_is_not_identity():
    a = Entry(EntryKind.BREAKOUT_HIGH, Side.LONG, (("lookback", 20), ("x", 1)))
    b = Entry(EntryKind.BREAKOUT_HIGH, Side.LONG, (("x", 1), ("lookback", 20)))
    assert a == b
