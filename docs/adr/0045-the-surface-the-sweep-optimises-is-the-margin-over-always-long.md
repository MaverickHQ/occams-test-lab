---
status: decided 2026-09-19 — drafted 2026-09-18 for the author's reading of Q2-001 (#19, #24) and adopted by the author the next day; built: `Cell.baseline_ev` and `baseline_by_group`, `Measurement.surface` and a winner by margin, the plateau and leave-one-out on the margin, both real engines running always-long per cell and the synthetic engine carrying its law's expectation, the resolved record naming its surface, `prepare` naming the margin winner on the definition partition; amends ADR-0036's choice of winner and DESIGN §3's objective; binds from the next registration; Q2-001 not re-judged (M12.13 closed)
---

# The surface the sweep optimises is the margin over always-long

DESIGN §3 says the surface a registered sweep optimises is **EV in net R**:
the winner cell is the highest EV (`Measurement.winner`, ADR-0036), the
plateau is judged on EV around it, and the floor, beats-null and — since
ADR-0043 — beats-always-long are then asked of that winner. The survey
(M12.3, M12.4) ranks the same cells by a different statistic: their
**margin over always-long at the same geometry and gate**, the number its
trust tiers are built on and the number its readiness table reports.

Q2-001 shows what that disagreement costs. Its family's sweep was hold ×
stop on the S&P 100 inside the up regime. The winner by EV was **hold 20,
stop 2 %**, the longest hold in the sweep — the geometry at which
always-long in the up regime of 2003–2019 pays most, +0.214 net R per
trade. The entry's EV there was +0.213. The verdict (#19) chose the cell
where the passive alternative is largest and then, under four checks,
could not see that the entry added nothing to it; the shrinkage record
(#24) could. The screen had ranked the same family by its margin and put
the hold-5 cell first, where always-long paid +0.017 on the definition
partition.

ADR-0043 refuses such a winner from the next registration. It does not
change how the winner is chosen. Under five checks a sweep like Q2-001's
would be refused rather than mis-supported — a null verdict on a family
whose hold-5 cell might have passed. A rule that picks the cell most
likely to fail the fifth check, then fails it, spends alpha to learn what
the choice of winner threw away.

## Decision (adopted 2026-09-19)

1. **The winner is the cell with the largest margin over always-long at
   its own geometry and gate.** `Measurement` carries, for every cell, the
   always-long EV at that cell's geometry (`baseline_ev` per cell, the
   probe the survey's `baseline_spec` and the fifth check already run);
   `Measurement.winner` maximises `cell.ev − cell.baseline_ev`, ties to the
   lowest indices as now. The screen and the verdict then rank by the same
   statistic, and the shrinkage record compares like with like.
2. **The plateau is judged on the margin surface.** The neighbourhood's
   median margin within `plateau_slack` of the winner's margin: a region of
   entry contribution, not a region of drift.
3. **The floor, beats-null and beats-always-long are unchanged** and asked
   of the winner so chosen: the floor on its absolute EV and frequency,
   since the money is earned in net R, not in margin; beats-null against
   the coin-flip null; beats-always-long against the Monte Carlo of
   always-long at the winner's geometry, which is now also the cell where
   that test is most likely to pass if the entry is real.
4. **Leave-one-out is asked on the margin too**: the pooled margin with
   each name held out, so a margin carried by one name is refused the way
   a pooled EV carried by one name is.
5. **Shown passable before alpha moves.** `question prepare` shows the
   sweep's cells with EV, always-long and margin on the definition
   partition and names the cell that would win by margin; from a survey
   that is the screen's own ranking.
6. **From the next registration, never backwards.** Q2-001 stands as
   recorded (ADR-0036: one-time; M6.2). A verdict records which surface
   chose its winner (`surface` on the resolved record: `ev` for every
   verdict so far, `margin` from adoption).

## Consequences

- `Measurement.Cell` gains `baseline_ev: float | None`; both real engines
  run the always-long probe per cell (k probes, each cheaper than the
  cell's own run); the synthetic engine draws it under no drift, so the
  controls still hold: a coin flip's margin is nil and refused, a planted
  effect's margin is the planted size and accepted (S3, S10 — or the
  change does not land).
- `plateau.check` and `leave_one_out.check` read margins; `clears_floor`,
  `beats_null` and `beats_always_long` are untouched. The survey runner's
  gate readiness already requires a positive margin; `survey candidates`
  already ranks by it.
- The engine code hash moves; grid-001's cells are not recomputed.
- The Shrinkage record (M12.6) keeps its fields: the survey cell is the
  screen's margin winner and the verdict's winner is now chosen the same
  way, so "shrinkage" measures transfer of one statistic, not the gap
  between two.
- Alpha is untouched: a rule is not a cost. A question registered under
  this rule carries the same k and the same charge.

## Considered options

- **Keep the winner by EV and let the fifth check refuse** (the status
  quo since ADR-0043). Rejected in this draft: it picks the cell the
  fifth check is most likely to fail and then fails it, and it spends the
  question's whole alpha to learn nothing about the cells the screen
  preferred. Kept as the author's alternative: it is the rule four
  verdicts were reached under, and it is simpler.
- **Ask the fifth check of every cell and take the best that passes.**
  Rejected: a search over cells for one that passes a significance test
  is the multiple-comparison problem the Bonferroni correction exists to
  refuse; the winner must be chosen by a statistic, not by a pass.
- **Rank by margin at registration only, then measure by EV.** Rejected:
  it moves the disagreement from the winner to the plateau, and the
  plateau on EV around a margin winner is still a region of drift.
- **Change the floor to a margin floor.** Rejected: the floor is absolute
  EV for the money's sake (M0.15) and is the author's declaration; it
  should not double as an attribution test. The fifth check is that test.
