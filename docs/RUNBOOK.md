# Occams — runbook

By situation, not by command. Each entry says what to do, what record it
leaves and what check proves it. No number that is the author's appears
here, no credential, no bucket name; `tools/prepublish.py` scans this file
with the pages (M14.2). The lab's vocabulary is `CONTEXT.md`'s.

**Three things never run without the author, whatever the situation:**
the `--yes` at registration (`question register`), `programme stop … --yes`,
and `APPROVED -> LIVE` (R1.1, R1.2). An agent prepares, measures, renders and
drafts; it never registers, stops, adopts or publishes.

Every command below runs from the repository root with the project's
interpreter on the path:

```bash
export PATH="$PWD/.venv/bin:$PATH"
```

---

## A burst that dies, stalls or never reports

The survey box is a spot instance in an auto scaling group of one with an
S3 checkpoint; every finished cell is an atomic file and a replacement
instance resumes from the checkpoint (`tools/aws/burst.sh`, M12.3b).
Programme N's run sets `CONFIG=configs/programme-N.toml` and
`REGISTER=register/programme-N.jsonl` in the environment of every call.
`start` uploads the manifest and only the bars the grid's universes and
the classifier's index need — `python -m occams survey inputs GRID
--register R --archive archive` lists them (M14.7).

1. **Where is it?** `tools/aws/burst.sh status GRID SEED` — the progress
   record from S3 and the group's instances. `watch` prints one line per
   change and exits on done.
2. **Booted but never reported?** `tools/aws/burst.sh console` — the
   instance's console log, filtered. A box that cannot read the config
   parameter or the bundle says so there.
3. **Interrupted?** Do nothing: the group replaces the instance and the
   replacement resumes. If the group holds zero instances and the job is
   not done, `start GRID SEED` again — the checkpoint is the resume point,
   nothing is recomputed.
4. **Done.** `pull GRID SEED` syncs the checkpoint into
   `archive/surveys/<job>-<type>/`; `record GRID SEED DIR` verifies every
   file against the index and appends `SurveyRecorded` **here** — the box
   never records. `compare DIR_A DIR_B` proves a run here matches a run
   there at trade level.
5. **Always, the same day:** `tools/aws/burst.sh teardown --all`, then
   verify: no group, no template, no parameter, no role, no bucket. The
   status log records the teardown with the run.

**Record left:** `SurveyRecorded` (results hash, cell count, seed) in the
programme's Register. **Check:** `python -m occams survey show GRID
--register R` prints the record; `make prepublish` passes on the page.

## A question refused at measurement

The loop refused a registered question at `REGISTERED -> MEASURED`: the
winning cell holds fewer trades than the power plan requires, or the sweep
that ran is not the sweep declared (M8.2, `guards/measure.py`). Q3-001,
2026-09-20, is the precedent.

- The refusal is a `RefusalRecorded` with its evidence; the question stays
  `REGISTERED` in the queue; **its alpha stays spent** as the ledger is
  built; there is no verdict and nothing from the measurement partition is
  read beyond the refusal's count.
- **Running the loop again repeats the refusal.** Do not.
- Rebuild the pages so the state is visible: `make console` and
  `make programme`; the question shows *registered, refused at
  measurement, unresolved* (M14.5).
- What follows is the author's: a superseding registration at a floor the
  sweep's thinnest cell affords (`question prepare` now prints that cell
  beside the template's signals, M14.3's neighbour `bound_by_thinnest_cell`),
  a re-declaration of the numbers, or `programme stop`. Recommend none.

**Record left:** `RefusalRecorded` (`REGISTERED->MEASURED`). **Check:** the
console card and the programme table carry the state; the ledger's
remaining alpha is what `python -m occams whatif CONFIG --register R` shows.

## The null control passes, or the signal control fails

`make null` must refuse and `make signal` must accept (S3, S10). If either
changes, **stop everything else**: the guards have drifted. Read the named
refusal, fix the guard, prove it with both controls on both engines
(`--engine=day_boxed`), then `make check`. Nothing registers or measures
until both are green. No verdict reached while a control was wrong stands
without a superseding record.

## A red CI

S1 is CI green on a clean checkout, on the CI machine. A red run records
nothing: fix locally, `make check`, push again. Only a green run gets the
"S1, S3, S10" status-log entry with its run id, and that entry is its own
commit. A red run caused by the machine (a runner outage) is re-run, not
recorded around.

## The source changed, or a series must be re-ingested

Every series has a rights record or it is not ingested (`occams/data/rights.py`);
an unanswered right is a refusal. The Tiingo key lives in the macOS
Keychain and is substituted inline, never printed, filed or pasted:

```bash
TIINGO_API_KEY="$(security find-generic-password -s TIINGO_API_KEY -w)" python -m occams ingest SYMBOL … --start YYYY-MM-DD --end YYYY-MM-DD --archive archive
```

- Symbols are charged against the monthly budget **before** the fetch
  (`--budget`, default `archive/symbol-budget.json`); a refused symbol
  costs nothing.
- `--refresh` re-fetches a series already held; the archive is
  content-addressed, so an unchanged series is a no-op and a changed one
  is a new manifest row — nothing is overwritten.
- A symbol is not an identity: a reassigned ticker serves its new holder
  and a delisted name serves nothing (M12.1b). Survivorship stays a named
  bias on the universe record.
- After a re-ingest, `python -m occams calendar show` — no calendar moves
  without a `CalendarFrozen` record, and a partition is cut from the record,
  never from the bars.

**Record left:** a manifest row per series (`archive/manifest.jsonl`);
never a Register record. **Check:** `make provenance`; the console's
archive section reads the manifest and never the bars.

## Rotating the Tiingo key or the EDGAR contact

Both live only in the Keychain, under `TIINGO_API_KEY` and
`EDGAR_CONTACT`, and are read with `security find-generic-password -s NAME
-w` at the moment of use.

```bash
security add-generic-password -U -s TIINGO_API_KEY -a occams -w
```

The `-w` with no value prompts; nothing lands in shell history. The same
form with `-s EDGAR_CONTACT`. Nothing in the repository changes;
`make credscan` (S5) must still return nothing.

## Rebuilding the pages after any Register change

```bash
make console && make programme
```

`make survey GRID=surveys/grid-NNN.toml OUT=archive/surveys/<job>-<type>`
renders a survey page (check the target's `--register` and `--config`; pass
the programme's explicitly). `make console-offline` is the CI proof that
the plain build needs no config. Every page is one static file: no script,
no network, no money by construction; `make prepublish` is the check and
publishing itself is a recorded decision (R7).

## Reproducing a verdict

```bash
make reproduce-private QUESTION=Q-005      # exact, from the licensed archive, on a scratch Register; fails loudly without the archive
make reproduce-public                      # the pipeline on synthetic fixtures; refuses an exact-historical claim the rights forbid
```

`--at-commit` recreates the stamped commit in a worktree. The reproduction
key is `engine_code_sha`, the content hash on every record; `engine_sha` is
the commit and carries `-dirty` only when the tree was dirty before the run
began (M14.3).

## Stopping a programme and writing its conclusion

The author's act, never an agent's:

```bash
python -m occams programme stop --register register/programme-N.jsonl --config configs/programme-N.toml --kind alpha|author --reason "…" --by NAME --yes
python -m occams conclude --register register/programme-N.jsonl --out docs/PROGRAMME-N-CONCLUSION.md --config configs/programme-N.toml --archive archive
```

An alpha stop is verified against the ledger; an author's stop names its
reason; `conclude` is refused until a stopping record exists and never
overwrites. The document is a draft until the author adopts it; adoption is
a status-log entry and a commit, and the pages are rebuilt.

## Opening a programme

In order, each a record before the next: the ADR; the configuration
(gitignored, the author's numbers, `python -m occams whatif` first); the
universes (`universe declare`); the calendars (`calendar freeze
--universe`); the classifier (`classifier freeze --seed`); the grid
(`surveys/grid-NNN.toml`, committed and hashed, never edited); the survey
on the burst; `survey record`; the page; `survey candidates --fifth-check
--readiness-out … --priors-register` for each earlier programme; then the
author's `--yes`. Question ids follow the Register's name
(`programme-N.jsonl` → `QN-`).
