---
status: amends ADR-0006
---

# The forward period runs before approval, not after

Two documents disagree, and the project's own rule is that a contradiction of
this kind is a release blocker rather than a precedence question.

| source | claim |
|---|---|
| ADR-0006, and the `CONTEXT.md` glossary entry | the forward period is wall-clock time **"from approval onward"** |
| The Strategy state machine, D22, ADR-0023 | `MEASURED -> FORWARD -> APPROVED`: forward runs **before** approval and can refuse it |

**ADR-0023 is operative.** Its window resolves three ways and two of them are
refusals. A refusal issued *after* approval is incoherent: the Strategy would
already be `LIVE` with real money against it, and the falsification window
would have no power to stop anything. The entire purpose of ADR-0014 — that
forward testing falsifies — depends on it preceding the gate.

**The forward period is wall-clock time from entry into `FORWARD`**: after
the single reserve look, before approval, before any signature.

**A second correction follows from the first.** ADR-0006 says price history
"is split four ways" and that "split percentages live in configuration". The
fourth is not price history and has no percentage — it is future time, and it
is declared as (minimum trades, maximum duration). **Three configured splits
partition the archive; the forward window is not one of them.** Listing it
alongside the other three is what invites reading it as held-out history,
which is the misunderstanding this ADR exists to close.

## Considered options

- **Take "from approval onward" as operative and move `FORWARD` after
  `APPROVED`.** Internally consistent with ADR-0006 as written, and it
  destroys ADR-0014 and ADR-0023 entirely: the stage could no longer refuse,
  and real money would be committed before the only genuinely unseen data had
  been seen.
- **Keep both readings and let context decide.** The deferral the working
  rules forbid, and it does not survive contact with the config schema: there
  are either four split percentages or three, and code has to pick.

## Consequences

ADR-0006 is marked amended. The `CONTEXT.md` **Forward period** entry is
corrected in place with a dated note — a glossary carrying a definition known
to be wrong is worse than no glossary.

**D11 and M4.6 change from four configured partitions to three.** Definition,
measurement and reserve are percentages over the archive. The forward window
is a pair in wall-clock time and carries no percentage.

The ordering is now explicit end to end: measure, take the one reserve look,
run the forward window in real time, then approve and sign. Nothing about
alpha, the sealed reserve or the four refusals changes.
