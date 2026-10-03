"""M1.5 — every vendored file matches its recorded hash, so a silent local
edit to "unchanged" code fails the build. The donor is not needed."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROV = json.loads((ROOT / "occams" / "core" / "PROVENANCE.json").read_text())


@pytest.mark.parametrize("row", PROV["files"], ids=[r["file"] for r in PROV["files"]])
def test_vendored_file_matches_recorded_hash(row):
    got = hashlib.sha256((ROOT / row["file"]).read_bytes()).hexdigest()
    assert got == row["vendored_sha256"], f"{row['file']} was edited after vendoring"


def test_provenance_names_the_donor_commit():
    assert PROV["donor"].endswith("/prop-challenge-lab")
    assert len(PROV["donor_commit"]) == 40
    assert len([r for r in PROV["files"] if r["kind"] == "module"]) == 12


def test_provenance_md_agrees_with_json():
    md = (ROOT / "PROVENANCE.md").read_text()
    assert PROV["donor_commit"] in md
    for r in PROV["files"]:
        assert r["vendored_sha256"][:16] in md, r["file"]
