---
title: "Occams — design (v4)"
type: design
status: agreed — nothing built, M0 next
created: 2026-08-31
updated: 2026-09-10
supersedes: "DESIGN-v3.md. Earlier versions remain unedited."
relates_to: "REQUIREMENTS-v4.md · TASKS-v4.md · CONTEXT.md · docs/adr/0001-0036"
---

# Occams — design (v4)

**Read `REQUIREMENTS-v4.md` first.** Decisions carry their rejected
alternatives in `docs/adr/`; this file is the shape they add up to.

---

## 1. The shape

```
  RESEARCH HOST                                     EXECUTION HOST
  ─────────────                                     ──────────────
  proposers/  ──drafts──►  [human confirms]              venues/
   indicator                      │                       paper
   regime                         ▼                       trading212
   fundamental*            Hypothesis (alpha)             funded-account
                                  │                          ▲
                                  ▼                          │
                            Strategy (money)          signed approval
                                  │                     ONLY (R11)
                    guards ◄──────┤                          │
                                  ▼                          │
                        Register (publishable) ──────────────┘
                                  ▲
                                  └──── fills, state (data, never commands)
                                                        Operations (private)
   * blocked: 2 entities
```

Reference-diagram mapping:

| Diagram box | Here | What changed and why |
|---|---|---|
| Internet -> Research Agent | `proposers/` | emits **drafts with a mechanism**, has no authority, cannot spend alpha |
| Developer AI (TradingView builds + backtests) | `spec/` + `engine/` | **inverted.** Python is authoritative, Pine is generated (R8, N1) |
| Optimisation Agent | `search` | plateau rule survives; objective moves from P(pass) to EV in net R |
| **GOOD SETUP?** | four guards | §3 |
| Forward Testing Agent | `forward/` | **falsifies, does not confirm**; window is (trades, duration) |
| Risk Management Agent | `account/` + `risk/` | portfolio envelope binds; correlation measured at approval |
| **APPROVE FOR LIVE?** | `LiveGate` + **a signature** | the signature is also the trust boundary between hosts |
| Live Trading Agent | `venues/` | built, gated, dry-run by default |

```
occams/
  core/          vendored unchanged, 11 modules, provenance-stamped  (F1)
  hypothesis.py  registration, resolution, supersession              (F0)
  strategy.py    the deployable lifecycle                            (F0)
  guards/        one module per transition; each may REFUSE
  ledger/        alpha_budget, search_budget, consumed observations  (F17)
  spec/          StrategySpec + to_engine + to_pine                  (F2)
  engine/        day_boxed.py · position_boxed.py                    (F5)
  data/          bars, corporate actions, partitions, archive        (F18)
  costs/         bounded and measured equity cost model              (F6)
  account/       cash, FX sleeve, limits, envelopes                  (F7)
  risk/          portfolio envelope, live correlation                (F19)
  proposers/     indicator · regime · fundamental (blocked)          (F12)
  forward/       unseen-data runner, state store                     (F20)
  venues/        port + adapters + LiveGate                          (F13)
  console/       renders the Register, offline-capable               (F8)
```

## 2. Two state machines, joined by a hash

**D1 — Hypothesis and Strategy are separate aggregates** *(ADR-0001)*. One
costs alpha and resolves once; the other costs money and has an operating
life. Conflating them made alpha accounting ad hoc exactly where it matters —
variants, resumes, and strategies resting on more than one question — which
is how the donor reached a corrected 1.70.

```
Hypothesis:  DRAFT ─► REGISTERED ─► MEASURED ─► RESOLVED
                 │           ▲                      │
       human confirms   alpha spent          spec hash frozen in
       (R4.8)           (R4.4)               the Verdict (D2)

Strategy:   SPECIFIED ─► COMPILED ─► MEASURED ─► FORWARD ─► APPROVED ─► LIVE ─► RETIRED
                                                                          ▲│
                                                                    HALTED ┘│
                                          └── REFUSED(reason, evidence) ────┘
```

**D2 — The spec that measured is the spec that trades** *(ADR-0002)*. A
Strategy may be built pre-resolution — it is the **apparatus**, and half the
donor register asked questions unanswerable without one. The hash is frozen
into the Verdict and deployment asserts equality. *Rules out* post-hoc
tuning between measurement and deployment, which is the commonest way
measured edge disappears and is invisible to every test unless identity is
pinned.

**D3 — Two tiers of Hypothesis** *(ADR-0027)*. A **mechanism** Hypothesis
establishes the effect at large alpha; each Strategy built on it registers an
**implementation** Hypothesis — does *this* spec clear its floor net of costs
and obtainability — at the smaller configured per-test allocation for that
axis, and cannot exist without a resolved mechanism parent. Both corrected
spends debit the same finite axis budget. *Rules out* both the free family
(twenty uncounted variants) and strict 1:1 (unaffordable iteration).

**D4 — The hash is identity, not context** *(ADR-0007)*. It covers entries,
exits, stop, sizing, order type, horizon, universe rule and required
capabilities. Data window, seed, `engine_sha` and cost-model version are
**context** in the Verdict. *Rules out* farming reserve looks by nudging
dates or bumping the engine. An engine fix that invalidates a verdict is an
explicit **supersession**, which is visible in the Register in a way a hash
bump is not.

## 3. GOOD SETUP? is five refusals

The diagram's diamond becomes five independently-logged checks, all of which
must pass:

1. **Plateau** — a lone maximum is noise. Chebyshev-1 neighbourhood must have
   `plateau_cells` members and a median within `plateau_slack` of the winner.
   Ported from `search.py:96-115`, the strongest single piece of the donor.
2. **Beats the null** — random entry, Monte Carlo, same costs and geometry,
   **resampling unit matched to the horizon** (D6). *Since ADR-0048
   (2026-10-03): the unit is the calendar day for both simulators. The winner
   and random entry — a coin's side on every box the gate admits — are summed
   by day and resampled together in blocks of consecutive days, at least two
   holds long, so every draw is at the winner's own count, trades that share
   a date stay together and overlapping positions stay together; the draw is
   studentised; a standard error clustered by date is read beside it and the
   check refuses when the two disagree at the corrected alpha. Verdicts
   before it were judged on an independent or a position-ordered null and say
   so.*
3. **Clears its declared floor** — the **pair**: EV per trade in net R, and
   the minimum frequency. Not a floor computed afterwards.
4. **Leave-one-out robustness** — the pooled effect must not be carried by a
   small minority of names *(ADR-0012)*.
5. **Beats always-long** — the winner against a Monte Carlo of always-long at
   the same geometry and gate (a market order on every box, long, the same
   exits, stop, horizon and regime gate), at the corrected alpha; the
   `Measurement` carries the distribution beside the null's. A supported
   verdict attests the entry, not the gate and the side *(ADR-0043, from
   2026-09-17; verdicts before it were evaluated against the four above and
   say so)*. *Since ADR-0049 (2026-10-03): the passive alternative takes the
   winner's own side mix — always-long for a long-only entry, the coin's own
   expectation for a coin, which had been passing this check on a falling
   market by being short half the time — and winner and baseline are
   resampled together by calendar day at the winner's count, as in check 2.
   The margin is recorded in two parts: selection, the passive outcome on the
   boxes the winner chose less the passive outcome on every admitted box; and
   execution, the winner's outcome less the passive outcome on the same
   boxes, which is nil for a market entry. The surface the sweep optimises
   is measured against the same baseline.*

**The objective changes.** `search.py` optimises `p_pass` and its gates are
thresholds on it; here the surface is EV in net R — and, since ADR-0045
(2026-09-19), the **margin over always-long** at the cell's own geometry and
gate: the winner and the plateau are judged on it, the floor stays absolute
EV. Finding 2 applies:
expectancy and EV disagree, and EV pays.

## 4. StrategySpec — one source, two compilers

```python
@dataclass(frozen=True)
class StrategySpec:
    entries: tuple[Rule, ...]
    exits: tuple[Rule, ...]
    stop: Stop                       # mandatory (D5)
    sizing: Sizing
    order_type: OrderType            # validated against entry geometry
    horizon: Horizon                 # INTRADAY | MULTI_DAY -> selects simulator
    universe: UniverseRule           # a rule, not a list (D8)
    required_capabilities: frozenset # identity; the venue is context (D11)
    axis: InformationAxis            # closed enum

def to_engine(spec) -> Strategy      # authoritative, seeded, engine_sha stamped
def to_pine(spec)   -> str           # generated; never hand-edited
```

**D5 — Every Strategy declares a stop; R is planned and fixed** *(ADR-0003)*.
`R = config.risk_per_trade` in account currency, converted at entry; size is
`R / stop_distance` in instrument currency. Results are multiples of planned
R, so a gap through the stop records as worse than -1R rather than clipped.
A regime Strategy carries a *disaster stop* beside its signal exit. *Rules
out* stopless specs, unbounded per-position loss, and an undefined floor unit.

**D6 — `horizon` selects the simulator, by type.** *Rules out* running a
multi-day hold through a Monte Carlo whose validity depends on days being
independent — a failure no test would have caught (A5).

**D7 — Pine is generated, never written** *(ADR-0002 consequence, A4)*. A
spec whose order type contradicts its entry geometry fails to compile. *Rules
out* the v1.8 class of defect, where a hand-written engine and a
hand-written renderer agreed with each other and were both wrong for nine
versions while a 500-day parity check passed.

## 5. Data

**D8 — The universe is a point-in-time rule** *(ADR-0025)*, evaluated at each
date from the full listed set **including names that later delisted**. *Rules
out* survivorship bias, which declaring a fixed list in advance does not fix
because the bias is in how the list was chosen, not when it was written down.

**D9 — As-printed prices, with corporate actions as a separate series**
*(ADR-0004)*. *Rules out* back-adjusted closes, whose adjustment factor
changes retroactively on every dividend so an archived run stops reproducing
with no code change. Delisting is a corporate action, or a position in a
vanishing name has no exit price.

**D10 — Time is an instant** *(ADR-0020)*. A bar is usable only if its close
instant is strictly after the signal's known-at instant. *Rules out* the
silent cross-venue lookahead: LSE closes 16:30 UK and NYSE 21:00 UK, so a
regime computed for a calendar date embeds four and a half hours of hindsight
on the UK names while every test passes.

**D11 — Three configured partitions, and the reserve permits one look per
hash** *(ADR-0006, ADR-0031)*. Definition (fixes the classifier) ·
measurement · reserve — percentages over the archive. **The forward window
is not a fourth**: it is wall-clock time from entry into `FORWARD`, declared
as (minimum trades, maximum duration), and carries no percentage. The look is recorded against the spec hash; a second is refused, so
another look needs a different spec, a new Hypothesis and new alpha. *Rules
out* the holdout quietly becoming training data.

**D12 — The archive stores the bars** *(ADR-0021)*, content-addressed and
immutable. *Rules out* a vendor revision breaking reproduction irreparably —
a stored hash plus a reference would fail loudly and permanently, which is
correct and useless. Exact private reproduction reads the archive. Public
reproduction uses archived bars only when the source rights permit
redistribution; otherwise it proves the pipeline with legally redistributable
or synthetic fixtures and never labels that an exact historical reproduction.
The source rights matrix is therefore an ingestion and publication guard, not
documentation deferred until release.

**D13 — The regime classifier is frozen first** *(ADR-0005)*, on a priori
grounds, calibrated only on the definition period. *Rules out* the double-dip
the budget accountant cannot see: tuning classifier parameters until a
strategy works is a search that `search_space_size` never counts.

## 6. Alpha

```toml
[capital]                    # all required, no defaults (R9)
starting = ...
max_drawdown_per_strategy = ...
max_drawdown_portfolio = ...
risk_per_trade = ...
currency = "GBP"
fx_exposure_limit = ...

[alpha]
total = ...                  # required; author's decision (Q8)
reserve = ...                # required
correction = "bonferroni"

[alpha.axes.regime]
budget = ...
mechanism_test_alpha = ...
implementation_test_alpha = ...

[alpha.axes.price_daily]
budget = ...
mechanism_test_alpha = ...
implementation_test_alpha = ...

[alpha.axes.cross_sectional]
budget = ...
mechanism_test_alpha = ...
implementation_test_alpha = ...

[alpha.axes.fundamental]     # cannot run yet (A2)
budget = 0.00
mechanism_test_alpha = 0.00
implementation_test_alpha = 0.00
```

**D14 — Exhaustion is terminal until new data, and replenishment is
mechanical** *(ADR-0011, ADR-0017)*. An axis that cannot run is allocated 0 and
receives a recorded transfer from reserve when it becomes viable, under the
invariant `sum(axis budgets) + reserve == total`. Mechanism and
implementation allocations are per-test rates against that budget, not extra
pools. For every runnable axis config enforces
`0 < implementation_test_alpha < mechanism_test_alpha`; registration
computes the corrected spend and refuses if it exceeds the remaining axis
budget. Budget accrues only against observations no Hypothesis has consumed.
*Rules out* both double-counting child pools and a soft budget — which is how
the donor reached 1.70 — while preserving affordable, counted iteration.

**D15 — The proposer cannot spend alpha** *(ADR-0016)*. It emits drafts;
a human confirms registration. The attack that matters is **alpha drain**: a
proposer reads adversarial text by design, and because exhaustion is terminal
an injection registering freely would permanently close an axis. No money
lost, programme dead. *Rules out* the autonomous loop the reference diagram
draws.

**D16 — Second looks are made visible, not prevented** *(ADR-0013)*. Overlap
in consumed observations on the same axis refuses registration until an
explicit `supersedes` link or a stated distinction is supplied. Deliberately
soft — no rule separates a genuine follow-up from a reworded retry, and one
claiming to would refuse good work confidently.

**D17 — Naming.** Not "alpha ledger": in the donor `alpha` already means
significance level and `ledger` already means per-day P&L and audit trail.
Use `alpha_budget` and `search_budget`.

## 7. Live

**D18 — Approval is a signature, and it is also the trust boundary**
*(ADR-0009, ADR-0022)*. `LiveGate` verifies a signature over the spec hash, made
with a key whose passphrase is never stored. Research -> execution carries
**signed approvals only**; execution -> research carries fills and state as
data. The executor's rule is one sentence: **act only on things bearing a
valid signature.** *Rules out* a shared writable store, which would restore
the injection path the host split closed.

**D26 — The execution host is a durable process** *(ADR-0030)*. R1.6
reconciles each heartbeat, R1.5 kills on heartbeat timeout, and R1.4 halts
on an unreconciled `ORDER_INTENT` at startup — so liveness must itself be
the signal, and absence must be an event rather than silence. The execution
host is a **single long-lived process on a small always-on instance**, awake
through venue hours, holding the credentials and the write-ahead log. The
**research host is the author's own machine** (N2: local, $0, no
credentials). Approvals cross as signed files over a one-way transport with
**no inbound path to the research host**. The heartbeat period is declared
config, and R1.5's timeout is calibrated against it. *Rules out* scheduled
invocation, where a missed run and a dead host are indistinguishable, so the
timeout kill path fires on its own scheduling gaps and gets tuned off. **M0.17
asks first whether the R1.7 default build needs a host at all** — no
credentials, no write-ahead log, no live position book to reconcile, so the
argument above is an argument about the *credentialed* path — and prices an
instance only if the answer is yes. M0.14 depends on the answer either way.

**D27 — The lab declares its own falsifier** *(ADR-0033)*. A count of
resolved **mechanism** verdicts, and an outcome, at which the lab closes.
Declared at **M0.18** before the first Hypothesis resolves, held in config,
evaluated mechanically against the Register, never judged in the moment —
the retirement rule construction (D19) applied one level up. The count
includes **superseded** hypotheses, so relabelling a null cannot reset it,
and it is stated over mechanism verdicts because an implementation null says
only that one apparatus could not reach the effect. *Rules out* stopping by
judgement, which asks for the decision at the moment least able to make it;
and rules out treating alpha exhaustion as the stopping rule, since ADR-0011
repairs exhaustion with new data and a lab that replenishes runs forever by
construction. The system refuses to start without the falsifier (R9
pattern). Firing it **publishes** — the Register carries no account state
(D-store split), so the count, the floors and every verdict go out as the
negative result.

**D19 — The retirement rule is declared at approval** *(ADR-0010)*, derived
from the Strategy's own Monte Carlo **path** distribution, evaluated
mechanically. *Rules out* deciding mid-drawdown with money moving, which is
sequential testing with no correction at the worst possible moment. **The
path distribution must be archived at resolution**, not just the summary.

**D20 — Halting is always allowed; resuming is not.** Any human may halt
anything without justification — safety is unilateral. A **retired** Strategy
returns only via a new Hypothesis. A **halted** one resumes when the halting
condition has cleared on its own terms plus a recorded human action
*(ADR-0024)*: a daily-loss halt cannot be cleared by insisting, a divergence
halt cannot be cleared by waiting.

**D21 — The portfolio envelope binds** *(ADR-0019)*. Breaching it halts
everything and retires nothing — a portfolio drawdown is evidence of
correlation, not of any Strategy being broken. **Approving Strategy N+1
measures its correlation to the live set** and refuses if the combined
envelope would breach. Regime strategies share the regime, so they go wrong
together by design; the correlation is measured, never assumed.

**D22 — Forward testing falsifies** *(ADR-0014, ADR-0023, ADR-0031,
ADR-0032)*. Window declared as (minimum trades, maximum duration), evaluated
once, in **wall-clock time before approval**. It **executes real orders at
minimum size** via the proposal path: cost and obtainability are properties
of actual fills, and a simulator would test the backtest's assumptions
against themselves. Passing means no
implementation, cost or obtainability defect was found — **not** that the edge
is confirmed, because confirmation would need ~125 trades at alpha 0.05 and
~265 after correction, one to two years at 0.5 trades/day. Too few trades at
the deadline is the frequency half of the declared floor failing. *Rules out*
both optional stopping and the zero-trade vacuous pass.

**D23 — Approve on a conservative cost bound** *(ADR-0015)*. A cost surprise
can then only be favourable; the donor's slippage assumption came out 2x
optimistic. Measured costs supersede via a calibration campaign registered at
alpha 0.

**D24 — Required capabilities are identity; the venue is context**
*(ADR-0018)*. The adapter exposes a capability manifest, but self-declaration
is not sufficient. Each capability carries dated conformance evidence from
the venue's live contract, official sandbox, or a human-approved minimum-size
calibration campaign. `COMPILED` refuses missing, failed, or stale evidence,
and also refuses when `stop_distance / R` exceeds the declared rounding
tolerance on a whole-share venue. *Rules out* discovering at submission, with
money on, that the broker cannot express the strategy.

**D25 — FX drift is an exposure, not an edge** *(ADR-0026)*. The conversion
spread is a cost and belongs in net R; the rate moving during a hold is a
currency position nobody asked for. *Rules out* bundling an unhedged bet with
no declared mechanism, no falsifier and no registered hypothesis into every
verdict — an undeclared information axis taken with real money. Net R is
measured in **instrument currency**, which also keeps verdicts comparable
across a multi-currency universe.

## 8. What is vendored, ported, and not taken

| | | |
|---|---|---|
| **Vendor unchanged** | `stats` `estimators` `power` `calibration` `result` `archive` `audit` `experiment` `backfill` `privacy` `charset` | **2,412 LOC**, import-closed, provenance-stamped with a per-file hash test |
| *Correction 2026-09-10* | `+ execution` | `estimators` imports it; F1's closure record missed the edge. **Twelve modules, 2,614 LOC.** `execution` is still *ported* for the equity auditor shape — the vendored copy is what `estimators.measure_from_fill` needs, nothing more. See F1's note and `PROVENANCE.md` |
| **Port the idea, rewrite the code** | `search` (plateau rule) · `execution` (auditor shape) · `feed` (`DataSource`, `ReplaySource`) · `state` · `telegram` · `cards` | the shape transfers; the ORB/futures logic does not |
| **Do not take** | `harness` `sim` `rules` `payout` `profiles` `plans` `strategy` `poller` `dayflow` `sessions` `calendar` `attribution` `parity` `synth` `spend` `verdict_*` `fade` `report` `obsidian` | day-boxed, futures-shaped, or challenge-specific |

Honest reuse is **~37% by line**. Still an excellent argument for vendoring:
the 37% is the part that took a year to get right.

**Must be built, not adapted:** the position-boxed simulator · equity `Costs`
(no shared fields with the futures version) · the account model · **and the
entire equity data path** — `stooq.py` is dead and both donor adapters are
close-only (A7).

## 9. The hard parts

**H1 — Point-in-time, by instant** (D10). The trap is granularity before
restatement, and it fails silently across venues.

**H2 — The resampling unit** (D6, A5). The donor Monte Carlo is correct only
because days are independent. Multi-day holds overlap; the honest unit is the
position with a block bootstrap. **No test would catch this** — everything
passes and the null is simply wrong. *It was wrong, and a test now catches
it: the size table (`make calibrate`, M16.7) measured the position-boxed null
passing a world with nothing in it fourteen times in a hundred at a declared
one, and the day-boxed one nine times under a shared market. The unit is the
calendar day since ADR-0048.*

**H3 — Survivorship** (D8). Twenty liquid names picked today and backtested
ten years measures a portfolio of known winners.

**H4 — Rights and affordability** (D12, N5). A technically suitable source is
unusable if its licence forbids the required retention or reproduction path,
and cheap data does not make the programme affordable if mandatory recurring
costs breach the same $150 total cap. M0 records both decisions before M1.

## 10. Success and failure

**Success:** a registered, adequately powered test of a regime-conditional
mechanism on liquid equities, with a verdict either way, produced by a
pipeline that refuses a coin flip.

> **Read against the confirmed class, 2026-09-10.** "Liquid equities" is the
> M0.7 class the author confirmed: **currently-listed, liquid US-listed ETFs
> and large-cap shares on daily bars.** ADR-0028's consequence rewrote this
> criterion to "an instrument class with no corporate-action series"; the
> amendment to that ADR narrowed the requirement to *no purchased-data
> dependency*, and the confirmed class meets it — dividends and splits
> arrive in the bar row at $0 (M0.3), and delistings do not touch a
> currently-listed deployment instrument. The class keeps **one declared
> bias, the instrument's own survival**, which binds selection hypotheses and
> not the mechanism hypotheses `regime` and `price_daily` run. "Adequately
> powered" is M0.15's conditional go: it holds across the declared ranges
> and turns on the concurrency `rho` M7.7 measures.

**Failure that still counts:** M0 shows the data rights are incompatible, the
complete programme is unaffordable, or the costs make the question
unanswerable, and the project stops at a cost of a day. **Treat that as a good
outcome.**

**Failure that does not count:** building first and discovering the sample,
cost or data problem afterwards. The donor's most expensive lesson was that
the instrument outran the question it could answer.

**The specific failure this design is built against:** a guard that passes
because it was given nothing to look for. It appeared eight times in the
donor programme; it let `test_cards.py` bless a wrong order type for nine
versions; it is what `make reproduce` still does when the archive is absent;
and it was found once more during this design review, in a forward window
that could close with zero trades. **Hence M2 (TASKS-v4): before any real
strategy exists, run a known-null through the whole pipeline and prove it is
refused.**

**And its mirror, added 2026-09-06** *(ADR-0029)*. Four conservative gates,
all of which must pass, compose multiplicatively: **a pipeline that refuses
everything satisfies every check in this specification**, and satisfies the
null harness *more* comfortably the worse it gets. A check that gets easier
to pass as the system degrades is not a check. So a second known-answer probe
runs beside it — `make signal`, a **planted effect at the declared floor**,
which must be **accepted**, naming that all five checks passed (S10, M2.7b).
The apparatus is bracketed from both sides or it is not tested.

**Success (§10) is therefore qualified.** "A verdict either way" presumes the
machine can produce both. S3 evidences one direction and S10 the other, and
S10 is only interpretable at a sample size M0.15 shows adequate — otherwise a
failure is ambiguous between gates too strict and an effect undetectable in
that many trades.
