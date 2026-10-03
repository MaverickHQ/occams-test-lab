# The archive stores the bars, not a reference to them

As-printed prices (ADR-0004) are only stable if a copy of what was printed is
kept. Vendors revise: bad ticks are corrected, late prints folded in,
occasionally whole days restated. **Every result records the hash of the
exact series it consumed, and the archive holds those bars.** Reproduction
reads the archive and never the vendor.

This is what is broken in the donor today, and its skip reasons name it:
`"vendor bars absent — this is the cache, not the archive"` and
`"archive unreachable"`. Reproduction must fail loudly rather than skip, but
failing loudly on data you no longer hold is barely an improvement. The
remedy is to hold the data.

## Considered options

- **Hash plus a reference, re-fetched to reproduce.** Cheap on storage and
  detects drift rather than tolerating it. Rejected because a vendor revision
  then produces a hash mismatch with no way to recover the original series:
  reproduction fails loudly, permanently, and uselessly.
- **Reference only.** Cheapest and licensing-free. A revision silently
  changes what a rerun computes, so an archived verdict and its recomputation
  can disagree with nothing to say which was right — precisely the condition
  the reproducibility requirement exists to prevent.

## Consequences

Storage grows with every run; the donor's archive is already 2.11 GB across
1,283 objects and must never be deleted.

Exact reproduction requires lawful access to the archived bars, not a live
vendor account. **Vendor licensing may forbid republishing bars.** When it
does, exact reproduction remains private and the public path proves the
pipeline with legally redistributable or synthetic fixtures. That public path
must not claim to reproduce the exact historical Verdict. Source rights are
recorded before ingestion and enforced again at publication.
