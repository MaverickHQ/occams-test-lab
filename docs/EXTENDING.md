# Extending the lab — a new entry kind, a new grid, your own bars

Three things a stranger may want to do, in the order the lab lets them.
Nothing here spends alpha or writes a Register; a kind is added by ADR,
never discovered (ADR-0037).

## 1. Your own bars

```bash
python -m occams ingest AAA BBB --csv bars/ --source-id my-bars --rights-provenance "my broker's export, 2026-09-26; mine to keep and analyse" --permit private_retention,internal_reproduction --start 2015-01-02 --end 2026-09-10 --archive archive
```

One CSV per symbol under the directory, columns `date, open, high, low,
close, volume` and optionally `dividend` and `split`. The rights are
yours to declare: what you permit is recorded in the archive under
`rights/` with the date, everything else is recorded forbidden, and
`private_retention` must be permitted or nothing is archived. No vendor,
no key, no budget charge. From there the path is the same as for any
series: a universe record, a frozen calendar, a classifier, a grid.

## 2. A grid of your own

Copy `surveys/grid-template.toml` to `surveys/grid-NNN.toml`, name it,
date it, and name what it supersedes if anything. Every universe it names
must be a `UniverseDeclared` record in the Register it loads against;
every mechanism kind must be on the closed enum with a sentence and an
auditor family. Then:

```bash
python -m occams survey show surveys/grid-NNN.toml --register register/programme-N.jsonl
```

prints the grid's hash and its cell count before anything runs. A grid is
never edited after that: a change is a new grid naming the old one.

## 3. A new entry kind — by ADR

The entry enum is closed (`occams/spec/spec.py`, `EntryKind`); the nine
kinds it holds were each added by a decision that names the mechanism, the
family it belongs to and why the existing kinds cannot state it. The path,
in order, and what refuses you at each step if you skip it:

1. **The ADR.** `docs/adr/NNNN-<kind>.md`: the mechanism in one sentence,
   the auditor family, the rejected alternatives. Without it the kind has
   no standing — the task list's rule, not the code's.
2. **The enum.** Add the member to `EntryKind` with a comment stating the
   signal in one line.
3. **The sentence.** `occams/proposers/price.py`, `MECHANISM_SENTENCES`:
   the hypothesis text with its parameters, its *if true* and *if false*.
   A kind without a sentence cannot be surveyed: `Cell.hypothesis` has
   nothing to fill.
4. **The signal.** The engines compute the entry (`occams/engine/`): where
   the level rests or when a market entry fires, for the day-boxed and
   the position-boxed simulators.
5. **The auditor family.** `occams/costs/auditors.py`, `FAMILY_OF`: which
   set of obtainability auditors judges its fills. **This is the step the
   code enforces:** a kind that belongs to no family is refused by name
   at compile — `UnauditedFamily` — and every survey cell and question
   using it refuses with it. A test keeps every member of the enum in
   `FAMILY_OF`.
6. **The grid.** A `[[mechanisms]]` entry with the kind, its order and its
   parameter points. `survey show` loads it or refuses it by name.
7. **The tests.** The controls must still refuse the coin flip and accept
   the planted edge (`make null`, `make signal`); the new kind gets a
   signal test of its own.

What you cannot do: add a kind without an ADR, add a parameter that is
not a number, or give the kind a side other than the grid's — the
templates are long-only, and a short side is a new template by ADR.
