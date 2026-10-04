"""The price_daily proposer: a mechanism on daily bars alone, no regime
gate, through the engine the horizon selects."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from occams.config import InformationAxis, parse
from occams.data.archive import BarArchive
from occams.data.bars import Bars, random_walk
from occams.engine.day_boxed import NO_ACTIONS
from occams.hypothesis import Gates, HypothesisState
from occams.measurement import Floor
from occams.proposers.base import DraftQueue, Sandbox, Sweep, validate_draft
from occams.proposers.price import PRICE_ENTRIES, PriceProposer, price_template
from occams.proposers.regime import axis_sensitivity, precommit
from occams.question import from_draft, to_hypothesis
from occams.register import Register
from occams.spec.compile import to_engine
from occams.spec.spec import EntryKind, ExitKind, Horizon, OrderType
from tests.test_config import FIXTURE


def cfg():
    return parse(copy.deepcopy(FIXTURE), Path("fixture"))


def calendar_bars(name: str, *, first: int, days: int, seed: int, drift: float = 0.0) -> Bars:
    b = random_walk(name, days=days, seed=seed, sigma_daily=0.012, drift_daily=drift)
    return Bars(b.name, b.open, b.high, b.low, b.close, b.volume, tuple(first + i for i in range(b.n)))


@pytest.fixture
def world(tmp_path):
    a = BarArchive(tmp_path / "archive")
    for i, n in enumerate(("AAA", "BBB", "CCC")):
        a.put(calendar_bars(n, first=727592, days=1200, seed=20 + i), NO_ACTIONS, source_id="synthetic")
    return a, Register(tmp_path / "r.jsonl")


EXAMPLE_PARAMS = {EntryKind.CLOSE_BELOW_MA: dict(lookback=10), EntryKind.CLOSE_ABOVE_MA: dict(lookback=10),
                  EntryKind.BREAKOUT_HIGH: dict(lookback=10), EntryKind.BREAKOUT_LOW: dict(lookback=10), EntryKind.DOWN_RUN: dict(runs=3),
                  EntryKind.RETURN_BELOW: dict(lookback=5, percent=3.0), EntryKind.PULLBACK_IN_TREND: dict(short=5, long=50)}


def test_every_price_entry_compiles_for_both_horizons_and_declares_its_capabilities():
    assert set(EXAMPLE_PARAMS) == set(PRICE_ENTRIES)
    for entry in PRICE_ENTRIES:
        for horizon in (Horizon.MULTI_DAY, Horizon.INTRADAY):
            t = price_template(entry, hold_bars=3, horizon=horizon, **EXAMPLE_PARAMS[entry])
            compiled = to_engine(t)
            assert compiled is not None and t.regime is None and t.axis is InformationAxis.PRICE_DAILY
            assert t.order_type is (OrderType.STOP if entry is EntryKind.BREAKOUT_HIGH else
                                    OrderType.LIMIT if entry is EntryKind.BREAKOUT_LOW else OrderType.MARKET)
            assert [x.kind for x in t.exits] == [ExitKind.TIME]
    with pytest.raises(ValueError, match="not a price_daily entry"):
        price_template(EntryKind.ALWAYS, lookback=10, hold_bars=3)


def test_the_proposer_emits_a_draft_with_both_interpretations_and_no_alpha(tmp_path):
    reg = Register(tmp_path / "r.jsonl")
    sb = Sandbox.build(reg, DraftQueue(tmp_path / "d.jsonl"))
    p = PriceProposer(entry=EntryKind.CLOSE_BELOW_MA, lookback=10, hold_bars=3, floor=Floor(0.15, 50), sigma_r=1.2,
                      sigma_provenance="fixture", power=0.8, gates=Gates(4, 0.10, 0.5, 50.0),
                      sweep=Sweep((("stop", (3.0, 5.0)), ("hold", (3.0, 5.0)))))
    (d,) = p.propose(sb)
    validate_draft(d)
    assert d.axis is InformationAxis.PRICE_DAILY and "10-bar moving average" in d.mechanism and "3 bars" in d.mechanism
    assert d.search_space_size == 4 and not hasattr(d, "alpha")
    h = to_hypothesis(d, id="Q-p", available_n=1000, alpha=0.04)
    assert h.state is HypothesisState.DRAFT and reg.records() == []


def test_precommit_runs_a_multi_day_template_through_the_position_boxed_engine(world):
    arch, reg = world
    t = price_template(EntryKind.CLOSE_BELOW_MA, lookback=10, hold_bars=3, horizon=Horizon.MULTI_DAY)
    pre = precommit(t, archive=arch, cfg=cfg(), register=reg, seed=1)
    assert pre["definition_trades"] > 0 and pre["available_n"] > 0 and pre["context"] is None
    assert sorted(pre["names"]) == ["AAA", "BBB", "CCC"]
    assert pre["clustering"] is None or pre["clustering"].level.value == "index"
    sens = axis_sensitivity(t, Sweep((("stop", (3.0, 5.0)), ("hold", (3.0, 5.0)))), pre["definition_bars"], ctx=None, seed=1)
    assert 0.0 < sens["hold"] <= 1.0    # a longer hold changes trades in a multi-day position


def test_a_price_question_builds_from_the_draft_on_its_own_axis(world, tmp_path):
    from occams.ledger.alpha_budget import AlphaBudget
    arch, reg = world
    c = cfg()
    t = price_template(EntryKind.CLOSE_ABOVE_MA, lookback=20, hold_bars=5)
    p = PriceProposer(entry=EntryKind.CLOSE_ABOVE_MA, lookback=20, hold_bars=5, floor=Floor(0.15, 50), sigma_r=1.2,
                      sigma_provenance="fixture", power=0.8, gates=Gates(4, 0.10, 0.5, 50.0),
                      sweep=Sweep((("stop", (3.0, 5.0)), ("hold", (5.0, 10.0)))))
    (d,) = p.propose(Sandbox.build(reg, DraftQueue(tmp_path / "d.jsonl")))
    q = from_draft(d, id="Q-p", template=t, budget=AlphaBudget(c, reg, config_sha="fixture"), available_n=900)
    assert q.hypothesis.axis is InformationAxis.PRICE_DAILY and q.template.hash == t.hash


def test_precommit_promises_the_sweeps_thinnest_cell_not_the_templates_signals(world):
    """M13.9: the guard at measurement counts the winning cell's own trades (M8.2). A close below its average
    persists for days, so a hold-20 cell boxes most signals out; the promise is the thinnest cell's, and both
    numbers are returned so prepare can print them."""
    arch, reg = world
    t = price_template(EntryKind.CLOSE_BELOW_MA, lookback=10, hold_bars=3, horizon=Horizon.MULTI_DAY)
    plain = precommit(t, archive=arch, cfg=cfg(), register=reg, seed=1)
    assert plain["thinnest_cell"] is None and plain["template_available_n"] == plain["available_n"]
    pre = precommit(t, archive=arch, cfg=cfg(), register=reg, seed=1, sweep=Sweep((("hold", (3.0, 20.0)), ("stop", (3.0,)))))
    tc = pre["thinnest_cell"]
    assert tc["point"] == {"hold": 20.0, "stop": 3.0} and tc["definition_trades"] < pre["definition_trades"]
    assert pre["template_available_n"] == plain["available_n"] and pre["available_n"] == min(plain["available_n"], tc["available_n"])
    assert pre["available_n"] < plain["available_n"]                       # the hold-3 template promised more than hold 20 can hold
