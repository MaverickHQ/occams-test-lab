---
status: decided 2026-10-03 — adopted by the author's instruction to run M16 ("run M16. Add including M16.21") after the inference review of 2026-10-03 was verified by rerun (`TASKS-v4.md` M16.0); built by M16.4 (the pin) and M16.5 (the attestation)
---

# The Register's heads are pinned, and attested outside the repository

A Register line's digest is `sha256(prev | seq | payload)`, with no key.
That makes a rewrite *of one line* detectable. It does not make a rewrite
*of the whole file* detectable: change Q2-002's outcome, recompute every
digest from genesis, and `verify()` returns 37 as before; cut the file to
its first twenty lines and it returns 20. Both were done to a copy and both
verified (M16.0). What stood behind the chain was the repository's history,
which showed each registration committed before its measurement — and the
public repository carries no history from before publication. The heads
appear only in prose.

## Decision (adopted 2026-10-03)

1. **The heads are pinned in the tree.** `register/HEADS.toml` holds, for
   every store, its path, its record count and its head sha. A test and the
   publication check fail on any mismatch, so a rewrite or a truncation of a
   committed store fails the build unless the pin is rewritten with it.
2. **The pin is attested by a third party, without a key.** A workflow
   attests `register/HEADS.toml` whenever it changes: a signed statement,
   bound to this repository and that workflow, recorded in a public
   transparency log that dates it. Anyone can verify it; no private key
   exists to be held, lost or copied.
3. **A pin is moved only by the command that appends.** A store's head
   changes only when a record is appended, and the pin is rewritten by a
   named command after that append, never by hand.
4. **What this does not claim.** The attestation dates the **pin**, not the
   past. That each registration preceded its measurement is attested by the
   private history, not by this mechanism.

## Consequences

- From the first attestation on, a rewrite of a committed store needs a
  rewrite of the pin, and a rewrite of the pin leaves a dated, public trace.
- A signature by a key of the author's own, and an anchor in another
  timestamping service, remain available as the author's acts; neither is
  required.

## Considered options

- **A signature by the author's key and a separate timestamp anchor**, as
  the review proposes. Not rejected: left to the author. A key is theirs to
  create and hold, and the run that builds this must not need one.
- **A keyed digest on every line.** Rejected: it proves integrity only to
  whoever holds the key.
- **Republishing the history.** Rejected by the author's decision of
  2026-10-03 (`docs/PUBLICATION.md`).
