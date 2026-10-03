"""M15.10 — the template grid loads and shows its hash; every entry kind belongs to an auditor family;
a kind without one is refused by name, which is the step docs/EXTENDING.md says the code enforces."""

from __future__ import annotations

from pathlib import Path

import pytest

from occams.costs import auditors
from occams.register import Register
from occams.spec.spec import EntryKind
from occams.survey.grid import load as load_grid, main as survey_main

ROOT = Path(__file__).resolve().parent.parent


def test_the_template_grid_loads_against_a_register_that_declares_its_universe_and_shows_its_hash(capsys):
    reg = Register(ROOT / "register" / "programme-3.jsonl")          # read only: index_etfs and SPY are records there
    g = load_grid(ROOT / "surveys" / "grid-template.toml", register=reg, plateau_cells=4)
    assert g.name == "grid-template" and g.count == 2 * 2 * 2 * 2 * 1 and len(g.families) == 4
    assert survey_main(["show", str(ROOT / "surveys" / "grid-template.toml"), "--register", str(ROOT / "register" / "programme-3.jsonl")]) == 0
    out = capsys.readouterr().out
    assert g.sha[:12] in out and "cells" in out


def test_every_entry_kind_belongs_to_an_auditor_family_and_one_without_is_refused_by_name(monkeypatch):
    assert set(EntryKind) <= set(auditors.FAMILY_OF)
    assert {auditors.FAMILY_OF[k] for k in EntryKind} <= set(auditors.FAMILY_AUDITORS)
    from tests.test_question import edge_template

    spec = edge_template()                                            # a DOWN_RUN entry
    assert auditors.family_of(spec) == "reversal"
    monkeypatch.setitem(auditors.FAMILY_OF, EntryKind.DOWN_RUN, None)
    monkeypatch.delitem(auditors.FAMILY_OF, EntryKind.DOWN_RUN)
    with pytest.raises(auditors.UnauditedFamily, match="down_run.*no auditor family"):
        auditors.family_of(spec)
