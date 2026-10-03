---
status: decided 2026-10-03 — adopted by the author's instruction to run M16 ("run M16. Add including M16.21") after the inference review of 2026-10-03 was verified by rerun (`TASKS-v4.md` M16.0); built by M16.10 (identity) and M16.17 (sources)
---

# The engine is identified by content, and a dirty tree cannot measure

Every verdict stamps the commit that measured it. Three things weaken the
stamp. The vendored `engine_sha()` appends `-dirty` when *anything* in the
working tree has changed — and the loop's own Register writes change it, so
every programme 2 verdict reads `-dirty` — and returns `unknown` on any
error; both were accepted. The content hash meant to stand in for it covers a
hand-kept list of eleven files that omits the fill model, the sizing rule,
the measurement contract and the guards, and no measured or resolved record
carries it. And the stamped commits are not in the public repository, so
nobody outside can inspect what they name.

## Decision (adopted 2026-10-03)

1. **The engine's identity is a hash of what it imports.** The content hash
   covers the transitive import closure, inside `occams/`, of the modules
   that measure: the loop, both engines, the survey runner. A change to any
   file a measurement depends on changes the hash; nothing is listed by hand.
2. **Only code can make the tree dirty.** Dirtiness is judged on the code
   paths alone, so a Register, an archive or a page written during a run
   does not mark the engine dirty.
3. **Dirty or unknown code does not measure.** A measurement or a survey
   refuses by name when the code is dirty or the commit cannot be read. The
   apparatus controls are exempt and say so.
4. **Every measured, resolved and surveyed record carries the content
   hash**, beside the commit.
5. **A stamped source is addressable without the history.** `SOURCES.toml`
   maps each stamped commit to its tree hash and its content hash; a source
   snapshot per content hash is kept beside the licensed archive, and a
   reproduction can run from a snapshot instead of a checkout. The
   snapshots are not published: those trees hold what the publication scan
   removed.

## Consequences

- The vendored `core/archive.py` stays byte-identical; the lab stops
  calling its `engine_sha` directly.
- A reproduction no longer needs the private history to exist as history,
  only the snapshot.
- Tests run on a tree whose identity is supplied to them, so a change under
  development does not refuse its own tests.

## Considered options

- **Extend the hand-kept list.** Rejected: the next omission is the same
  defect.
- **Hash every file under `occams/`.** Rejected: a change to the console's
  templates would then change the engine's identity.
- **Publish the snapshots.** Left to the author: it would republish a
  venue's name and private paths the scan removed.
