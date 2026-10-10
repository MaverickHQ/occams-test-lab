"""M16.19 (ADR-0047) — the pages and the report show each diagnostic **beside the verdict it annotates, never in its
place**; the report is written from the diagnostics store alone and says it has no standing; and the closing statement
the author adopted is the bytes it was."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from occams import rescore, rescored
from occams.console import build as build_console
from occams.console.programme import build as build_programme
from occams.register import Diagnostics
from tests.test_rescore import _as_recorded, programme  # noqa: F401 — the fixture programme of one supported verdict

ROOT = Path(__file__).resolve().parents[1]
LAB_CONCLUSION_SHA256 = "c6df20358c3874313adf9a351b25884cd1e7863239558d32a85e04aaa448b625"      # the text of 2026-09-24 plus the note adopted 2026-10-10


@pytest.fixture
def annotated(programme, tmp_path):  # noqa: F811
    prog, archive, v, m = programme
    out = Diagnostics(Path(prog.register).parent / "diagnostics.jsonl")           # beside the Register, where a page looks for it
    (rec,) = rescore.run([prog], archive=archive, out=out, null_draws=300, measure_at_source=_as_recorded(v, m))
    return prog, rec, v


def test_the_console_shows_a_diagnostic_beside_its_verdict_and_never_in_its_place(annotated):
    prog, rec, v = annotated
    page, facts = build_console(prog.register, controls="none", generated="g", repo_sha="x")
    (fd,) = facts.findings
    assert fd.state == "supported" and fd.resolved["outcome"] == "supported"       # the finding's state is the Register's, whatever the diagnostic reads
    assert fd.rescored["hypothesis_id"] == "Q-1" and fd.rescored["reading"] == rec["reading"]
    card = page[page.index('class="card finding"'):]
    verdict, diagnostic = card.index("Verdict"), card.index("Re-scored under the corrected rules — a diagnostic, not a verdict")
    assert verdict < diagnostic                                                     # under the record, after it
    block = card[diagnostic:]
    assert "The verdict above stands as reached: <strong>supported</strong>" in block and "RESCORE-2026-10.html" in block
    assert "Recreated first" in block and "exactly, at its stamped source" in block and "Judged by" in block
    assert "beats-null" in block and "**" not in block
    # and with no diagnostics store beside the Register, the page is the page it was
    Path(prog.register).with_name("diagnostics.jsonl").unlink()
    plain, facts = build_console(prog.register, controls="none", generated="g", repo_sha="x")
    assert facts.findings[0].rescored is None and "Re-scored under the corrected rules" not in plain


def test_the_programme_page_carries_the_reading_beside_every_record(annotated):
    prog, rec, v = annotated
    page, progs = build_programme((prog.register,), generated="g", repo_sha="x")
    assert "Verdicts — every one beside where it came from" in page
    table = page[page.index("Re-scored under the corrected rules — a diagnostic beside each record, never a verdict"):]
    assert "Every outcome above stands as it was reached" in table and "It moves no falsifier and spends no alpha" in table
    assert rescored.one_line(rec).split(";")[0] in table and ">exactly<" in table and f"#{rec['annotates_seq']}" in table
    tiles = page[page.index('class="tiles"'):page.index("Lab falsifier")]
    assert ">1<" in tiles                                                           # one verdict, one supported: the count is the Register's


def test_the_report_is_written_from_the_diagnostics_alone_and_says_it_has_no_standing(tmp_path):
    records, head = rescored.load()
    text = rescored.report(records, head=head, count=len(records))
    assert text.splitlines()[2].startswith("**This document has no standing.**") and "nothing in it is a verdict" in text
    assert [ln[3:9].strip("`| ") for ln in text.splitlines() if ln.startswith("| `Q")] == ["Q-003", "Q-004", "Q-005", "Q2-001", "Q2-002", "Q3-001"]
    assert "| `Q2-001` | supported, EV +0.213 R over 6,946 trades; no check refused it | exactly | would be null; refused by floor, beats-always-long |" in text
    assert "Not recreated, so not re-scored" in text and "## What this is not" in text
    assert "| `Q3-001` | refused at measurement: 863 trades against 1,068 required | no |" in text
    assert rescored.revived(records) == [] and "No check that refused a question as recorded passes it here" in text
    back = [dict(r) for r in records]                                               # a store in which a recorded refusal now passes says so, in bold
    q = next(r for r in back if r["hypothesis_id"] == "Q2-002")
    q["checks"] = [dict(c, passed=True) for c in q["checks"]]
    assert rescored.revived(back) == [("Q2-002", "floor")]
    assert "**Q2-002's floor refused as recorded and would pass here**" in rescored.report(back, head=head, count=len(back))
    committed = (ROOT / rescored.REPORT).read_text(encoding="utf-8")
    assert committed == text                                                        # the committed report is this function of the committed store
    out = tmp_path / "r.md"
    assert rescored.main(["--out", str(out)]) == 0 and out.read_text(encoding="utf-8") == text
    assert rescored.main(["--diagnostics", str(tmp_path / "none.jsonl"), "--out", str(out)]) == 2


def test_the_closing_statement_is_the_bytes_the_author_adopted():
    """`docs/LAB-CONCLUSION.md` was adopted by the author on 2026-09-24. A re-score is written beside it; adopting a
    note on it into the closing statement is the author's act, and no row of M16 touched the file. On 2026-10-10 the
    author adopted a plain-language note on the re-score, appended under the text of 2026-09-24, which is unchanged."""
    digest = hashlib.sha256((ROOT / "docs" / "LAB-CONCLUSION.md").read_bytes()).hexdigest()
    assert digest == LAB_CONCLUSION_SHA256
