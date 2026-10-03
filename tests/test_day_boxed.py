"""M3.6 deterministic, seeded, stamped · M3.7 a known fixture to a
hand-checked P&L · M3.8 a gap through the stop records worse than -1R."""

from __future__ import annotations

import json

import pytest

from occams.config import InformationAxis
from occams.data.bars import Bars, random_walk
from occams.engine import day_boxed
from occams.register import _plain
from occams.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing,
                         Stop, StopKind, StrategySpec, UniverseRule, to_engine)

CAPS = frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS})


def spec(**kw):
    base = dict(entries=(Entry(EntryKind.BREAKOUT_HIGH, Side.LONG, (("lookback", 2),)),),
                exits=(Exit(ExitKind.TIME, (("bars", 1),)), Exit(ExitKind.TARGET_R, (("multiple", 2),))),
                stop=Stop(StopKind.PERCENT, 2.0), sizing=Sizing(), order_type=OrderType.STOP,
                horizon=Horizon.INTRADAY, universe=UniverseRule((("venue", "US"),)),
                required_capabilities=CAPS, axis=InformationAxis.PRICE_DAILY)
    base.update(kw)
    return StrategySpec(**base)


def bars(rows, name="F"):
    o, h, lo, c = zip(*rows)
    return Bars(name, tuple(map(float, o)), tuple(map(float, h)), tuple(map(float, lo)), tuple(map(float, c)),
                tuple(1.0 for _ in rows), tuple(range(len(rows))))


# ---- M3.7: hand-checked fixture ----------------------------------------

FIXTURE = bars([
    (100.0, 102.0, 99.0, 101.0),   # day 0  history
    (101.0, 103.0, 100.0, 102.0),  # day 1  history           -> level for day 2 = 103
    (102.5, 105.0, 102.0, 104.0),  # day 2  fills at 103, exits at close 104
    (106.0, 107.0, 105.5, 106.5),  # day 3  level 105; opens 106 through it -> fills at the open
    (106.0, 106.8, 104.0, 104.5),  # day 4  level 107 never reached -> no trade
    (107.5, 108.0, 105.0, 105.2),  # day 5  level 107; fills at the open 107.5, stopped at 105.35
])


def test_hand_checked_pnl_in_r():
    trades = day_boxed.run(to_engine(spec()), {"F": FIXTURE}, seed=0)
    assert [t.day for t in trades] == [2, 3, 5]
    d2, d3, d5 = trades
    assert (d2.entry, d2.exit, d2.reason) == (103.0, 104.0, "time")
    assert d2.gross_r == pytest.approx((104 - 103) / (103 * 0.02))          # 0.485437
    assert (d3.entry, d3.reason) == (106.0, "time")                          # gapped entry fills at the open
    assert d3.gross_r == pytest.approx((106.5 - 106) / (106 * 0.02))         # 0.235849
    assert (d5.entry, d5.reason) == (107.5, "stopped")
    assert d5.gross_r == pytest.approx(-1.0)                                 # planned risk, exactly


def test_signals_use_only_bars_before_the_box():
    """The level on day 2 is the max high of days 0-1; day 2's own high is
    never consulted (a look-ahead would fill every breakout)."""
    trades = day_boxed.run(to_engine(spec()), {"F": FIXTURE}, seed=0)
    assert trades[0].entry == 103.0 and trades[0].entry != FIXTURE.high[2]


def test_stop_taken_over_target_inside_one_bar():
    """Both levels inside the range of one bar: the worse case is booked."""
    b = bars([(100, 101, 99, 100.5), (100.5, 110.0, 90.0, 100.0)])
    s = spec(entries=(Entry(EntryKind.ALWAYS, Side.LONG),), order_type=OrderType.MARKET,
             required_capabilities=CAPS)
    t = day_boxed.run(to_engine(s), {"F": b}, seed=0)[0]
    assert t.reason == "stopped" and t.gross_r == pytest.approx(-1.0)


# ---- M3.8: the gap ------------------------------------------------------

def test_a_gap_through_the_stop_records_minus_2_7_r():
    """An intraday box of two bars: entry at 100 with a 2 % stop (98); the
    second bar opens at 94.6, through the stop. The fill is the open, not
    the stop, and the record is -2.7R — not -1R."""
    g = Bars("G", open=(99.0, 100.0, 94.6), high=(99.5, 101.0, 95.0), low=(98.5, 99.0, 94.0),
             close=(99.2, 100.5, 94.8), volume=(1, 1, 1), day=(0, 1, 1))
    s = spec(entries=(Entry(EntryKind.ALWAYS, Side.LONG),), order_type=OrderType.MARKET,
             exits=(Exit(ExitKind.TIME, (("bars", 5),)),))
    t = day_boxed.run(to_engine(s), {"G": g}, seed=0)[0]
    assert t.reason == "gapped" and t.exit == 94.6
    assert t.gross_r == pytest.approx(-2.7)


# ---- M3.6: deterministic, seeded, stamped -------------------------------

def measure(seed=11, names=("A", "B", "C"), days=120):
    template = spec(entries=(Entry(EntryKind.COIN_FLIP, Side.LONG, (("seed", 3),)),), order_type=OrderType.MARKET)
    axes = {"stop": [1.5, 2.0, 2.5], "target": [2.0, 3.0]}

    def cell(t, p):
        return t.replace(stop=Stop(StopKind.PERCENT, p["stop"]),
                         exits=(Exit(ExitKind.TIME, (("bars", 1),)), Exit(ExitKind.TARGET_R, (("multiple", p["target"]),))))

    world = {n: random_walk(n, days=days, seed=5, sigma_daily=0.02) for n in names}
    return day_boxed.measure(template, axes, cell, world, seed=seed, cost_in_r=0.02, null_draws=300)


def test_same_spec_seed_and_bars_give_byte_identical_results():
    a, b = measure(), measure()
    assert json.dumps(_plain(a), sort_keys=True) == json.dumps(_plain(b), sort_keys=True)
    assert a.engine == "day_boxed" and len(a.engine_sha) >= 7 and a.seed == 11


def test_the_measurement_meets_the_m2_contract():
    m = measure()
    assert m.search_space_size == 6 and all(c.spec_hash for c in m.cells)
    assert len(m.null_ev) == 300 and m.winner.groups == ("A", "B", "C")
    assert abs(m.years - 120 / 252) < 1e-9


def test_random_walk_bars_are_reproducible_across_processes():
    a = random_walk("Z", days=5, seed=1, sigma_daily=0.01)
    b = random_walk("Z", days=5, seed=1, sigma_daily=0.01)
    assert a == b


def test_the_null_is_random_entry_under_the_same_geometry():
    m = measure()
    import statistics
    assert statistics.fmean(m.null_ev) < 0.05  # driftless world, cost paid: near or below zero
ENGINE = day_boxed


# ---- ADR-0040: a resting limit the bar opens through fills at the open ---------------

LIMIT_ROWS = [
    (100.0, 102.0, 99.0, 101.0),   # 0 history
    (101.0, 103.0, 100.0, 102.0),  # 1 history                    -> level for day 2 = min low = 99
    (98.0, 99.5, 97.0, 99.0),      # 2 opens 98, through the 99 limit -> fills at the open, 98 (before: 99, inside the gap)
    (99.0, 100.0, 98.5, 99.5),     # 3 level 97 never reached     -> no trade
    (98.0, 99.0, 96.5, 98.5),      # 4 level 97; opens above it and trades down to it -> fills at the level, 97
    (98.6, 99.2, 98.0, 98.8),      # 5
]


def test_a_resting_limit_the_bar_opens_through_fills_at_the_open_and_passes_the_gap_auditor():
    from dataclasses import replace

    from occams.costs.auditors import check_fill

    s = spec(entries=(Entry(EntryKind.BREAKOUT_LOW, Side.LONG, (("lookback", 2),)),), order_type=OrderType.LIMIT,
             exits=(Exit(ExitKind.TIME, (("bars", 1),)),), stop=Stop(StopKind.PERCENT, 2.0))
    trades = ENGINE.run(to_engine(s), {"L": bars(LIMIT_ROWS, name="L")}, seed=0)
    assert [t.entry_index for t in trades] == [2, 4] and [t.entry for t in trades] == [98.0, 97.0]
    assert trades.missed == () and all(t.fill.order_kind == "limit" and t.fill.level in (99.0, 97.0) for t in trades)
    # the fill the old rule booked — the level, inside the gap 102 -> 98 — is exactly what the auditor refuses
    assert "inside the overnight gap" in check_fill("breakout", replace(trades[0].fill, price=99.0))
    assert check_fill("breakout", trades[0].fill) == "" and check_fill("breakout", trades[1].fill) == ""
