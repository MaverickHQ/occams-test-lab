"""M3.9 — the three entry kinds ADR-0037 added: each fires only from bars
before the box, carries its own params, sits in the compiler's tables, and
hashes as its own family."""

from __future__ import annotations

import pytest

from occams.config import InformationAxis
from occams.engine import day_boxed, position_boxed
from occams.engine.day_boxed import signal
from occams.proposers.price import PRICE_ENTRIES, entry_params, price_template
from occams.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing, Stop,
                         StopKind, StrategySpec, UniverseRule)
from occams.spec.compile import GEOMETRY, REQUIRED_PARAMS, CompileError, to_engine
from tests.test_day_boxed import bars

NEW = (EntryKind.DOWN_RUN, EntryKind.RETURN_BELOW, EntryKind.PULLBACK_IN_TREND)


def spec(entry: Entry, **kw) -> StrategySpec:
    base = dict(entries=(entry,), exits=(Exit(ExitKind.TIME, (("bars", 1),)),), stop=Stop(StopKind.PERCENT, 2.0),
                sizing=Sizing(), order_type=OrderType.MARKET, horizon=Horizon.INTRADAY,
                universe=UniverseRule((("venue", "US"),)), required_capabilities=frozenset({Capability.NATIVE_STOP}),
                axis=InformationAxis.PRICE_DAILY)
    base.update(kw)
    return StrategySpec(**base)


# ---- the tables ----------------------------------------------------------------------

def test_every_new_kind_has_a_geometry_row_a_params_row_and_a_market_only_geometry():
    for k in NEW:
        assert GEOMETRY[k] == {Side.LONG: "none", Side.SHORT: "none"} and REQUIRED_PARAMS[k]
    assert REQUIRED_PARAMS[EntryKind.DOWN_RUN] == ("runs",)
    assert REQUIRED_PARAMS[EntryKind.RETURN_BELOW] == ("lookback", "percent")
    assert REQUIRED_PARAMS[EntryKind.PULLBACK_IN_TREND] == ("short", "long")


def test_missing_params_and_impossible_params_are_refused_at_compile_by_name():
    with pytest.raises(CompileError, match="down_run entry needs parameter 'runs'"):
        to_engine(spec(Entry(EntryKind.DOWN_RUN, Side.LONG)))
    with pytest.raises(CompileError, match="short < long"):
        to_engine(spec(Entry(EntryKind.PULLBACK_IN_TREND, Side.LONG, (("short", 20), ("long", 10)))))
    with pytest.raises(CompileError, match="runs >= 1"):
        to_engine(spec(Entry(EntryKind.DOWN_RUN, Side.LONG, (("runs", 0),))))
    with pytest.raises(CompileError, match="percent > 0"):
        to_engine(spec(Entry(EntryKind.RETURN_BELOW, Side.LONG, (("lookback", 5), ("percent", 0)))))
    assert to_engine(spec(Entry(EntryKind.PULLBACK_IN_TREND, Side.LONG, (("short", 5), ("long", 50))))).engine == "day_boxed"


def test_a_new_kind_is_its_own_family_under_the_hash():
    a = spec(Entry(EntryKind.DOWN_RUN, Side.LONG, (("runs", 3),)))
    b = spec(Entry(EntryKind.RETURN_BELOW, Side.LONG, (("lookback", 3), ("percent", 3))))
    c = spec(Entry(EntryKind.PULLBACK_IN_TREND, Side.LONG, (("short", 3), ("long", 10))))
    d = spec(Entry(EntryKind.CLOSE_BELOW_MA, Side.LONG, (("lookback", 3),)))
    assert len({a.hash, b.hash, c.hash, d.hash}) == 4
    assert spec(Entry(EntryKind.DOWN_RUN, Side.LONG, (("runs", 4),))).hash != a.hash


# ---- the signals, from bars before the box only -------------------------------------------

def test_down_run_fires_after_the_streak_and_never_on_the_bar_that_completes_it():
    # closes: 100, 99, 98, 97 (three lower closes end at index 3), then 96
    b = bars([(100, 101, 99, 100), (99, 100, 98, 99), (98, 99, 97, 98), (97, 98, 96, 97), (96, 97, 95, 96)])
    e = Entry(EntryKind.DOWN_RUN, Side.LONG, (("runs", 3),))
    assert signal(e, b, 4)[0] is True        # bars 0..3 hold the streak; box 4 is entered
    assert signal(e, b, 3)[0] is False       # bar 3 completes the streak, and bar 3 is the box: not consulted
    assert signal(e, b, 2)[0] is False       # too few bars


def test_return_below_measures_the_decline_over_the_window_before_the_box():
    # close falls 100 -> 96 over bars 0..2 (4 %); bar 3 falls to 90 but is the box
    b = bars([(100, 101, 99, 100), (98, 99, 97, 98), (96, 97, 95, 96), (95, 96, 89, 90)])
    e = Entry(EntryKind.RETURN_BELOW, Side.LONG, (("lookback", 2), ("percent", 3.0)))
    assert signal(e, b, 3)[0] is True        # 96/100 - 1 = -4 % <= -3 %
    tight = Entry(EntryKind.RETURN_BELOW, Side.LONG, (("lookback", 2), ("percent", 5.0)))
    assert signal(tight, b, 3)[0] is False   # -4 % is not -5 %; bar 3's fall to 90 is never read


def test_pullback_fires_below_the_short_average_and_above_the_long_one():
    closes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 106]   # a dip on the last prior bar
    b = bars([(c, c + 1, c - 1, c) for c in closes] + [(106, 107, 105, 106)])
    e = Entry(EntryKind.PULLBACK_IN_TREND, Side.LONG, (("short", 3), ("long", 10)))
    first = len(closes)                       # the box is the bar after the dip
    fires, side, level = signal(e, b, first)
    assert fires is True and side is Side.LONG and level is None
    # the same bars without the dip: above both averages, no pullback
    flat = bars([(c, c + 1, c - 1, c) for c in closes[:-1] + [110]] + [(110, 111, 109, 110)])
    assert signal(e, flat, first)[0] is False


def test_the_new_kinds_run_through_both_engines_and_the_null_probe():
    b = bars([(100 - i * 0.5, 101 - i * 0.5, 99 - i * 0.5, 100 - i * 0.5) for i in range(12)]
             + [(94, 96, 93, 95), (95, 96, 94, 95.5), (95.5, 97, 95, 96)])
    for k, params in ((EntryKind.DOWN_RUN, (("runs", 3),)), (EntryKind.RETURN_BELOW, (("lookback", 5), ("percent", 1.0))),
                      (EntryKind.PULLBACK_IN_TREND, (("short", 2), ("long", 5)))):
        s = spec(Entry(k, Side.LONG, params))
        day_boxed.run(to_engine(s), {"F": b}, seed=0)
        position_boxed.run(to_engine(s.replace(horizon=Horizon.MULTI_DAY, exits=(Exit(ExitKind.TIME, (("bars", 2),)),))),
                           {"F": b}, seed=0)


# ---- the proposer knows them -----------------------------------------------------------

def test_the_price_proposer_declares_each_kinds_params_by_name():
    assert set(NEW) <= set(PRICE_ENTRIES)
    assert entry_params(EntryKind.DOWN_RUN, runs=3) == (("runs", 3.0),)
    assert entry_params(EntryKind.RETURN_BELOW, lookback=5, percent=3) == (("lookback", 5.0), ("percent", 3.0))
    with pytest.raises(ValueError, match="missing \\['percent'\\]"):
        entry_params(EntryKind.RETURN_BELOW, lookback=5)
    with pytest.raises(ValueError, match="not its own \\['runs'\\]"):
        entry_params(EntryKind.CLOSE_BELOW_MA, lookback=5, runs=3)
    t = price_template(EntryKind.PULLBACK_IN_TREND, hold_bars=5, short=5, long=50)
    assert to_engine(t).engine == "position_boxed" and t.order_type is OrderType.MARKET
    assert t.required_capabilities == frozenset({Capability.NATIVE_STOP})


def test_each_new_kind_belongs_to_an_auditor_family_so_its_fills_are_audited():
    from occams.costs.auditors import FAMILY_AUDITORS, FAMILY_OF, family_of
    for k in NEW:
        assert FAMILY_OF[k] == "reversal" and FAMILY_AUDITORS["reversal"]
        assert family_of(spec(Entry(k, Side.LONG, (("runs", 3),) if k is EntryKind.DOWN_RUN else
                                     (("lookback", 5), ("percent", 3)) if k is EntryKind.RETURN_BELOW else
                                     (("short", 5), ("long", 50))))) == "reversal"
    assert all(k in FAMILY_OF for k in EntryKind)   # no kind without a family: unaudited means refused
