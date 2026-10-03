"""The suite runs with no AWS and no network. The vendored archive tests
expect the bogus credentials the donor's CI sets; set them here too so a bare
``pytest`` behaves like CI instead of reaching for a real keychain."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("AWS_ACCESS_KEY_ID", "ci-has-no-aws")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "ci-has-no-aws")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("OCCAMS_RESEARCH_BUCKET", "ci-has-no-bucket")


@pytest.fixture(autouse=True)
def _the_suite_runs_on_a_supplied_identity(request, monkeypatch):
    """ADR-0055: dirty or unknown code does not measure — and a change under development is
    dirty code. The suite is therefore supplied a clean identity: the tree's own commit when
    it can be read, a placeholder when it cannot (a source archive with no repository), and
    no dirty paths. A test marked ``real_identity`` reads the tree itself."""
    if request.node.get_closest_marker("real_identity"):
        return
    from occams import identity

    head = identity.commit()
    monkeypatch.setattr(identity, "commit", lambda root=identity.ROOT: head if head != identity.UNKNOWN else "0" * 40)
    monkeypatch.setattr(identity, "dirty_paths", lambda root=identity.ROOT: ())
