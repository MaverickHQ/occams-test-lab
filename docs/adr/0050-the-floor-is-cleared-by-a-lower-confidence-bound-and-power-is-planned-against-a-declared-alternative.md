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

## As built: the dispersion half (M16.16, 2026-10-04)

- **§3, the widest cell.** A question registered from a survey takes its
  plan's dispersion from the largest among its family's cells that the
  survey measured and did not refuse, and its provenance names that cell.
  `prepare` prints both numbers. On the test fixture the chosen cell
  measures 0.49 R and the family's widest 1.02 R, and a floor that was
  powered at the first is refused as underpowered at the second.
- **§4, the winner's own dispersion.** The engines put the winner's standard
  deviation, the standard error of its EV clustered by date, and its
  effective count — the count of independent trades that standard error is
  worth, never more than it holds — in the Measurement. At
  REGISTERED → MEASURED the required count is recomputed on the question's
  own formula at the winner's standard deviation and refused as
  *underpowered at the winning cell's own dispersion* when the effective
  count is below it. It reads the measurement partition and can only refuse.

## As built: the bound and the alternative (M16.21, 2026-10-04)

- **§1, the bound.** `clears_floor` refuses unless
  `winner.ev − z(1 − alpha/k) · se` is at or above the declared floor; `se`
  is the winner's standard error clustered by date, which the engine puts in
  the Measurement. A measurement with no standard error is refused by name.
  The frequency half is unchanged.
- **§2, the alternative.** `PowerPlan.alternative_ev_net_r`; a registration
  without it is refused, naming the key and no value, and so is one whose
  alternative is not above its floor; `--alternative-ev` on both
  registration commands, no default; `prepare` says *UNDECLARED*. The
  required count is `inference.one_sided_n`. The review's figure checks:
  1,446 at 1.2 R, a gap of 0.10 R, a corrected alpha of 0.01 and power 0.8.
  `python -m occams --schema` lists the four keys a registration declares —
  the floor's pair, the alternative, the plateau's slack in standard errors —
  each with its type and none with a value. `whatif` prints the count for
  four gaps beside the count under the rule before.
- **§5, the controls.** `controls.toml` declares an apparatus alternative of
  0.30 R, twice the control's floor, and the signal control plants there net
  of the spread: 732 trades a cell required, 1,000 held. Before this the
  signal planted 0.165 R before costs — 0.115 net, *under* its own floor —
  and was accepted because the best of nine cells cleared 0.15 by its point
  estimate. That acceptance was the defect.
- **§6, never backwards.** A question with no declared alternative is judged
  by its point estimate, as it was registered to, and its bound is written
  into the evidence beside it. A re-score asks for the bound by name.
- **What the size table reads.** With the true EV exactly at the floor the
  bound is cleared 0.010 of the time at a declared 0.01 and 0.065 at 0.05,
  over 200 seeds. With the true EV at the alternative and the count the plan
  asks for it is cleared 0.75 of the time against a planned 0.80, over 100
  seeds, inside tolerance. Across seeds the null control is accepted by all
  five checks 0 times in 200 on either engine; the signal control 92 times
  in 100 on the synthetic law and 100 in 100 through the day-boxed engine.
- **What it costs is real.** A survey family that was powered at its chosen
  cell and a floor told from nil is not powered at its widest cell and a
  floor to be cleared from above. That is what the consequence above says,
  measured on the fixture.
