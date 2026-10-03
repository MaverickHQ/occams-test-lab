"""M2.8 — `occams refusals`: what was searched, what it cost, why each thing
died — from the Register, without re-running anything."""
from __future__ import annotations

import pytest

from occams.controls import load_controls, run
from occams.refusals import report


def test_report_answers_from_the_register_alone(tmp_path):
    run("null", load_controls(), tmp_path)
    run("signal", load_controls(), tmp_path)
    out = report(tmp_path / "register.jsonl")
    assert "Searched: 2 hypotheses" in out
    assert "search-space cells 18" in out
    assert "alpha spent 0.0000" in out
    assert "CONTROL-NULL" in out and "refused at MEASURED->FORWARD: beats-null" in out
    assert "CONTROL-SIGNAL" in out
    assert "chain verified" in out


def test_report_reads_a_tampered_register_as_a_failure(tmp_path):
    from occams.register import TamperedHistory
    run("null", load_controls(), tmp_path)
    p = tmp_path / "register.jsonl"
    p.write_text(p.read_text().replace("CONTROL-NULL", "CONTROL-NULL2", 1))
    with pytest.raises(TamperedHistory):
        report(p)
