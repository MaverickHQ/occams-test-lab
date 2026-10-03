"""M15.4 — `python -m occams init` writes the configuration skeleton with no value in
it and never overwrites; `python -m occams doctor` names what is missing and never
prints a secret."""

from __future__ import annotations

import re
from pathlib import Path

from occams.doctor import checks, doctor_main, init_main
from tests.test_console import config_on_disk

ROOT = Path(__file__).resolve().parent.parent


def test_init_writes_every_required_key_as_a_placeholder_and_never_a_value(tmp_path, capsys):
    out = tmp_path / "occams.toml"
    assert init_main(["--out", str(out)]) == 0
    text = out.read_text()
    assert "[capital]" in text and "[alpha]" in text and "[lab]" in text and "[partitions]" in text
    assert "falsifier_count = <int>" in text and "starting = <float>" in text
    # no number anywhere but the R-references in comments: a placeholder is not a default (R9, R4)
    values = [line for line in text.splitlines() if "=" in line and not line.lstrip().startswith("#")]
    assert values and all(re.search(r"=\s*<(float|int|str|bool)>", line) for line in values), values[:3]
    assert "keys to declare, no value supplied" in capsys.readouterr().out
    # never overwritten: a configuration is the author's document
    assert init_main(["--out", str(out)]) == 1 and "never overwritten" in capsys.readouterr().out
    assert out.read_text() == text


def test_doctor_names_what_is_missing_and_stops_at_the_configuration(tmp_path, capsys, monkeypatch):
    import occams.doctor as doctor

    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    monkeypatch.setattr(doctor, "_keychain_has", lambda service: False)      # this machine's Keychain is not the test's
    cfg = tmp_path / "occams.toml"
    rows = {name: (status, detail) for status, name, detail in checks(config=cfg, archive=tmp_path / "archive", env={}, cwd=ROOT)}
    assert rows["configuration"][0] == "missing" and "python -m occams init" in rows["configuration"][1]
    assert rows["archive"][0] == "note" and rows["interpreter"][0] == "ok" and rows["burst: tools/aws/burst.sh"][0] == "ok"
    assert rows["data key"][0] == "note" and "TIINGO_API_KEY is not set" in rows["data key"][1]
    assert doctor_main(["--config", str(cfg), "--archive", str(tmp_path / "archive")]) == 1
    out = capsys.readouterr().out
    assert "MISSING" in out and "the lab cannot start: configuration" in out
    # the skeleton: the unfilled keys are named
    init_main(["--out", str(cfg)])
    capsys.readouterr()
    rows = {name: (status, detail) for status, name, detail in checks(config=cfg, archive=tmp_path / "archive", env={}, cwd=ROOT)}
    assert rows["configuration"][0] == "missing" and "still a placeholder" in rows["configuration"][1] and "starting" in rows["configuration"][1]


def test_doctor_passes_on_a_declared_configuration_and_never_prints_the_key(tmp_path, capsys):
    cfg = Path(config_on_disk(tmp_path).path)
    secret = "not-a-real-key-0123456789"
    rows = {name: (status, detail) for status, name, detail in
            checks(config=cfg, archive=tmp_path / "archive", env={"TIINGO_API_KEY": secret}, cwd=ROOT)}
    assert rows["configuration"][0] == "ok" and rows["data key"][0] == "ok"
    assert all(secret not in detail for _s, detail in rows.values())
    assert doctor_main(["--config", str(cfg), "--archive", str(tmp_path / "archive")]) in (0, 1)   # AWS is advisory either way
    out = capsys.readouterr().out
    assert secret not in out and "configuration" in out and "burst: variables" in out and "REGISTER" in out
