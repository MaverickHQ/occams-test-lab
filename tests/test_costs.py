"""M5.1 the equity cost model · M5.2 bounded to approve · M5.3 FX conversion
is a cost, drift is not · M5.4 drift as a money exposure · M5.5-M5.7 the
obtainability auditors, per family, default-deny, with the fill signature."""

from __future__ import annotations

import dataclasses

import pytest

from occams.config import InformationAxis
from occams.costs.auditors import (FAMILY_AUDITORS, Fill, UnauditedFamily, audit, check_fill, family_of,
                                   halt, opening_auction, overnight_gap)
from occams.costs.equity import (DECLARED_SPREAD, EquityCosts, InstrumentClass, SpreadObservation,
                                 measured_spread, net_r)
from occams.costs.fx import FxAtEntry, drift_exposure, exposure_against_limit, net_r_instrument
from occams.data.actions import Action, ActionKind, ActionSeries
from occams.data.bars import random_walk
from occams.engine import day_boxed
from occams.guards import approve, clears_floor
from occams.hypothesis import Gates, Hypothesis, HypothesisState, PowerPlan, Tier, Verdict
from occams.measurement import Floor
from occams.register import Money, NotPublishable, register_record
from occams.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing, Stop,
                         StopKind, StrategySpec, UniverseRule, to_engine)
from occams.strategy import Strategy, StrategyState
from types import SimpleNamespace

CAPS = frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS})


def costs(cls=InstrumentClass.US_LARGE, *, instrument="USD", account="GBP", low=False):
    return EquityCosts.declared(cls, instrument_currency=instrument, account_currency=account, low=low)


# ---- M5.1 -----------------------------------------------------------------

@pytest.mark.parametrize("cls,instrument,account,fixed", [
    (InstrumentClass.LSE_SHARE, "GBP", "GBP", 0.0050),      # SDRT on the purchase
    (InstrumentClass.LSE_ETF_GBP, "GBP", "GBP", 0.0000),    # no SDRT, no FX
    (InstrumentClass.US_LARGE, "USD", "GBP", 0.0030),       # two conversion legs (SEC fee is 0.00002)
    (InstrumentClass.US_LARGE, "USD", "USD", 0.0000),       # no per-trade FX in a USD account
    (InstrumentClass.EU_SHARE, "EUR", "GBP", 0.0070),       # FX both ways + FTT as the bound
])
def test_round_trip_fixed_components_match_the_m0_2_table(cls, instrument, account, fixed):
    c = costs(cls, instrument=instrument, account=account)
    assert c.fixed_fraction() == pytest.approx(fixed, abs=5e-5)


def test_the_spread_is_declared_until_measured_and_the_model_says_so():
    c = costs()
    assert c.basis == "declared" and "M5.0" in c.spread.provenance
    assert c.bound().basis == "bounded" and c.bound().spread.fraction == DECLARED_SPREAD[InstrumentClass.US_LARGE][1]
    obs = tuple(SpreadObservation("XYZ", "2026-09-11T14:30:00+00:00", 99.99, 100.01, p) for p in ("open", "mid", "close"))
    m = c.with_measured(obs, provenance="demo account, 2026-09-11, author")
    assert m.basis == "measured" and m.spread.observations == 3 and m.bound() is m


def test_a_measurement_needs_open_mid_and_close_phases():
    obs = (SpreadObservation("XYZ", "t", 99.99, 100.01, "open"),)
    with pytest.raises(ValueError, match="phases"):
        measured_spread(obs, provenance="p")


def test_cost_in_r_is_c_over_s():
    c = costs()  # 0.30 % FX + 0.10 % spread (upper end) = 0.40 %
    assert c.round_trip_fraction() == pytest.approx(0.0040, abs=5e-5)
    assert c.cost_in_r(entry_price=100.0, stop_distance=2.0) == pytest.approx(0.20, abs=0.003)  # 0.40 % / 2 % = 0.20R
    assert c.cost_in_r(entry_price=100.0, stop_distance=5.0) == pytest.approx(0.08, abs=0.002)


def test_ptm_levy_applies_above_the_threshold_on_lse_names_only():
    lse = costs(InstrumentClass.LSE_ETF_GBP, instrument="GBP", account="GBP")
    assert lse.round_trip_fraction(notional_gbp=5_000) == lse.round_trip_fraction()
    assert lse.round_trip_fraction(notional_gbp=20_000) == pytest.approx(lse.round_trip_fraction() + 3.0 / 20_000)
    us = costs()
    assert us.round_trip_fraction(notional_gbp=20_000) == us.round_trip_fraction()


def test_no_field_is_shared_with_the_donor_futures_costs():
    from occams.costs.equity import EquityCosts
    names = {f.name for f in dataclasses.fields(EquityCosts)}
    assert names.isdisjoint({"multiplier", "tick_size", "commission_per_side", "slippage_ticks"})


# ---- M5.2 -----------------------------------------------------------------

def _spec():
    return StrategySpec(entries=(Entry(EntryKind.ALWAYS, Side.LONG),), exits=(Exit(ExitKind.TIME, (("bars", 1),)),),
                        stop=Stop(StopKind.PERCENT, 2.0), sizing=Sizing(), order_type=OrderType.MARKET,
                        horizon=Horizon.INTRADAY, universe=UniverseRule((("world", "synthetic"),)),
                        required_capabilities=CAPS, axis=InformationAxis.PRICE_DAILY)


def _measure(costs_model, seed=4):
    world = {n: random_walk(n, days=300, seed=seed, sigma_daily=0.02, drift_daily=0.004) for n in ("A", "B", "C")}
    return day_boxed.measure(_spec(), {"stop": [2.0, 3.0]},
                             lambda t, p: t.replace(stop=Stop(StopKind.PERCENT, p["stop"])),
                             world, seed=seed, cost_in_r=0.0, null_draws=200, costs=costs_model)


def test_a_strategy_clearing_only_under_optimistic_costs_is_refused():
    # a wide-spread class where the declared range is 0.05-0.15 %; the drift is tuned
    # so the winner clears a 0.10R floor at the low end of the range and not at the bound
    optimistic = _measure(costs(InstrumentClass.LSE_SHARE, instrument="GBP", account="GBP", low=True))
    bounded = _measure(costs(InstrumentClass.LSE_SHARE, instrument="GBP", account="GBP").bound())
    assert optimistic.cost_basis == "declared" and bounded.cost_basis == "bounded"
    assert bounded.winner.ev < optimistic.winner.ev
    floor = Floor((optimistic.winner.ev + bounded.winner.ev) / 2, 1)  # between the two: only optimism clears it
    assert clears_floor.check(optimistic, floor) is None
    assert clears_floor.check(bounded, floor) is not None


def test_approval_refuses_a_verdict_not_reached_under_the_bound():
    s = Strategy(identity=(("stop", 1.0),), state=StrategyState.FORWARD)
    h = Hypothesis(id="H", tier=Tier.MECHANISM, axis=InformationAxis.PRICE_DAILY, mechanism="m", if_true="t",
                   if_false="f", falsifier="x", floor=Floor(0.1, 1), power_plan=PowerPlan(1.0, 0.05, 0.8, 100, alternative_ev_net_r=0.4),
                   gates=Gates(1, 1.0, 0.5, 50.0), search_space_size=1, state=HypothesisState.RESOLVED,
                   verdict=Verdict("supported", 0.3, 100, s.spec_hash, "e", 1, "measurement", (), cost_basis="declared"))
    r = approve.check(s, SimpleNamespace(hypothesis=h))
    assert r is not None and "optimistic" in r.reason
    h2 = dataclasses.replace(h, verdict=dataclasses.replace(h.verdict, cost_basis="bounded"))
    assert approve.check(s, SimpleNamespace(hypothesis=h2)) is None
    h3 = dataclasses.replace(h, verdict=dataclasses.replace(h.verdict, cost_basis="measured"))
    assert approve.check(s, SimpleNamespace(hypothesis=h3)) is None


# ---- M5.3 / M5.4 ------------------------------------------------------------

def test_net_r_is_the_same_for_any_foreign_account_currency_and_any_fx_path():
    """USD instrument. GBP and EUR accounts both convert; the rate at exit
    never enters net R because R was converted once, at entry."""
    pnl, cost = 40.0, 4.0  # USD
    gbp = net_r_instrument(pnl_instrument=pnl, costs_instrument=cost, risk_account=10.0, fx_entry=FxAtEntry(1.25))
    eur = net_r_instrument(pnl_instrument=pnl, costs_instrument=cost, risk_account=10.0 * 1.25 / 1.10, fx_entry=FxAtEntry(1.10))
    assert gbp == pytest.approx(eur) == pytest.approx((40 - 4) / 12.5)
    # the FX path is irrelevant: nothing about the exit rate is an input
    import inspect
    assert "fx_exit" not in inspect.signature(net_r_instrument).parameters


def test_a_domestic_account_differs_by_exactly_the_conversion_charge():
    foreign = costs(InstrumentClass.US_LARGE, instrument="USD", account="GBP")
    domestic = costs(InstrumentClass.US_LARGE, instrument="USD", account="USD")
    other = costs(InstrumentClass.US_LARGE, instrument="USD", account="EUR")
    assert foreign.cost_in_r(entry_price=100, stop_distance=2) == pytest.approx(other.cost_in_r(entry_price=100, stop_distance=2))
    diff = foreign.cost_in_r(entry_price=100, stop_distance=2) - domestic.cost_in_r(entry_price=100, stop_distance=2)
    assert diff == pytest.approx(2 * 0.0015 * 100 / 2)  # two conversion legs, in R
    assert net_r(1.0, diff) == pytest.approx(1.0 - 0.15)


def test_fx_drift_is_money_against_the_limit_and_can_never_reach_the_register():
    d = drift_exposure(position_value_instrument=1250.0, fx_entry=1.25, fx_now=1.20, account_currency="GBP")
    assert isinstance(d, Money) and d.currency == "GBP" and d.amount == pytest.approx(1250 / 1.20 - 1000)
    e = exposure_against_limit(open_value_instrument=1250.0, fx_now=1.25, limit_account=2000.0, account_currency="GBP")
    assert e.within_limit and e.open_value_account.amount == pytest.approx(1000)
    with pytest.raises(NotPublishable):
        @register_record
        @dataclasses.dataclass(frozen=True)
        class Leak:
            spec_hash: str
            drift: Money


# ---- M5.5 / M5.6 / M5.7 -------------------------------------------------------

def fill(**kw) -> Fill:
    base = dict(price=100.0, bar_index=5, order_kind="market", side=Side.LONG, level=None, prior_close=99.0,
                bar_open=100.0, bar_high=101.0, bar_low=99.5, bar_volume=1e6, next_open=100.5, name="X",
                prior_day=4, day=5)
    base.update(kw)
    return Fill(**base)


def test_the_fill_signature_carries_prior_close_and_next_open_by_type():
    with pytest.raises(TypeError):
        Fill(price=100.0, bar_index=5, order_kind="market", side=Side.LONG, level=None)  # type: ignore[call-arg]
    f = fill()
    assert f.prior_close == 99.0 and f.next_open == 100.5


def test_overnight_gap_auditor_refuses_a_fill_at_a_level_nothing_traded():
    # buy stop at 99.5; the market gapped from 99.0 to 100.0 overnight; a fill booked AT 99.5 is fiction
    bad = fill(order_kind="stop", level=99.5, price=99.5)
    assert overnight_gap(bad) is not None and "inside the overnight gap" in overnight_gap(bad)
    good = fill(order_kind="stop", level=99.5, price=100.0)  # the engine's own answer: the open
    assert overnight_gap(good) is None


def test_overnight_gap_measures_from_the_action_restated_prior_close():
    split = ActionSeries((Action(ActionKind.SPLIT, "X", day=5, ratio=2.0),))
    # prior close 99 on the old basis is 49.5 on the new; the bar opens at 50: a stop at 49.8 sits in the gap
    f = fill(order_kind="stop", level=49.8, price=49.8, prior_close=99.0, bar_open=50.0, bar_high=51.0, bar_low=49.9)
    assert overnight_gap(f, split) is not None
    assert overnight_gap(fill(order_kind="stop", level=49.8, price=49.8, prior_close=49.7, bar_open=50.0, bar_high=51.0, bar_low=49.9)) is not None


def test_opening_auction_auditor_refuses_a_market_fill_at_the_decision_price():
    assert opening_auction(fill(price=99.0)) is not None   # booked at the prior close, not the auction print
    assert opening_auction(fill(price=100.0)) is None


def test_halt_auditor_refuses_a_fill_in_a_bar_that_did_not_trade():
    assert halt(fill(bar_volume=0.0)) is not None
    assert halt(fill(bar_open=100, bar_high=100, bar_low=100)) is not None
    assert halt(fill()) is None


def test_audit_is_default_deny_per_family_and_exhaustive():
    with pytest.raises(UnauditedFamily):
        audit("options-gamma-scalp", (fill(),))
    with pytest.raises(UnauditedFamily):
        audit("options-gamma-scalp", ())    # default-deny even with nothing to audit
    assert set(FAMILY_AUDITORS) == {"breakout", "trend", "apparatus", "reversal"}   # reversal: ADR-0037
    assert audit("breakout", (fill(),)) == ("",)
    bad = fill(order_kind="stop", level=99.5, price=99.5)
    why = check_fill("breakout", bad)
    assert "inside the overnight gap" in why and why.startswith("bar 5 X:")
    # ADR-0041: one sentence per fill, every fill, nothing raised — the engine drops the trade the sentence names
    assert audit("breakout", (fill(), bad) + (bad,) * 600) == ("", why) + (why,) * 600


def test_a_fill_at_the_open_passes_the_gap_auditor_whatever_its_level():
    # a stop that the bar opens through fills at the open (M3.8); a level a rounding error below that open is not "inside the gap"
    # (the CVX bar the first survey refused 112 cells on, ADR-0040)
    assert overnight_gap(fill(order_kind="stop", level=99.99999999999997, price=100.0, prior_close=99.0, bar_open=100.0)) is None
    assert overnight_gap(fill(order_kind="limit", level=99.5, price=99.5, prior_close=100.0, bar_open=99.0)) is not None


def test_an_unobtainable_entry_is_a_missed_trade_not_a_refused_run():
    from occams.engine import position_boxed
    from occams.spec import Horizon

    clean = random_walk("A", days=60, seed=3, sigma_daily=0.02)
    j = 19   # one flat bar: open = high = low, the halt auditor's rule — a source defect, not a signal; 19 = 1 + 3·6, an entry bar of the hold-3 cadence below
    flat = dataclasses.replace(clean, open=clean.open[:j] + (clean.close[j],) + clean.open[j + 1:],
                               high=clean.high[:j] + (clean.close[j],) + clean.high[j + 1:],
                               low=clean.low[:j] + (clean.close[j],) + clean.low[j + 1:])
    always = _spec()   # market entry on every box
    before = day_boxed.run(to_engine(always), {"A": clean}, seed=0)
    after = day_boxed.run(to_engine(always), {"A": flat}, seed=0)
    assert before.missed == () and len(after) == len(before) - 1 and len(after.missed) == 1
    (m,) = after.missed
    assert m.name == "A" and m.bar_index == j and "did not trade" in m.reason and all(t.entry_index != j for t in after)
    # the position-boxed engine: the missed entry opens nothing, so the next signal is free to enter
    multi = always.replace(horizon=Horizon.MULTI_DAY, exits=(Exit(ExitKind.TIME, (("bars", 3),)),))
    p = position_boxed.run(to_engine(multi), {"A": flat}, seed=0)
    assert len(p.missed) == 1 and p.missed[0].bar_index == j and any(t.entry_index == j + 1 for t in p)
    # audit_fills=False keeps every trade and misses nothing, as before
    assert day_boxed.run(to_engine(always), {"A": flat}, seed=0, audit_fills=False).missed == ()


def test_family_is_derived_from_the_entry_kinds():
    assert family_of(_spec()) == "apparatus"
    s = _spec().replace(entries=(Entry(EntryKind.BREAKOUT_HIGH, Side.LONG, (("lookback", 2),)),), order_type=OrderType.STOP)
    assert family_of(s) == "breakout"


def test_the_engines_own_fills_pass_their_family_audit():
    world = {"A": random_walk("A", days=120, seed=9, sigma_daily=0.02)}
    s = _spec().replace(entries=(Entry(EntryKind.BREAKOUT_HIGH, Side.LONG, (("lookback", 5),)),), order_type=OrderType.STOP)
    trades = day_boxed.run(to_engine(s), world, seed=0)  # audit_fills=True by default: raises if not obtainable
    assert trades and all(t.fill is not None for t in trades)
