"""The suite runs with no AWS and no network. The vendored archive tests
expect the bogus credentials the donor's CI sets; set them here too so a bare
``pytest`` behaves like CI instead of reaching for a real keychain."""

from __future__ import annotations

import os

os.environ.setdefault("AWS_ACCESS_KEY_ID", "ci-has-no-aws")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "ci-has-no-aws")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("OCCAMS_RESEARCH_BUCKET", "ci-has-no-bucket")
