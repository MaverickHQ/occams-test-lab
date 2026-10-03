---
status: decided 2026-10-03 — adopted by the author's instruction to run M16 ("run M16. Add including M16.21") after the inference review of 2026-10-03 was verified by rerun (`TASKS-v4.md` M16.0); built by M16.16
---

# A plateau is judged in standard errors, without the winner in its own median

`guards/plateau.py` asks that the winner's score exceed the median of its
neighbourhood by no more than `plateau_slack`. Two things loosen it. The
neighbourhood includes the winner, so with four cells the winner is one of
the two middle values and pulls the median toward itself. And the slack is
absolute — 0.10 R for every question so far — whatever the surface's scale
and whatever the winner's own sampling error.

## Decision (adopted 2026-10-03)

1. **The winner is not in its own median.** The median is taken over the
   neighbours that traded, the winner excluded. The neighbourhood's size is
   still counted with the winner in it, as `plateau_cells` was declared.
2. **A slack in standard errors is declared with the question.** A new
   registration declares `plateau_slack_se`; the check refuses when the
   winner's score exceeds its neighbours' median by more than that many of
   the winner's standard errors (ADR-0048's). It has no default.
3. **The absolute slack stays.** A question is refused if either slack is
   exceeded; the two together can only refuse more.
4. **From the next registration.** A question registered before this
   carries no `plateau_slack_se`; for it the standard-error half is absent
   and the gap in standard errors is recorded as evidence, not judged.

## Consequences

- A lone spike that the old median hid — the winner 0.12 above its
  neighbours' median with a slack of 0.10 — is refused.
- The check's evidence gains the neighbours' median, the gap, and the gap in
  standard errors.

## Considered options

- **Replace the absolute slack.** Rejected: on a surface whose errors are
  tiny, a slack in standard errors alone would refuse differences that do
  not matter in R.
- **A fixed number of standard errors.** Rejected: it is a number, and the
  question's author declares its gates.
