# Unadjusted prices, with corporate actions as a separate series

Equity price history can be stored back-adjusted (splits and dividends folded
into historical prices) or as-printed. We store **as-printed prices** and
carry **splits and dividends as a separate dated event series**. The engine
treats a price move explained by a corporate action as a known event rather
than a gap: the stop does not fire, and the position is adjusted.

## Considered options

- **Back-adjusted closes.** The standard choice, one series, no extra
  dependency. Rejected for two reasons. It is restated history, which is the
  precise failure the point-in-time rule exists to prevent — the equity form
  of reading tomorrow's newspaper. And the adjustment factor changes
  *retroactively* every time a dividend is paid, so an archived run stops
  reproducing with no code change at all. Reproducibility would fail
  silently, which is worse than failing.
- **Unadjusted with no actions series.** Cheapest and point-in-time correct,
  but a 4:1 split reads as a -75% gap through every stop and every dividend
  as a fake overnight loss. Results on any multi-year series would be wrong
  in a direction that looks exactly like real drawdown.

## Consequences

A corporate-actions source becomes a required dependency, possibly a paid
one — it needs a question and a price in M0, against a data budget already at
$128.09 of $150 with free credit exhausted.

**A related defect was found while deciding this, and is not itself an
architectural decision:** the donor data adapters cannot serve this project.
`oldschool-investor/src/osi/stooq.py` is unusable live (its own header
records a JavaScript browser-check returning HTML since 2026-07), and both it
and the working `yahoo.py` parse **close only** — no high, no low. Without
highs and lows there is no way to know whether price touched a stop, and
stops are mandatory (ADR-0003). **The equity data path is a new component,
not a donor reuse.** The task list must be corrected accordingly.
