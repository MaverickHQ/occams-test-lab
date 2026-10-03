"""M3.3 stop mandatory and sizing across currencies · M3.4 order type
validated against entry geometry — the A4 regression."""

from __future__ import annotations

import pytest

from occams.config import InformationAxis
from occams.core import execution as ex
from occams.guards import Refused
from occams.register import Register
from occams.sizing import position_size, r_multiple
from occams.spec import (Capability, CompileError, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType,
                         Side, Sizing, Stop, StopKind, StrategySpec, UniverseRule, to_engine)
from occams.spec.compile import derived_capabilities
from occams.strategy import Strategy, StrategyState, transition


def spec(entry_kind=EntryKind.BREAKOUT_HIGH, side=Side.LONG, order_type=OrderType.STOP, **kw):
    params = (("lookback", 20),) if entry_kind not in (EntryKind.ALWAYS, EntryKind.COIN_FLIP) else \
             ((("seed", 1),) if entry_kind is EntryKind.COIN_FLIP else ())
    base = dict(entries=(Entry(entry_kind, side, params),), exits=(Exit(ExitKind.TIME, (("bars", 1),)),),
                stop=Stop(StopKind.PERCENT, 2.0), sizing=Sizing(), order_type=order_type,
                horizon=Horizon.INTRADAY, universe=UniverseRule((("venue", "US"),)),
                required_capabilities=frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS}),
                axis=InformationAxis.PRICE_DAILY)
    base.update(kw)
    return StrategySpec(**base)


# ---- M3.4: the v1.8 defect ---------------------------------------------

def test_a_buy_stop_below_market_fails_to_compile():
    """A4: a hand-written engine and a hand-written renderer agreed on this
    for nine versions. Here it is one line and it is refused at compile."""
    with pytest.raises(CompileError, match="buy stop below market"):
        to_engine(spec(EntryKind.BREAKOUT_LOW, Side.LONG, OrderType.STOP))


def test_the_same_defect_is_refused_per_bar_by_the_vendored_execution_module():
    with pytest.raises(ex.Unplaceable, match="BELOW market"):
        ex.validate(ex.Order(ex.STOP, ex.BUY, 99.0), market=100.0)


def test_a_buy_limit_above_market_fails_to_compile():
    with pytest.raises(CompileError, match="buy limit above market"):
        to_engine(spec(EntryKind.BREAKOUT_HIGH, Side.LONG, OrderType.LIMIT))


def test_sell_side_geometry_is_mirrored():
    with pytest.raises(CompileError, match="sell stop above market"):
        to_engine(spec(EntryKind.BREAKOUT_HIGH, Side.SHORT, OrderType.STOP))
    to_engine(spec(EntryKind.BREAKOUT_LOW, Side.SHORT, OrderType.STOP))  # sell stop below: fine


def test_a_levelless_entry_must_be_a_market_order():
    with pytest.raises(CompileError, match="must be market"):
        to_engine(spec(EntryKind.ALWAYS, Side.LONG, OrderType.STOP))
    to_engine(spec(EntryKind.ALWAYS, Side.LONG, OrderType.MARKET))


def test_market_orders_carry_no_geometry_to_contradict():
    to_engine(spec(EntryKind.BREAKOUT_LOW, Side.LONG, OrderType.MARKET))


# ---- M3.3: the stop, and sizing ----------------------------------------

def test_a_non_positive_stop_fails_to_compile():
    with pytest.raises(CompileError, match="stop must be positive"):
        to_engine(spec(stop=Stop(StopKind.PERCENT, 0.0)))
    with pytest.raises(CompileError, match="lookback"):
        to_engine(spec(stop=Stop(StopKind.ATR, 2.0, lookback=0)))


def test_sizing_crosses_currencies_correctly():
    # planned risk in the account currency, converted at entry into the
    # instrument currency, divided by the stop distance in that currency.
    # Fixture numbers: 1 unit of account currency buys 1.25 instrument units.
    assert position_size(risk_account=1.0, fx_instrument_per_account=1.25, stop_distance_instrument=0.5) == pytest.approx(2.5)
    assert position_size(risk_account=1.0, fx_instrument_per_account=0.8, stop_distance_instrument=0.5) == pytest.approx(1.6)
    with pytest.raises(ValueError):
        position_size(risk_account=1.0, fx_instrument_per_account=1.0, stop_distance_instrument=0.0)


def test_results_are_multiples_of_planned_r_and_not_clipped():
    assert r_multiple(entry=100, exit=102, stop_distance=2, side=Side.LONG) == pytest.approx(1.0)
    assert r_multiple(entry=100, exit=94.6, stop_distance=2, side=Side.LONG) == pytest.approx(-2.7)
    assert r_multiple(entry=100, exit=105.4, stop_distance=2, side=Side.SHORT) == pytest.approx(-2.7)


# ---- capabilities and horizon ------------------------------------------

def test_undeclared_required_capabilities_fail_to_compile():
    with pytest.raises(CompileError, match="does not declare"):
        to_engine(spec(required_capabilities=frozenset({Capability.NATIVE_STOP})))  # a stop entry rests


def test_capabilities_are_derived_from_the_spec():
    assert derived_capabilities(spec(EntryKind.ALWAYS, order_type=OrderType.MARKET)) == {Capability.NATIVE_STOP}
    assert Capability.RESTING_ORDERS in derived_capabilities(spec(order_type=OrderType.LIMIT, entry_kind=EntryKind.BREAKOUT_LOW))


def test_horizon_selects_the_engine_by_type():
    assert to_engine(spec(horizon=Horizon.MULTI_DAY)).engine == "position_boxed"
    assert to_engine(spec(horizon=Horizon.INTRADAY)).engine == "day_boxed"


def test_compiled_strategy_is_deterministic_and_stamped():
    a, b = to_engine(spec()), to_engine(spec())
    assert a == b and a.spec_hash == spec().hash and len(a.engine_sha) >= 7


# ---- the SPECIFIED -> COMPILED guard now reads the spec -----------------

def test_the_compile_guard_refuses_a_spec_that_does_not_compile(tmp_path):
    reg = Register(tmp_path / "r.jsonl")
    s = Strategy.from_spec(spec(EntryKind.BREAKOUT_LOW, Side.LONG, OrderType.STOP))
    with pytest.raises(Refused, match="does not compile"):
        transition(s, StrategyState.COMPILED, register=reg)
    ok = Strategy.from_spec(spec())
    assert transition(ok, StrategyState.COMPILED, register=reg).state is StrategyState.COMPILED
    assert ok.spec_hash == spec().hash
