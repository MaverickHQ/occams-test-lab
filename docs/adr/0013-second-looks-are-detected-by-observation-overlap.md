# Second looks are detected by observation overlap, not prevented

Every other guard keys on identity: the spec hash catches a re-run of the
same Strategy. A **mechanism** Hypothesis has no spec, so "does regime
predict fade success?" and "is fade success conditional on trend state?" are
the same question in different words, and nothing else would notice.

Detection reuses the bookkeeping ADR-0011 already requires. **A new
Hypothesis whose consumed observations overlap a resolved one on the same
axis beyond a declared threshold is refused until it carries an explicit
link** — either `supersedes`, stating what changed, or a stated distinction
explaining why it is a different question. The threshold is configuration.

## Considered options

- **Nothing; rely on alpha cost.** Registration already costs, so re-asking
  is self-limiting. Rejected because rewording is cheap relative to a budget,
  and the donor programme's own near-duplicates (`H4-ORDERFLOW` ->
  `H4-ORDERFLOW-v2`) were linked because a person chose to, not because
  anything required it.
- **Hard block on overlap.** Strongest guarantee, and it would refuse
  legitimate replications, corrections after an engine fix, and genuinely new
  mechanisms examined on the same data. A guard that costs more than it saves.

## Consequences

This is deliberately a soft gate. No rule can distinguish a genuine follow-up
from a reworded retry, and one that claimed to would produce confident wrong
refusals. What it does is make a second look **visible and deliberate**: an
operator may still write "this is different because...", but they must write
it, in the register, beside the thing it overlaps. That is a materially
different act from not noticing.
