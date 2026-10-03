"""M2.3 — two append-only stores joined by spec hash. Rewriting history
fails; S7 holds by type."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from occams.register import (Money, NotPublishable, Operations, OrderIntent, Register,
                             RefusalRecorded, TamperedHistory, register_record)


def test_rewriting_history_fails(tmp_path):
    reg = Register(tmp_path / "r.jsonl")
    reg.append(RefusalRecorded("a->b", "one", {}, None, None))
    reg.append(RefusalRecorded("a->b", "two", {}, None, None))
    assert reg.verify() == 2
    text = reg.path.read_text().replace('"reason":"one"', '"reason":"won"')
    reg.path.write_text(text)
    with pytest.raises(TamperedHistory):
        reg.verify()
    with pytest.raises(TamperedHistory):
        reg.append(RefusalRecorded("a->b", "three", {}, None, None))  # cannot extend a rewritten chain


def test_deleting_a_record_fails(tmp_path):
    reg = Register(tmp_path / "r.jsonl")
    for i in range(3):
        reg.append(RefusalRecorded("a->b", str(i), {}, None, None))
    lines = reg.path.read_text().splitlines()
    reg.path.write_text("\n".join(lines[:1] + lines[2:]) + "\n")
    with pytest.raises(TamperedHistory):
        reg.verify()


def test_s7_a_money_typed_field_cannot_be_a_register_record():
    with pytest.raises(NotPublishable):
        @register_record
        @dataclass(frozen=True)
        class Bad:
            spec_hash: str
            risk: Money


def test_s7_a_money_named_field_cannot_be_a_register_record():
    with pytest.raises(NotPublishable):
        @register_record
        @dataclass(frozen=True)
        class Bad:
            spec_hash: str
            account_currency: str


def test_s7_an_operations_record_is_refused_by_the_register(tmp_path):
    reg = Register(tmp_path / "r.jsonl")
    with pytest.raises(TypeError):
        reg.append(OrderIntent("h", "X", "buy", 1.0, Money(1.0, "XXX")))
    ops = Operations(tmp_path / "o.jsonl")
    ops.append(OrderIntent("h", "X", "buy", 1.0, Money(1.0, "XXX")))
    assert ops.records()[0]["risk"] == {"amount": 1.0, "currency": "XXX"}


def test_the_register_holds_no_currency_string_anywhere(tmp_path):
    reg = Register(tmp_path / "r.jsonl")
    reg.append(RefusalRecorded("a->b", "x", {"p": 0.1}, "abc", "H-1"))
    text = reg.path.read_text().lower()
    for w in ("currency", "gbp", "usd", "amount"):
        assert w not in text


def test_stores_are_joined_by_spec_hash(tmp_path):
    reg = Register(tmp_path / "r.jsonl")
    ops = Operations(tmp_path / "o.jsonl")
    reg.append(RefusalRecorded("a->b", "x", {}, "hash-1", None))
    ops.append(OrderIntent("hash-1", "X", "buy", 1.0, Money(1.0, "XXX")))
    assert reg.records()[0]["spec_hash"] == ops.records()[0]["spec_hash"] == "hash-1"


def test_records_carry_an_instant_not_a_date(tmp_path):
    reg = Register(tmp_path / "r.jsonl")
    at = reg.append(RefusalRecorded("a->b", "x", {}, None, None))["payload"]["at"]
    assert "T" in at and at.endswith("+00:00")


# ---- M14.6: the module is a package; nothing recorded changed ------------------------------------

PUBLIC_NAMES = (
    "CalendarFrozen", "ClassifierFrozen", "EraDecomposition", "Exposure", "FORBIDDEN_IN_REGISTER", "ForwardFill",
    "ForwardWindowOpened", "ForwardWindowResolved", "GuardEvidence", "HypothesisMeasured", "HypothesisRegistered", "HypothesisResolved",
    "LabClosed", "Money", "NotPublishable", "Operations", "OrderIntent", "PathsArchived", "ProgrammeStopped",
    "ProposalIssued", "RefusalRecorded", "Register", "ReserveLook", "RollMeasured", "Shrinkage", "Store", "StrategyTransitioned",
    "SurveyRecorded", "TamperedHistory", "UniverseDeclared", "_plain", "canonical", "now", "operations_record",
    "register_record",
)


def test_the_package_exposes_every_name_the_module_had_and_binds_the_records_to_their_stores():
    import occams.register as pkg
    from occams.register import records, store

    assert all(hasattr(pkg, n) for n in PUBLIC_NAMES) and set(pkg.__all__) == set(PUBLIC_NAMES)
    # the record types live in records.py, the chain machinery in store.py, the two stores bind them here
    record_types = [getattr(records, n) for n in dir(records) if getattr(getattr(records, n), "__register_record__", False)
                    or getattr(getattr(records, n), "__operations_record__", False)]
    assert len(record_types) == 23 and all(t.__module__ == "occams.register.records" for t in record_types)
    assert store.Store.__module__ == "occams.register.store" and not any(getattr(store, n, None) is Register for n in dir(store))
    assert pkg.Register.__module__ == "occams.register" and pkg.Operations.__module__ == "occams.register"
    # the nineteen defined here are attached to Register (other modules attach their own, e.g. the ledger's)
    attached = {n for n in dir(Register) if getattr(getattr(Register, n), "__register_record__", False)}
    defined = {t.__name__ for t in record_types if getattr(t, "__register_record__", False)}
    assert len(defined) == 19 and defined <= attached and all(getattr(Register, n) is getattr(records, n) for n in defined)
    assert pkg.HypothesisRegistered.__name__ == "HypothesisRegistered"    # the chain's ``type`` is the class name, unmoved


def test_every_committed_register_and_queue_still_verifies_and_every_record_type_resolves():
    """The lab's six files, read-only: the chain hashes payloads, never code, so a move must change nothing."""
    from pathlib import Path

    from occams.question import QuestionQueue

    root = Path(__file__).resolve().parent.parent / "register"
    registers = sorted(p for p in root.glob("*.jsonl") if not p.name.endswith("-queue.jsonl") and p.name != "queue.jsonl")
    queues = sorted(p for p in root.glob("*.jsonl") if p not in registers)
    assert len(registers) == 3 and len(queues) == 3
    for p in registers:
        reg = Register(p)
        n = reg.verify()
        assert n == len(reg.chain()) > 0
        for rec in reg.records():
            cls = getattr(Register, rec["type"], None)
            assert cls is not None and getattr(cls, "__register_record__", False), (p.name, rec["type"])
    for p in queues:
        assert isinstance(QuestionQueue(p).questions(), (list, tuple))
