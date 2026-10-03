# Halts are durable, and clear on their own terms

A halt that lives only in memory means nothing across a crash — and crashes
correlate with the conditions that halt you, so the protection would vanish
exactly when it had just worked. **Halt is durable state: a restart never
resumes trading on its own.**

Resuming requires two things, not one. **The halting condition must have
cleared on its own terms, and a human must explicitly act**, with both
recorded.

| halt cause | clears when |
|---|---|
| kill-file present | the file is removed |
| max daily loss breached | the next session — resuming same-day would defeat the limit |
| broker/internal divergence | reconciliation returns clean |
| portfolio envelope breached (ADR-0019) | the envelope is back within limits, the correlation/root-cause review is recorded, and a human records which still-approved Strategies may resume; the breach retires none |
| human halt | the human says so |

This is deliberately lighter than an approval signature: resuming from a halt
returns to a state that was already approved. Resuming from **retirement** is
different and needs a new Hypothesis (ADR-0010).

## Considered options

- **In-memory halt, restart resumes per config.** Self-heals from transient
  faults with nobody woken, and discards the protection at the moment it
  matters.
- **Durable halt with a declared expiry.** Allows unattended recovery and
  tunes safety against availability. The expiry is a guess about a condition
  nobody has re-checked, and a daily-loss halt clearing on a timer defeats
  the limit that set it.

## Consequences

Recovery from a transient fault always requires a person, so unattended
operation has a hard floor. That floor is the point.
