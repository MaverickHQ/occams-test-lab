# Time is an instant, never a date

Point-in-time correctness fails on granularity before it fails on
restatement. A vault claim reads `"GOOGL traded at $327.65 intraday on
2026-07-27 (11:39 AM EDT)"` with `as_of: "2026-07-27"`. That day's close came
four and a half hours after the claim was known, so the bar is legitimately
usable — but a claim published at 16:30 ET the same day carries the identical
`as_of` and would make the same bar a lookahead. **A date cannot distinguish
them.**

Across venues it is worse. A GBP account trading LSE and NYSE has two
different "today": LSE closes 16:30 UK, NYSE 21:00 UK. A regime computed for
a calendar date across both embeds a four-and-a-half-hour lookahead on the UK
names, and nothing fails — every test passes and the backtest is simply
wrong.

**Bars, claims, signals and regime labels all carry a UTC instant. The gate
compares instants: a bar is usable only if its close instant is strictly
after the signal's known-at instant.** Calendar dates appear in rendering
only, never in logic.

## Considered options

- **Dates with a per-instrument exchange calendar.** Handles the cross-venue
  offset with no schema change, and still cannot separate a claim known at
  11:39 from one known at 16:30 on the same date.
- **Dates with a global one-day buffer.** Cheap and safe in every case,
  including the cross-venue one, at the cost of discarding a day of genuinely
  available information everywhere.

## Consequences

The claim schema needs a known-at timestamp. Existing date-only `as_of`
values are read conservatively as end-of-day, so that day's bar is unusable —
a day lost per legacy claim, erring in the only safe direction.
