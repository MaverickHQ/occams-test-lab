"""M2.2 — the Strategy lifecycle. Illegal transitions raise; a test
enumerates the full legal set."""

from __future__ import annotations

import itertools

import pytest

from occams.guards import Refused
from occams.register import Register
from occams.strategy import LEGAL, IllegalTransition, Strategy, StrategyState as S, spec_hash, transition


@pytest.fixture
def reg(tmp_path):
    return Register(tmp_path / "register.jsonl")


def test_the_full_legal_set_is_exactly_this():
    assert LEGAL == {
        (S.SPECIFIED, S.COMPILED), (S.COMPILED, S.MEASURED), (S.MEASURED, S.FORWARD),
        (S.FORWARD, S.APPROVED), (S.APPROVED, S.LIVE), (S.LIVE, S.HALTED), (S.HALTED, S.LIVE),
        (S.MEASURED, S.RETIRED), (S.FORWARD, S.RETIRED), (S.APPROVED, S.RETIRED),
        (S.LIVE, S.RETIRED), (S.HALTED, S.RETIRED),
    }


@pytest.mark.parametrize("a,b", [(a, b) for a, b in itertools.product(S, S) if (a, b) not in LEGAL])
def test_every_illegal_pair_raises_before_any_guard_runs(a, b, reg):
    s = Strategy(identity=(("stop", 1.0),), state=a)
    with pytest.raises(IllegalTransition):
        transition(s, b, register=reg)
    assert reg.records() == []  # nothing recorded: it never reached a guard


def test_a_refusal_leaves_the_strategy_unchanged_and_is_recorded(reg):
    s = Strategy.specify({"kind": "x"})  # no stop
    with pytest.raises(Refused):
        transition(s, S.COMPILED, register=reg)
    assert s.state is S.SPECIFIED
    assert reg.records()[-1]["type"] == "RefusalRecorded"


def test_a_pass_is_recorded_with_both_states(reg):
    s = Strategy.specify({"stop": 2.0})
    s2 = transition(s, S.COMPILED, register=reg)
    assert s2.state is S.COMPILED and s.state is S.SPECIFIED
    rec = reg.records()[-1]
    assert rec["type"] == "StrategyTransitioned" and (rec["from_state"], rec["to_state"]) == ("SPECIFIED", "COMPILED")


def test_hash_is_identity_not_context():
    a = spec_hash({"stop": 2.0, "entries": ["x"]})
    assert a == spec_hash({"entries": ["x"], "stop": 2.0})  # order is not identity
    assert a != spec_hash({"stop": 2.5, "entries": ["x"]})


def test_specify_sorts_identity_so_equal_specs_hash_equal():
    assert Strategy.specify({"b": 1, "a": 2}).spec_hash == Strategy.specify({"a": 2, "b": 1}).spec_hash
