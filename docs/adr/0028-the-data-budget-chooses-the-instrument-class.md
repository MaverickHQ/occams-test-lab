---
status: applies ADR-0017 · defers ADR-0004 and ADR-0025 to a later axis · cost of the deferral recorded 2026-09-06 · replacement instrument set chosen at M0.7 and confirmed by the author 2026-09-10
---

# The data budget chooses the instrument class

Three of the M0 gates price data: full OHLC as-printed bars (M0.3), a
corporate-actions series including delistings (M0.4), and historical
constituents for point-in-time universe construction (M0.5). All three exist
for one upstream reason — **the intention to measure equities over multi-year
history.** Splits and dividends are an equity phenomenon; changing universe
membership is an equity phenomenon; delisting is an equity phenomenon. On an
instrument with none of them, the dependency does not become cheaper, it
ceases to exist.

$128.09 of the $150 cap is spent and free credit is exhausted. Rather than
weaken the evidence standard to fit $21.91, **v1 changes the instrument class
and keeps the standard intact.** The equity-dependent axes are allocated 0
under ADR-0017 and draw from `reserve` by recorded decision if the data is
later acquired.

**This does not overturn ADR-0004 or ADR-0025.** Both stand exactly as
written. They govern an axis that is not running, and they are the reason it
is not running.

## Considered options

- **Free adjusted equity data, with the bias declared.** The obvious cheap
  path, and already rejected twice. ADR-0025: declaring a bias does not
  remove it — the number produced is still not the number the strategy would
  have made. ADR-0004 is worse than a bias objection: the adjustment factor
  is restated retroactively on every dividend, so an archived run stops
  reproducing with no code change. That is not a quality compromise, it
  breaks the foundation the Register rests on.
- **A short window and a fixed equity list chosen so no corporate action
  falls inside it.** Superficially rigorous and **unverifiable**: proving no
  action occurred requires the actions series that has not been bought. The
  claim would rest on the absence of evidence that was never collected.
- **Raise the cap.** Available, and it is the author's decision alone (R9
  reasoning). Not taken here because it answers *how to pay* rather than
  *what v1 should measure*, and this decision is required either way — the
  equity axes cannot run before the data exists, whatever the eventual
  budget. Nothing in this ADR forecloses it.
- **Build the machinery and measure nothing — stop at M3.** Cheapest and
  genuinely safe. Rejected because `make null` proves the pipeline *refuses*;
  nothing would ever prove it can *produce a verdict*. A falsification
  apparatus never run against real market data is untested in the direction
  that matters.

## Consequences

**Two of four axes go to zero.** `fundamental` was already 0 (A2, effective
n=2). `cross_sectional` joins it: comparison across a universe of names is
precisely what point-in-time constituents are for. `regime` and
`price_daily` remain runnable and carry the whole live budget. The invariant
`sum(axis budgets) + reserve == alpha.total` is unaffected.

**The success criterion in DESIGN-v4 §10 changes.** It reads "on liquid
equities". For v1 it is a regime-conditional or daily-price mechanism on an
instrument class with no corporate-action series. The equity form of the
criterion is deferred, not abandoned.

**M4.2, M4.3 and M4.10** — splits, delistings, point-in-time universe — are
built as ports with fixture-backed tests and no live source. The semantics
are proven; the data is absent. This keeps the equity axis a configuration
and licence question later, not a rewrite.

**M0.3-M0.5 still run.** They cost nothing but time, and they price the
option to reopen. M0.6 records the go/no-go with real numbers behind it.

**M0.2 becomes the load-bearing gate.** On instruments without corporate
actions the spread is substantially the entire round-trip cost, and it is
what kills short-horizon edges. The detectable floor declared under D5 must
clear a cost bound that bites harder here than it would on equities.
ADR-0026 also gains weight if the replacement class is FX-denominated.

**The replacement instrument set is not decided by this ADR** — only that it
must carry no purchased-data dependency. That choice follows M0.2 and M0.7.

---

> **Amendment note, 2026-09-06 — the price of the deferral, recorded.**
>
> This decision stands: the money is not there, and ADR-0017 supplies the
> mechanism. Two things learned since should be written down, because a
> deferral whose cost is unrecorded is indistinguishable from a decision
> nobody has to revisit.
>
> **The decision is stronger than it was argued.** All three deferred data
> lines are *properties of equities*. FX pairs do not delist, index CFDs have
> no constituent history to reconstruct, commodities pay no dividends.
> Moving the instrument class did not only avoid three invoices — it
> dissolved three bias classes (survivorship, delisting returns, restatement
> look-ahead) rather than declaring them. That is a better justification than
> cost, and it is the one that would survive a larger budget.
>
> **The deferral has a price, and it was not named.** The capacity
> constraint is the only structural advantage a retail participant holds:
> what is too small for a fund to enter without impact is available, and
> published anomalies persist in exactly that corner because they cannot be
> arbitraged at scale. Capturing it requires holding many small positions at
> once, because breadth in the cross-section is the only substitute for the
> trade frequency a long holding period gives up (`IR ~ IC * sqrt(breadth)`).
> **That is the `cross_sectional` axis this decision allocated 0** — and it
> needs precisely the survivorship-free constituent history that was
> deferred.
>
> So the axis set to 0 is the one where the retail edge structurally lives.
> That does not overturn anything; the money is still not there. It makes
> `cross_sectional` **the first axis reconsidered if M0.14 leaves room**,
> rather than one deferred item among three, and it is why **M0.7** now
> records what the chosen instrument class gives up rather than only what it
> offers.

---

> **Amendment note, 2026-09-10 — the replacement instrument set, chosen and
> confirmed.** This ADR left the set to M0.2 and M0.7. M0.7 chose
> **currently-listed, liquid US-listed ETFs and large-cap shares on daily
> bars**, and the author confirmed it the same day (`docs/M0-ANSWERS.md`
> §M0.7; TASKS status log).
>
> Two things the choice settles about this ADR's own wording. **First**, the
> consequence "an instrument class with no corporate-action series" is
> superseded by the amendment's narrower test, *no purchased-data
> dependency*: the class has dividends and splits, and they cost nothing
> (Tiingo's bar row carries `divCash` and `splitFactor`), while the three
> deferred data lines stay deferred because a currently-listed deployment
> instrument needs no survivorship-free universe, no delisting returns and
> no constituent history. **Second**, the four-way position is on record:
> the class gives up the capacity edge entirely, takes the best `cost_in_R`
> available, moves the sample risk from count to concurrency `rho`, and
> keeps one declared bias — the instrument's own survival — that binds
> selection hypotheses only. ADR-0025's objection to declared survivorship
> is therefore not engaged by `regime` or `price_daily` on this class, and
> is engaged the moment a `UniverseRule` selects from a set.
>
> **What did not change.** `cross_sectional` stays at 0, now on sample size
> as well as money (M0.15). The FX term on this class is 0 or 0.30 % per
> round trip by the account currency, which is the author's at M0.13 and is
> recorded, not recommended.
