# Occams — project context

**State:** published and public (`MaverickHQ/occams-test-lab`, pages at
`https://maverickhq.github.io/occams-test-lab/`). Three programmes are run,
stopped by record and concluded; M0–M15 are closed. **M16 is open**: an
external review of the inference, verified by rerun, fixed in three releases —
1.0.1 (released), 1.1.0, 2.0.0. `TASKS-v4.md` holds every row, its *Rules of
the run*, and the dated status log: read the last entries before any change.
This file's long form, as it stood before M16.12, is `git show b838479:CLAUDE.md`.

## Read order

1. `README.md`, then `docs/INTEGRITY.md`, `docs/RUNBOOK.md`, `docs/LAB-CONCLUSION.md`
2. `REQUIREMENTS-v4.md` (normative), `DESIGN-v4.md`, `TASKS-v4.md` (sequence, gates, log)
3. `CONTEXT.md` — canonical language; use its words
4. `docs/adr/0001-0055` (0052 and 0053 unused) — decisions and rejected alternatives
5. `docs/reviews/` — the 2026-10-03 inference review and its verification

Precedence: ADR amendment, then requirements, design, task evidence. A
contradiction between them is a release blocker.

## Naming

The project is **`occams`**. `occums` was a typo. `MaverickHQ/occams-trader`
redirects to the public `prop-challenge-lab`: **never set it as a remote**.
Remotes here: `origin` (public) and `history` (private, archived, read-only).

## Standing rules

- **Three sets of numbers are the author's alone: money, alpha, the lab
  falsifier** — and any floor, seed or new required number. Never pick,
  recommend or default one; a default is a recommendation.
- **`occams.toml` and `configs/` are gitignored and never committed.** No
  credentials, account identifiers or broker terms in the repository. Keys
  live in the macOS Keychain and are never printed.
- **Append, never overwrite.** No closed Register gains or loses a record;
  corrections supersede. Register before measuring; state the floor first.
- **The author's acts are never an agent's:** `register --yes`,
  `programme stop --yes`, adopting a conclusion, `APPROVED -> LIVE`.
- **A Draft is not a plan** — no standing, no alpha, until a human registers it.
- **`occams/core/` is vendored and never edited** (`make provenance`).
- **Other repositories are read-only references.** Never modify or push to them.
- **History is never rewritten.** No force-push, no moved or deleted tag.
- **The private history never goes to `origin`:** no `git push --all`, no
  `--mirror`, no old tag. A pre-push hook refuses refs from the old root.
- **Merge in this checkout and push; never merge on GitHub's side.**
- **The publication gate binds every commit:** `make prepublish`,
  `make prepublish-all`.
- **Dirty or unknown code does not measure** (ADR-0055): commit, then run.

## Every change ends with the record

1. `PATH="$PWD/.venv/bin:$PATH" make check` — tests, lint, credential scan,
   provenance, publication gate, `make null` (must refuse), `make signal`
   (must accept). If either control changes its answer, stop and fix the guards.
2. Commit, push, and see both CI jobs green: `check` and `setup`.
3. Append the dated S1, S3, S10 entry to the status log in `TASKS-v4.md`.
4. After a change under `docs/` or to a Pages action: `gh workflow run pages.yml`.

The virtual environment has no `pip`: use
`uv pip install --python .venv/bin/python -e ".[dev]"`. A test that must fail
before its fix is committed as a strict expected failure naming the row that
fixes it. `make calibrate` runs the size table; it is never part of `make check`.

## Where things are

| What | Where |
|---|---|
| Guards, one per transition | `occams/guards/` |
| The measurement contract | `occams/measurement.py` |
| Engines, probes, shared inference | `occams/engine/`, `occams/inference.py` |
| Engine identity | `occams/identity.py` |
| Registers, pinned heads | `register/`, `register/HEADS.toml` |
| Size table | `occams/calibrate.py`, `tests/test_apparatus_size.py` |
| Pages | `docs/` (`make console`, `make programme`, `make site`) |
