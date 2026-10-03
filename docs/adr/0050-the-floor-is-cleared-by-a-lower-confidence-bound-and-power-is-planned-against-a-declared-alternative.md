---
status: decided 2026-10-03 — adopted by the author's instruction to run M16 ("run M16. Add including M16.21") after the inference review of 2026-10-03 was verified by rerun (`TASKS-v4.md` M16.0), the instruction naming M16.21; built by M16.16 (dispersion) and M16.21 (the bound and the alternative)
---

# The floor is cleared by a lower confidence bound, and power is planned against a declared alternative

`guards/clears_floor.py` refuses when the winner's EV is below the declared
floor. The winner is the best of k cells, so its point estimate is biased
upward, and a true effect sitting exactly at the floor passes about half the
time. The power plan (`hypothesis.py`) sizes N to tell the floor from
**zero**, two-sided: nothing is sized to show an EV **above** the floor.
The dispersion the plan uses is the survey cell's or the template's, while
the winner may be any cell of the sweep — Q2-001 planned at 2.22 R on its
hold-5 cell and won at hold 20, where its ungated sibling measures 4.09 R.

This is the one fix that changes what *supported* means, and the author
adopted it by name.

## Decision (adopted 2026-10-03)

1. **The floor is cleared by the lower confidence bound.** The check refuses
   unless `winner.ev − z(1 − alpha/k) · se` is at or above the declared
   floor, where k is the declared sweep size and `se` is the winner's
   standard error clustered by entry date with a correction across dates out
   to the hold (ADR-0048's standard error). Simultaneous bounds at alpha/k
   cover all k cells, so the bound is valid after choosing the winner. The
   frequency half of the floor is unchanged.
2. **Power is planned against a declared alternative.** A question declares,
   at registration and beside its floor, the EV it wants power **at** —
   strictly above the floor, with no default, printed by `--schema` as a key
   and never a value. Required N is one-sided:
   `ceil(((z(1 − alpha/k) + z(power)) · sigma / (alternative − floor))²)`.
   The vendored `core/power.py` is untouched; the formula lives in this
   lab's code.
3. **The plan uses the widest cell.** A question registered from a survey
   plans on the largest dispersion among its sweep's cells, naming the cell.
4. **The winner must be powered at its own dispersion.** At measurement the
   required N is recomputed with the winner's own standard deviation and its
   effective count; a winner too dispersed for its count is refused. This
   reads the measurement partition and can only refuse.
5. **The controls plant at an apparatus alternative.** `controls.toml`
   declares it — an apparatus number, never the author's — and S10 becomes
   *a planted effect at the alternative is accepted*.
6. **From the next registration, never backwards.** A question registered
   before this carries no alternative and is read as such; a re-score reports
   its bound and judges it against its recorded floor (ADR-0047).

## Consequences

- Fewer questions are affordable: at a corrected alpha of 0.01 and power
  0.8, a gap of 0.10 R between alternative and floor needs 1,446 trades at a
  dispersion of 1.2 R and 4,951 at 2.22 R. That is what *clears the floor*
  costs when it is meant.
- Q2-001's bound at the plan's dispersion is +0.151 with independent trades
  and below the floor under any clustering; the re-score records it.
- The quickstart's known answer (714) stays as the M0.15 figure, labelled as
  the rule before this one.

## Considered options

- **Keep the point estimate.** Rejected by the author's adoption: it attests
  the best of k draws, not the cell.
- **A separate winner's-curse correction.** Rejected: the simultaneous bound
  already covers selection among the k cells.
- **A default alternative.** Rejected: a default is a recommendation (R9).
