---
status: decided 2026-09-12 — the author's act, "freeze the calendar first"; amends ADR-0006
---

# The calendar is frozen: partitions are cut from a recorded span, never the archive's live one

ADR-0006 partitions history into definition, measurement and reserve, and
seals the reserve. ADR-0005's fix on 2026-09-11 made the cut one calendar
for every name: the partitions are percentages of the archive's *common
span*, first day to last, so definition never overlaps measurement across
names. What that left open was found on 2026-09-12 by an ingest: the
common span is the archive's **live** span. IWM's last bar was one day
later than the other three names', and every boundary moved — definition
end 2003-03-01 → 03-02, measurement end 2019-12-21 → 12-23. Both moves
fell on a weekend and no bar changed partition, checked name by name. But
each trading day added at the end of the archive moves the measurement
boundary about 0.8 of a day into the reserve, and 0.3 of a day of
measurement into definition. A fortnight of new bars would hand
measurement a week of the sealed reserve. A reserve that drifts open with
the calendar is not sealed.

## Decision

**The span every partition is cut from is a Register record,
`CalendarFrozen`**, written once by the author's act (`python -m occams
calendar freeze`) and read by every cut thereafter: the classifier's
freeze, `precommit`, `measure_question`, the console. It carries the
start and end day, the split, the boundaries the split produces, the
names present, the config sha, a reason and, for a second freeze, the
calendar it supersedes.

Three rules follow.

1. **Bars beyond the frozen end are forward data.** They fall in no
   partition; the reserve ends at the frozen end. Growing the archive
   changes nothing the lab has measured or will measure on the sealed
   record.
2. **A live cut is allowed only while it reproduces every boundary the
   Register already used.** Without a `CalendarFrozen`, a cut from the
   live span compares that span's boundaries with every recorded
   classifier definition and consumed measurement span; a span that would
   move one — the archive grew since the last cut — is refused by name
   (`CalendarNotFrozen`). An unchanged archive cuts as before. This is the
   precise guard; the freeze is the explicit pin, and the author's act.
3. **A freeze must reproduce every boundary the Register already used.**
   The freeze compares the candidate span's boundaries with every
   recorded classifier definition and consumed measurement span; on a
   mismatch it refuses and names the end day that reproduces them. A
   second freeze is a recorded supersession: it names the calendar it
   replaces and says why (the ADR-0005 shape).

## Consequences

- `occams/register.py`: `CalendarFrozen`. `occams/data/partitions.py`:
  `span_for(register, bars)`, `freeze_calendar(...)`, `frozen_calendar`,
  `CalendarNotFrozen`, `AlreadyFrozen`. `occams/calendar.py`: the
  command. The three cuts read `span_for`; the console draws its bands
  from the record even on a plain build.
- **The live Register's first freeze is pinned to the span the lab has
  already used**: 1993-01-29 to 2026-09-10, which reproduces the
  classifier's definition and Q-003's and Q-004's consumed measurement
  spans exactly. IWM's 2026-09-11 bar is forward data.
- M4.6's row (the partitions) carries the amendment; M4.11 is unchanged.
- A change of split after a freeze is a supersession with a reason, and
  every registered question is stamped with its config already (M6.2):
  changing the split is a recorded decision, not a re-run.

## Considered options

- **Cut from the live span and accept the drift.** Rejected: the drift is
  monotone and silent, and its direction is the one that flatters — the
  measurement partition gains the most recent, best-known days.
- **Pin the span in configuration.** Rejected: the configuration is the
  author's numbers, gitignored and unstamped in the Register; a span that
  every verdict depends on belongs in the chained record beside the
  verdicts, where the console can render it and a reader can check it.
- **Derive the span from the first consumed record.** Rejected: implicit,
  and undefined for a lab whose first act is a classifier freeze. An
  explicit record with a reason is one line and cannot be misread.
- **Freeze per question.** Rejected: one calendar for the pooled set is
  the point of ADR-0005; per-question calendars would let two questions
  on the same axis consume differently cut observations and defeat the
  overlap gate.
