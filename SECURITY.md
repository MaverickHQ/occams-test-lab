# Security

This repository is a research lab that measures and refuses. By construction it
holds no credential, no account and no money figure (`make credscan`,
`make prepublish-all`; R5, R6, R9), it trades nothing (ADR-0044), and it runs
nowhere but on the machine that clones it. A security report here is therefore
about the record and the guards.

## What counts

- A credential, a private number or a private path reaching the tree or the
  site: a class the publication gate (`tools/prepublish.py`) does not catch.
- A guard passed without the evidence it demands: a way to reach
  `MEASURED -> FORWARD` that the null control (`make null`) should refuse, or
  `APPROVED -> LIVE` by any path but the human signature (R1).
- A Register whose hash chain can be broken or rewritten without the history
  showing it, or an `engine_sha` stamp that can be forged.
- A dependency advisory in what `pyproject.toml` installs.

## How to report

Use GitHub's private vulnerability reporting for this repository (the Security
tab, *Report a vulnerability*), so the report stays private until it is fixed.
Anything that is not sensitive, such as a false refusal or a page that misreads
a record, is an ordinary issue.

One person maintains this repository. Reports are read, acknowledged and
answered in the order they arrive; there is no service-level promise.

## Supported

The `main` branch only. Every commit on it passes `make check` in CI. A verdict
names the commit it was measured on (`engine_sha`); those commits belong to the
lab's private history, since the public repository begins at the publication
snapshot. From that snapshot on, history is never rewritten: a fix is a new
commit and never an edit of the record.
