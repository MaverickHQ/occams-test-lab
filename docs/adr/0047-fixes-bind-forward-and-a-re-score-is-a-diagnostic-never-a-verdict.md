---
status: decided 2026-10-03 — adopted by the author's instruction to run M16 ("run M16. Add including M16.21") after the inference review of 2026-10-03 was verified by rerun (`TASKS-v4.md` M16.0); governs M16.1–M16.21
---

# Fixes bind forward, and a re-score is a diagnostic, never a verdict

An external review of the published lab at `2e86d58` found the guards
looser than they claim: the position-boxed null resampled at the pool's size
and not the winner's, both nulls blind to trades that share a date, a fifth
check a coin flip can pass, a floor judged on a point estimate, a plateau
that keeps the winner in its own median, a Register whose chain carries no
key, an engine identified by a hand-kept list. Each was verified by rerun
before this was written (M16.0). Every one of them errs toward a false
positive. So the four null verdicts are robust, and the one supported
verdict — Q2-001, beside which the lab had already recorded that the entry
added nothing — is the soft spot.

The lab's three programmes are stopped by record and concluded. Their
verdicts were reached under the rules then in force and are sealed. This
decision says how a lab in that state takes a correction.

## Decision (adopted 2026-10-03)

1. **A fix binds forward, by ADR.** Each change to what a guard tests, to
   what the Register attests or to how the engine is identified is adopted
   by an ADR and binds from the next registration, as ADR-0043 and ADR-0045
   did. Nothing is re-judged.
2. **A sealed verdict is never edited.** No line of a programme Register is
   rewritten; no stopped Register gains a record
   (`occams/stopping.py`); a resolved outcome keeps its outcome.
3. **A re-score is a diagnostic, in its own store.** `register/diagnostics.jsonl`
   is a hash-chained store beside the Registers with one record kind,
   `Rescored`: the record it annotates by its chain sha, the ADRs applied,
   the engine's content hash, the seed, whether the original numbers were
   first recreated exactly, the checks and refusals under the named rules,
   and every number, passing or failing. It never counts toward the
   falsifier, never spends or accrues alpha, never changes a balance. The
   pages show it beside the verdict it annotates and never in its place.
4. **Reproduce first.** A question is re-scored only after its recorded
   numbers are recreated exactly from its stamped source and the licensed
   archive. One that cannot be is recorded `reproduced=False` with the
   reason and is not re-scored.
5. **Conservative before non-conservative.** A fix that can only turn a
   pass into a refusal lands, and is re-scored, before any fix that can move
   a number either way; a null is never revived on a guard set known to be
   too loose.
6. **The apparatus proves itself before and after.** `make null` refuses and
   `make signal` accepts on both engines; a size-and-power table measures
   each guard's false-positive rate in isolation over at least 200 seeds; a
   fix that leaves a measured size above alpha plus 2.33 standard errors is
   not done.
7. **A rule that needs a number waits for the author.** No fix introduces a
   default for a number that is the author's; a re-score judges only rules
   whose numbers the registered question already carries and reports the
   rest as statistics.

The review reserves ADR numbers 0047 to 0060. This lab adopts 0047 to 0051,
0054 and 0055. Numbers 0052, 0053 and 0056 to 0059 — survey-wide inference,
structural overlap and a lab-wide ceiling, point-in-time universes, measured
costs, the calibration gate, an entry registry — are left unused here: no
programme will register, survey or trade in this lab again, and the
successor lab closes them by construction. They are named in the README's
known limitations.

## Consequences

- The record gains a second, smaller chain. The three programme Registers'
  heads do not move, and M16.4 pins them so that is checkable.
- Q2-001 stays *supported, as reached*. What the corrected rules would have
  said is written beside it, with its numbers.
- A reader can tell at a glance which rules a number was produced under:
  every `Rescored` names its full ADR set.

## Considered options

- **Edit the verdicts.** Rejected: the Register's whole claim is that what
  was decided is what is shown (ADR-0036).
- **Annotate inside the closed Registers.** Rejected: a stopped Register
  gains no record, and an annotation is a record.
- **Fix forward and leave the record unannotated.** Rejected: the lab would
  then know something about its one positive verdict that its pages do not
  say.
- **Adopt all thirteen proposed ADRs here.** Rejected: half of them bind
  only a lab that still registers, surveys or trades.
