"""M4.2 actions not gaps · M4.3 delisting on terms · M4.4 instants
everywhere · M4.5 date-only as_of · M4.6 partitions · M4.7 one reserve look
· M4.10 the universe rule."""

from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from occams.config import InformationAxis
from occams.data.actions import Action, ActionKind, ActionSeries, explained_move, rebase, stop_fires
from occams.data.bars import Bars, random_walk
from occams.data.instants import Claim, NotAnInstant, end_of_day_utc, instant, session_close, usable
from occams.data.partitions import Partitions
from occams.data.universe import Listing, evaluate
from occams.engine import day_boxed
from occams.guards import Refused, reserve
from occams.register import Register
from occams.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing, Stop,
                         StopKind, StrategySpec, UniverseRule, to_engine)

CAPS = frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS})


def spec(**kw):
    base = dict(entries=(Entry(EntryKind.BREAKOUT_HIGH, Side.LONG, (("lookback", 2),)),),
                exits=(Exit(ExitKind.TIME, (("bars", 1),)),), stop=Stop(StopKind.PERCENT, 2.0), sizing=Sizing(),
                order_type=OrderType.STOP, horizon=Horizon.INTRADAY, universe=UniverseRule((("venue", "NYSE"),)),
                required_capabilities=CAPS, axis=InformationAxis.PRICE_DAILY)
    base.update(kw)
    return StrategySpec(**base)


def bars(rows, name="S"):
    o, h, lo, c = zip(*rows)
    return Bars(name, tuple(map(float, o)), tuple(map(float, h)), tuple(map(float, lo)), tuple(map(float, c)),
                tuple(1.0 for _ in rows), tuple(range(len(rows))))


# ---- M4.2 -----------------------------------------------------------------

SPLIT = ActionSeries((Action(ActionKind.SPLIT, "S", day=2, ratio=2.0),))
# days 0-1 print near 100; a 2:1 split takes effect on day 2, which prints near 50
SPLIT_BARS = bars([(100.0, 102.0, 99.0, 101.0), (101.0, 103.0, 100.0, 102.0),
                   (50.8, 52.5, 50.5, 52.0), (52.0, 53.0, 51.5, 52.5)])


def test_a_split_loads_as_an_action_and_the_breakout_level_is_rebased():
    """Without the action the level is 103 and day 2 never fills; with it
    the level is 51.5 on the new basis and the breakout fills at 51.5."""
    with_actions = day_boxed.run(to_engine(spec()), {"S": SPLIT_BARS}, seed=0, actions=SPLIT)
    without = day_boxed.run(to_engine(spec()), {"S": SPLIT_BARS}, seed=0)
    assert [t.day for t in with_actions][:1] == [2] and with_actions[0].entry == pytest.approx(51.5)
    assert all(t.day != 2 for t in without)


def test_the_move_at_a_split_is_explained_not_a_gap():
    prev_close = SPLIT_BARS.close[1]  # 102 on the old basis
    assert explained_move(prev_close, name="S", prev_day=1, day=2, series=SPLIT) == pytest.approx(51.0)
    assert rebase(102.0, name="S", from_day=1, to_day=2, series=SPLIT) == pytest.approx(51.0)
    assert rebase(102.0, name="S", from_day=1, to_day=1, series=SPLIT) == 102.0


def test_the_stop_does_not_fire_on_the_split_print():
    """A long from day 1 with a stop at 98 on the old basis: day 2 prints
    50.8-52.5. Compared raw, the print is 'through' the stop; restated to
    the new basis the stop is 49 and nothing fired."""
    naive_breach = SPLIT_BARS.open[2] <= 98.0
    assert naive_breach
    assert stop_fires(long=True, stop_level=98.0, name="S", stop_day=1, day=2, bar_open=50.8, bar_low=50.5,
                      bar_high=52.5, series=SPLIT) is False
    assert stop_fires(long=True, stop_level=98.0, name="S", stop_day=1, day=2, bar_open=48.0, bar_low=47.0,
                      bar_high=52.5, series=SPLIT) is True  # a real breach on the new basis still fires


def test_dividends_rebase_too():
    div = ActionSeries((Action(ActionKind.DIVIDEND, "S", day=2, amount=1.5),))
    assert rebase(102.0, name="S", from_day=1, to_day=2, series=div) == pytest.approx(100.5)


# ---- M4.3 -----------------------------------------------------------------

def test_a_delisting_closes_the_position_at_the_recorded_terms():
    delist = ActionSeries((Action(ActionKind.DELISTING, "S", day=3, terms=12.34, provenance="fixture"),))
    b = bars([(100, 101, 99, 100.5), (100.5, 101.5, 100, 101), (101, 102, 100.5, 101.5), (101.5, 103, 101, 102.5)])
    s = spec(entries=(Entry(EntryKind.ALWAYS, Side.LONG),), order_type=OrderType.MARKET)
    trades = day_boxed.run(to_engine(s), {"S": b}, seed=0, actions=delist)
    last = trades[-1]
    assert last.day == 3 and last.reason == "delisted" and last.exit == 12.34
    assert last.gross_r < -1.0  # worse than planned risk, and recorded as such


# ---- M4.4 / M4.5 ------------------------------------------------------------

def test_cross_venue_same_date_is_refused_by_instant_where_a_date_would_allow_it():
    d = date(2026, 6, 15)
    lse_close = session_close(d, "LSE")      # 15:30Z in summer
    nyse_close = session_close(d, "NYSE")    # 20:00Z
    known = datetime(2026, 6, 15, 18, 0, tzinfo=timezone.utc)  # a regime label computed at 18:00Z
    assert lse_close.date() == nyse_close.date() == known.date()  # a date comparison sees no difference
    assert usable(nyse_close, known) is True
    assert usable(lse_close, known) is False  # the LSE bar closed before the label existed


def test_dates_and_naive_datetimes_are_not_instants():
    with pytest.raises(NotAnInstant):
        instant(date(2026, 6, 15))
    with pytest.raises(NotAnInstant):
        instant(datetime(2026, 6, 15, 12, 0))
    assert instant(datetime(2026, 6, 15, 12, 0, tzinfo=ZoneInfo("Europe/London"))).hour == 11


def test_bars_refuse_naive_close_instants():
    with pytest.raises(NotAnInstant):
        Bars("X", (1.0,), (1.0,), (1.0,), (1.0,), (1.0,), (0,), close_at=("2026-06-15T16:00:00",))


def test_a_date_only_as_of_is_read_as_end_of_day_so_that_days_bar_is_unusable():
    claim = Claim.from_as_of("GOOGL traded at 327.65 intraday", date(2026, 7, 27))
    assert claim.known_at == end_of_day_utc(date(2026, 7, 27))
    for venue in ("LSE", "NYSE"):
        assert usable(session_close(date(2026, 7, 27), venue), claim.known_at) is False
    assert usable(session_close(date(2026, 7, 28), "LSE"), claim.known_at) is True
    precise = Claim.from_as_of("same fact, at 11:39 New York", datetime(2026, 7, 27, 11, 39, tzinfo=ZoneInfo("America/New_York")))
    assert usable(session_close(date(2026, 7, 27), "NYSE"), precise.known_at) is True


# ---- M4.6 / M4.7 ------------------------------------------------------------

def test_partitions_are_stamped_into_the_result():
    parts = Partitions(0.25, 0.5, 0.25)
    world = {n: random_walk(n, days=200, seed=3, sigma_daily=0.02) for n in ("A", "B", "C")}
    sliced = {n: parts.slice(b, "measurement")[0] for n, b in world.items()}
    bounds = parts.bounds(200)["measurement"]
    template = spec(entries=(Entry(EntryKind.COIN_FLIP, Side.LONG, (("seed", 1),)),), order_type=OrderType.MARKET)
    m = day_boxed.measure(template, {"stop": [2.0, 3.0]}, lambda t, p: t.replace(stop=Stop(StopKind.PERCENT, p["stop"])),
                          sliced, seed=1, cost_in_r=0.0, null_draws=100, partition="measurement",
                          partition_bounds=bounds, split=parts.as_tuple())
    assert m.partition == "measurement" and m.partition_bounds == (50, 150) and m.split == (0.25, 0.5, 0.25)
    assert all(50 <= t.day < 150 for c in m.cells for t in c.trades)


def test_the_forward_window_is_not_a_partition():
    with pytest.raises(KeyError, match="wall-clock"):
        Partitions(0.25, 0.5, 0.25).slice(random_walk("A", days=10, seed=1, sigma_daily=0.01), "forward")
    with pytest.raises(ValueError):
        Partitions(0.25, 0.5, 0.3)


def test_one_reserve_look_per_spec_hash(tmp_path):
    reg = Register(tmp_path / "r.jsonl")
    reserve.look("hash-A", "H-1", reg)
    with pytest.raises(Refused, match="second look is refused"):
        reserve.look("hash-A", "H-2", reg)
    reserve.look("hash-B", "H-2", reg)  # a different spec is a different hash
    types = [r["type"] for r in reg.records()]
    assert types.count("ReserveLook") == 2 and "RefusalRecorded" in types


# ---- M4.10 -------------------------------------------------------------------

LISTINGS = (
    Listing("SURVIVOR", "NYSE", listed_day=0),
    Listing("GONE2020", "NYSE", listed_day=0, delisted_day=2020),
    Listing("NEW2021", "NYSE", listed_day=2021),
    Listing("LSE1", "LSE", listed_day=0),
)


def test_a_universe_evaluated_for_2019_contains_a_name_that_delisted_in_2020():
    rule = UniverseRule((("venue", "NYSE"),))
    in_2019 = evaluate(rule, LISTINGS, as_of_day=2019)
    in_2021 = evaluate(rule, LISTINGS, as_of_day=2021)
    assert "GONE2020" in in_2019 and "GONE2020" not in in_2021
    assert "NEW2021" not in in_2019 and "NEW2021" in in_2021
    assert "LSE1" not in in_2019


def test_liquidity_terms_need_liquidity_and_unknown_is_not_membership():
    rule = UniverseRule((("venue", "NYSE"), ("min_adv_shares", 1000)))
    assert evaluate(rule, LISTINGS, as_of_day=2019, adv={"SURVIVOR": 5000, "GONE2020": 10}) == {"SURVIVOR"}
    assert evaluate(rule, LISTINGS, as_of_day=2019, adv=None) == frozenset()


def test_an_unknown_term_is_refused_not_ignored():
    with pytest.raises(ValueError, match="no evaluator knows"):
        evaluate(UniverseRule((("sector", "tech"),)), LISTINGS, as_of_day=1)


def test_pooled_partitions_share_one_calendar_boundary():
    """Two series with different start dates: cut per series, their
    definition slices end on different dates and one name's definition
    overlaps another's measurement in calendar time; cut on the common span
    they share one boundary (ADR-0005)."""
    a = random_walk("A", days=1000, seed=1, sigma_daily=0.01)
    b_raw = random_walk("B", days=600, seed=2, sigma_daily=0.01)
    b = Bars("B", b_raw.open, b_raw.high, b_raw.low, b_raw.close, b_raw.volume, tuple(d + 200 for d in b_raw.day))  # starts later
    parts = Partitions(0.3, 0.5, 0.2)
    own_a = parts.slice(a, "definition")[1]
    own_b = parts.slice(b, "definition")[1]
    assert own_a[1] != own_b[1]  # per-series cuts disagree on the boundary
    span = Partitions.common_span({"A": a, "B": b})
    ca = parts.slice(a, "definition", span=span)[1]
    cb = parts.slice(b, "definition", span=span)[1]
    assert ca == cb == (0, 300)  # one boundary for both
    assert max(parts.slice(b, "definition", span=span)[0].day) < 300
    assert min(parts.slice(a, "measurement", span=span)[0].day) >= 300
    late = Bars("C", b_raw.open, b_raw.high, b_raw.low, b_raw.close, b_raw.volume, tuple(d + 400 for d in b_raw.day))
    assert parts.slice(late, "definition", span=span)[0].n == 0  # listed after the boundary: no definition bars, no error
