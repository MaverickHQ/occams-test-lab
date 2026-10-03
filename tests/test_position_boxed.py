"""M9.1 the position-boxed simulator on a hand-checked multi-day fixture ·
M9.2 block bootstrap coverage under known autocorrelation · M9.3 horizon
selects the simulator by type."""

from __future__ import annotations

import numpy as np
import pytest

from occams.config import InformationAxis
from occams.data.actions import Action, ActionKind, ActionSeries
from occams.data.bars import Bars, random_walk
from occams.engine import day_boxed, position_boxed
from occams.engine.position_boxed import block_bootstrap_means, block_length
from occams.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing, Stop,
                         StopKind, StrategySpec, UniverseRule, to_engine)

CAPS = frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS})


def spec(**kw):
    base = dict(entries=(Entry(EntryKind.BREAKOUT_HIGH, Side.LONG, (("lookback", 2),)),),
                exits=(Exit(ExitKind.TIME, (("bars", 3),)), Exit(ExitKind.TARGET_R, (("multiple", 3),))),
                stop=Stop(StopKind.PERCENT, 2.0), sizing=Sizing(), order_type=OrderType.STOP,
                horizon=Horizon.MULTI_DAY, universe=UniverseRule((("venue", "NYSE"),)),
                required_capabilities=CAPS, axis=InformationAxis.PRICE_DAILY)
    base.update(kw)
    return StrategySpec(**base)


def bars(rows, name="P"):
    o, h, lo, c = zip(*rows, strict=True)
    return Bars(name, tuple(map(float, o)), tuple(map(float, h)), tuple(map(float, lo)), tuple(map(float, c)),
                tuple(1.0 for _ in rows), tuple(range(len(rows))))


FIXTURE = bars([
    (100.0, 102.0, 99.0, 101.0),   # 0 history
    (101.0, 103.0, 100.0, 102.0),  # 1 history                -> level for day 2 = 103
    (102.5, 105.0, 102.0, 104.0),  # 2 fills at 103; stop 100.94, target 109.18; held
    (104.0, 106.0, 103.5, 105.0),  # 3 held (2nd bar)
    (105.0, 107.0, 104.5, 106.0),  # 4 time exit at close 106 (3rd bar)      -> +1.4563R
    (106.0, 108.0, 105.5, 107.0),  # 5 level = max(h3,h4)=107; open 106 < 107, high 108 -> fills 107; stop 104.86
    (100.0, 101.0, 99.0, 100.5),   # 6 opens at 100, through the stop -> gapped exit at 100 -> -3.2710R
    (100.5, 102.0, 100.0, 101.0),  # 7 level = max(h5,h6)=108 never reached
])


def test_hand_checked_multi_day_pnl():
    trades = position_boxed.run(to_engine(spec()), {"P": FIXTURE}, seed=0)
    assert [t.day for t in trades] == [2, 5]
    a, b = trades
    assert (a.entry, a.exit_index, a.reason) == (103.0, 4, "time")
    assert a.gross_r == pytest.approx((106.0 - 103.0) / (103.0 * 0.02))       # 1.456311
    assert (b.entry, b.exit, b.reason) == (107.0, 100.0, "gapped")
    assert b.gross_r == pytest.approx((100.0 - 107.0) / (107.0 * 0.02))       # -3.271028, worse than -1R


def test_one_position_at_a_time_per_name():
    """Day 3 is also a breakout day (level 105 < high 106) but a position is open: not taken."""
    trades = position_boxed.run(to_engine(spec()), {"P": FIXTURE}, seed=0)
    assert all(t.day != 3 for t in trades)


def test_a_split_inside_the_hold_does_not_fire_the_stop():
    split = ActionSeries((Action(ActionKind.SPLIT, "P", day=3, ratio=2.0),))
    rows = [(100.0, 102.0, 99.0, 101.0), (101.0, 103.0, 100.0, 102.0), (102.5, 105.0, 102.0, 104.0),
            (52.0, 53.0, 51.75, 52.5), (52.5, 53.5, 52.0, 53.0)]  # days 3-4 print on the new basis
    s = spec(exits=(Exit(ExitKind.TIME, (("bars", 3),)),))
    t = position_boxed.run(to_engine(s), {"P": bars(rows)}, seed=0, actions=split)[0]
    assert t.reason == "time" and t.exit_index == 4
    assert t.gross_r == pytest.approx((53.0 * 2 - 103.0) / (103.0 * 0.02))  # exit restated to the entry basis
    naive = position_boxed.run(to_engine(s), {"P": bars(rows)}, seed=0)[0]
    assert naive.reason == "gapped"  # without the action the split print looks like a gap through the stop


# ---- M9.3 -----------------------------------------------------------------------

def test_horizon_selects_the_simulator_and_each_refuses_the_other():
    multi = to_engine(spec())
    intra = to_engine(spec(horizon=Horizon.INTRADAY, exits=(Exit(ExitKind.TIME, (("bars", 1),)),)))
    assert multi.engine == "position_boxed" and intra.engine == "day_boxed"
    with pytest.raises(day_boxed.EngineRefusal, match="A5"):
        day_boxed.run(multi, {"P": FIXTURE}, seed=0)
    with pytest.raises(position_boxed.EngineRefusal, match="D6"):
        position_boxed.run(intra, {"P": FIXTURE}, seed=0)
    assert len(multi.run({"P": FIXTURE}, seed=0)) == 2  # dispatch by type


# ---- M9.2 -----------------------------------------------------------------------

def _ar1(n, phi, seed):
    rng = np.random.default_rng(seed)
    x = np.empty(n)
    x[0] = rng.standard_normal()
    for i in range(1, n):
        x[i] = phi * x[i - 1] + rng.standard_normal() * np.sqrt(1 - phi**2)
    return x


def test_block_bootstrap_has_near_nominal_coverage_where_the_iid_bootstrap_does_not():
    """AR(1) with phi = 0.6, true mean 0. Nominal 90 % intervals over 150
    replications: the block bootstrap should cover near 0.9; resampling
    single observations ignores the dependence and covers well below it."""
    n, phi, reps = 300, 0.6, 150
    block_cov = iid_cov = 0
    for r in range(reps):
        x = _ar1(n, phi, seed=1000 + r)
        b = block_bootstrap_means(x, block=block_length(x), draws=400, seed=r)
        i = block_bootstrap_means(x, block=1, draws=400, seed=r)
        block_cov += np.quantile(b, 0.05) <= 0.0 <= np.quantile(b, 0.95)
        iid_cov += np.quantile(i, 0.05) <= 0.0 <= np.quantile(i, 0.95)
    block_cov /= reps
    iid_cov /= reps
    assert 0.78 <= block_cov <= 0.97, block_cov
    assert iid_cov < block_cov - 0.08, (iid_cov, block_cov)


def test_block_length_grows_with_dependence_and_a_block_of_one_is_the_plain_bootstrap():
    assert block_length(_ar1(400, 0.8, 1)) > block_length(_ar1(400, 0.0, 1))
    x = _ar1(100, 0.0, 2)
    a = block_bootstrap_means(x, block=1, draws=50, seed=3)
    assert a.shape == (50,) and abs(a.mean() - x.mean()) < 0.3


def test_the_measurement_meets_the_contract_and_the_null_is_over_positions():
    template = spec(entries=(Entry(EntryKind.COIN_FLIP, Side.LONG, (("seed", 3),)),), order_type=OrderType.MARKET,
                    exits=(Exit(ExitKind.TIME, (("bars", 5),)),))
    world = {n: random_walk(n, days=250, seed=s, sigma_daily=0.02) for n, s in (("A", 1), ("B", 2), ("C", 3))}
    m = position_boxed.measure(template, {"stop": [2.0, 3.0]},
                               lambda t, p: t.replace(stop=Stop(StopKind.PERCENT, p["stop"])),
                               world, seed=5, cost_in_r=0.01, null_draws=200)
    assert m.engine == "position_boxed" and len(m.null_ev) == 200 and m.search_space_size == 2
    assert all(t.day == t.day for c in m.cells for t in c.trades) and m.winner.n < 250 * 3  # holds span days
ENGINE = position_boxed


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
