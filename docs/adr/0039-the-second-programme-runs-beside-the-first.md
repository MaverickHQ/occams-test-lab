---
status: decided in shape 2026-09-12 (the author opened M12 and M12.0); the floor, falsifier count and alpha split for programme 2 are the author's numbers and are not in this ADR
---

# The second programme runs beside the first, in the same repository, on its own Register

The first programme's lab closed on 2026-09-12 when its falsifier fired
(ADR-0033): three mechanism verdicts, all null, on a floor and a count
declared before the first bar was read. ADR-0033 says what closing is —
terminal, a publication, not repaired by new data — and the Register
enforces it: nothing registers after `LabClosed` (#33).

The author then asked for what the first programme did not do: *a full
set of strategies tested across multiple histories, depth and breadth, in
batch, with the hypotheses and results written and logged legibly.* That
is a different premise from the one that closed, and ADR-0033 already
names its form: **a new question is a new programme.**

## Decision

**Programme 2 runs in this repository beside programme 1**, and never in
its Register.

- **Its own Register and queue**: `register/programme-2.jsonl` and
  `register/programme-2-queue.jsonl`. The first programme's Register is
  never written again; the console renders both, the first marked closed.
- **Its own configuration**: `configs/programme-2.toml`, gitignored like
  every configuration. It carries the author's floor convention, falsifier
  count and alpha split for this programme, declared after
  `python -m occams whatif --archive archive --register …` has shown two
  tables the first programme lacked: **the falsifier arithmetic** —
  P(the first N mechanism verdicts are all null) at a range of base rates
  of true edges, with the declared count marked — and **universe
  affordability** — the trades each universe affords on the measurement
  partition after the design effect at its own same-day ρ, and the largest
  floor that count can detect at each sweep size. The numbers stay the
  author's; the tables say what they buy. A count that closes the lab
  before the base rate can show is a test of *edges are common*, not of
  *an edge exists* — that is what programme 1's count of three was, and it
  is written here so it is not chosen twice by accident.
- **Its own frozen calendar** at its first act (ADR-0038), per universe.
- **The same apparatus, unchanged**: the spec, the engines, the guards,
  the accountant, the loop, the console. Every command takes `--register`
  and `--config`, so the two programmes share code and nothing else.
- **Breadth by survey at zero alpha, depth by registration with alpha**
  (M12): a survey reads the definition partition only and is a Register
  record; registration is the author's `--yes` naming the ids; the four
  checks and their evidence decide on the measurement partition; the cells
  screened are counted beside every question registered from them (N6).

## Consequences

- `whatif` gains `close_probability`, `universe_rho`, `affordability` and
  the two tables; `--archive` and `--register` flags.
- `question` and `loop` gain `--config`; the console's `--register`
  repeats; `make console` renders both Registers.
- The first programme's conclusion (`docs/PROGRAMME-CONCLUSION.md`) stays
  a draft until programme 2 has run, and is then joined by programme 2's
  own, written after the search and not before (M12.8).
- M12.1 (universes as records), M12.2 (the grid), M12.3–M12.7 follow;
  none registers anything.

## Considered options

- **Reopen programme 1 with a larger falsifier count.** Rejected: a count
  raised after three verdicts is a count chosen with knowledge of them,
  which is the thing every gate in the lab exists to prevent; and ADR-0033
  says terminal.
- **A new repository.** Rejected: the apparatus, the archive, the rights
  records and the ADRs are the accumulated value; a second Register is one
  file and keeps the two records distinguishable by construction.
- **One Register, two programmes.** Rejected: `LabClosed` is a terminal
  record for its Register, and the falsifier count is evaluated over that
  Register's verdicts; mixing programmes would either bypass the closure
  or count the first programme's nulls against the second.
