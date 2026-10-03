---
status: decided 2026-09-20 — the author opened the third programme ("open a third programme"); the floor, falsifier count, alpha split and partition split for programme 3 are the author's numbers and are not in this ADR; what carries over from programme 2 is named here, and what changes
---

# The third programme asks whether a margin the screen finds transfers

Programme 2 ran and stopped on the author's record (#36) with two verdicts
and one lesson in two halves. Q2-001, its winner chosen by EV, cleared the
floor on the geometry where being long in the up regime paid the same and
the entry added nothing (#24, margin −0.001). Q2-002, its winner chosen by
margin under ADR-0045, beat always-long at the corrected alpha and missed
the floor (#33, #35). The screen had ranked both families by their margin
over always-long on the definition partition; the readiness pass of
2026-09-18 showed every one of the twenty candidates passing the fifth
check there with a positive margin in every era, the one that lost its
whole margin among them. Programme 2's conclusion (adopted 2026-09-20)
says what that leaves open: *the definition partition's eras give no
warning; whether a margin the screen finds transfers is a question the
second programme could not ask cleanly, because its screen and its verdict
ranked by different statistics until its last question.*

That is the third programme's question, and ADR-0033's rule applies as it
did to the second: a new question is a new programme.

## Decision (the author's, 2026-09-20)

**Programme 3 runs in this repository beside the first two, and never in
their Registers.**

- **Its own Register and queue**: `register/programme-3.jsonl` and
  `register/programme-3-queue.jsonl`. Programme 2's Register ended at the
  author's stop and is never written again; the console and the programme
  page render all three.
- **Its own configuration**: `configs/programme-3.toml`, gitignored. It
  carries the author's floor convention, falsifier count, alpha split and
  partition split for this programme, declared after `python -m occams
  whatif configs/programme-3.toml --archive archive --register
  register/programme-3.jsonl` has shown the falsifier arithmetic and the
  universe affordability table. Nothing in this ADR proposes a value, and
  programme 2's values are not a default: the author copies them or
  declares others, and either is a recorded act (M13.0).
- **The same four universes, re-declared as records in the new Register**
  from programme 2's latest record under each name — members, rule and
  bias unchanged, the flat bars named — unless and until the author
  supersedes one. Each is frozen on its own calendar at the programme's
  first act after the configuration exists (ADR-0038).
- **A grid that supersedes grid-001**: `surveys/grid-002.toml`, the same
  closed enum on the corrected engine — the resting limit fills at the
  open (ADR-0040) and the fill audit is exhaustive (ADR-0041), so
  `breakout_low` is measurable for the first time — with the same
  geometry; a grid is never edited, and this one names what it supersedes.
- **The apparatus as it stands, unchanged**: nine entry kinds by ADR, the
  survey at zero alpha on the definition partition, gate readiness under
  the fifth check with the margin in every era (`survey candidates
  --fifth-check`), registration by the author's `--yes`, five checks on
  the measurement partition, the winner and the plateau and leave-one-out
  on the margin over always-long (ADR-0043, ADR-0045), the shrinkage and
  the eras recorded after every verdict, a stop that is a record and a
  conclusion written from the Register after it (M12.8). Every command
  takes `--register` and `--config`; the programmes share code and nothing
  else.
- **What the third programme reads that the second could not:** two
  measured priors. The readiness table and the conclusion cite every
  `Shrinkage` record beside the screen; programme 3's tools read programme
  2's Register for them, read-only, so that the one statistic the screen
  and the verdict now share is compared with what it did the last two
  times.

## Consequences

- The M13 phase in `TASKS-v4.md`, mirroring M12's rows with the machinery
  already built: declared (M13.0, the author's numbers), universes and
  calendars (M13.1), the grid (M13.2), the survey on the burst (M13.3),
  the page (M13.4), candidates and registration (M13.5), the loop (M13.6),
  the programme page (M13.7), the stop and the conclusion (M13.8).
- `make console` and `make programme` take the third Register; the
  prepublish check covers it as it covers the others.
- Programme 3's first spend of money is the burst that computes its
  survey, priced by the last one at about the cost of a coffee; its first
  spend of alpha is the author's `--yes`.
- Programme 2's Strategy at `FORWARD` (#22) is not carried over: ADR-0044
  deferred the host, and a Strategy in one programme's Register is not a
  question in another's.

## Considered options

- **Reopen programme 2 with the unspent 0.05 on each axis.** Rejected:
  its Register ended at the author's stop, terminal by construction
  (M12.8), and 0.05 buys no family the survey holds.
- **A grid two inside programme 2's Register.** Rejected for the same
  reason, and because the question changed: the second programme asked
  what its grid held; the third asks whether what a screen finds
  transfers, and needs its own falsifier declared for that.
- **A programme that trades.** Rejected as this programme: ADR-0044
  deferred the execution host outside the lab, and M5.0 closed by
  decision with the cost basis bounded; a programme that trades begins
  with the host and a measured spread, and this one begins with neither.
- **The same four universes, or new ones.** The four are re-declared so
  the priors from programme 2 compare like with like; the author may add
  a universe by declaration at any time, and M12.1e keeps the lab above
  large caps.
