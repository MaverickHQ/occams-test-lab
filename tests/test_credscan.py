"""S5 — the scanner must catch each listed shape. Fixtures are assembled at
runtime so this file does not itself trip the scan."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("_credscan", ROOT / "tools" / "credscan.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


PLANTED = {
    "aws access key": "AKIA" + "EXAMPLEKEY123456",
    "telegram bot token": "1234567890" + ":" + "AAH" + "x" * 32,
    "github token": "ghp_" + "a" * 36,
    "private key block": "-----BEGIN " + "RSA PRIVATE KEY-----",
    "assigned secret": "api_key" + " = " + '"' + "k" * 24 + '"',
    "basic auth in url": "https://" + "user:pass" + "@example.test/x",
}


@pytest.mark.parametrize("name,planted", sorted(PLANTED.items()))
def test_each_shape_is_caught(name, planted):
    cs = _load()
    hits = cs.scan_text("harmless line\n" + planted + "\nanother line\n")
    assert any(h[0] == name and h[1] == 2 for h in hits), (name, hits)


def test_the_tree_is_clean():
    cs = _load()
    assert cs.scan(ROOT) == []


def test_placeholders_do_not_trip_it():
    cs = _load()
    assert cs.scan_text('api_key = "<YOUR_API_KEY>"\ntoken: ${TOKEN}\n') == []
