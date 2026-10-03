---
title: "Occams — requirements (v4)"
type: requirements
status: agreed — nothing built, M0 next
created: 2026-08-31
updated: 2026-09-06
supersedes: "REQUIREMENTS-v3.md. Earlier versions remain unedited."
relates_to: "DESIGN-v4.md · TASKS-v4.md · CONTEXT.md · docs/adr/0001-0036"
private: "No venue or broker terms in any public artifact. No credentials, ever."
---

# Occams — requirements (v4)

**Read `DESIGN-v4.md` next, then `TASKS-v4.md`.** The glossary is
`CONTEXT.md` and the decisions with their rejected alternatives are in
`docs/adr/0001-0036`. Later ADR amendments define the decision; this document
states the normative obligation. A contradiction inside this v4 snapshot is a
release blocker and must be resolved before implementation.

**Repository: `occams-test-lab`** (remote `MaverickHQ/occams-test-lab`,
**private**). Package name remains `occams`. `prop-challenge-lab` is a
**source donor, not a dependency**.

---

## 0. What a fresh session must know

### 0a. Decisions taken by the author

| # | Question | Decision |
|---|---|---|
| C1 | Stage 6: proposal-only, or build execution? | **Build it**, behind a human gate, off by default (**R1**) |
| C2 | Crypto in scope? | **No** |
| C3 | Repository | **`occams-test-lab`** — amended 2026-09-06; originally `occams`. The **package** name remains `occams`; only the folder and remote carry the `-test-lab` suffix |
| Q4 | Starting capital, drawdown | **Configurable, required, no defaults** (**R9**) |

### 0b. Verified against the source repositories, 2026-08-31

**These were checked, not assumed. Four killed a plan.**

| # | Finding |
|---|---|
| **A1** | The donor register's raw alpha is exactly **0.620**, but `search_space_size` is populated on all 24 hypotheses and the search-corrected sum is **1.700**. Inheriting that register while applying the correction rule was self-defeating. **The blank page resolves it: this is attempt 1, with a declared total** |
| **A2** | The claim set is **151 claims across 2 entities** (140 `sourced`, 11 `opinion`, many with `measure: "price"`). Effective independent n for a company-level thesis is **2**. **Q5 is closed NO** |
| **A3** | `rules` is imported by **8 of 40** modules including `harness` (`harness.py:27`, `:246` for `payout`). The v1/v2 "retire `rules`, adapt `harness`" boundary did not exist |
| **A4** | `fade_campaign.pine` is **v1.9**, not the v1.8 cited as proof. Its changelog: *"v1.0-v1.8 said 'STOP' and cost two of the campaign's first three setups."* The 500-day parity check passed because engine and renderer shared the same wrong assumption |
| **A5** | The donor engine is **day-boxed**, and `tests/test_ledger.py` states the Monte Carlo is valid *because* days are independent. Multi-day holds break it silently |
| **A6** | `information_axis` was **free text** — 11 spellings for 24 hypotheses, three of them one axis |
| **A7** | `osi/stooq.py` is **unusable live** (JS browser-check since 2026-07) and both it and `yahoo.py` parse **close only**. No highs, no lows, so no way to know whether a stop was touched. **The equity data path is a new component** |

**Verified and carried:** 518 tests, exact by collection · `search.py`'s
plateau rule is real and better than the reference design · `execution.py` is
a clean leaf with zero internal imports · ~50% of modelled failures breach
trailing DD (`RESULTS.md:131`) · `strategy.make_null_strategy` exists.

### 0c. Five findings not to re-derive

1. **Cost in R is invariant to position size**; it varies ~15x with stop
   distance.
2. **Expectancy and EV disagree, and EV pays.**
3. **Trade geometry moved results more than any signal measured.**
4. **Intra-cluster correlation was asserted at 0.9 and measured 0.38.**
   Measure design parameters; do not assert them.
5. **Public intraday price structure on liquid instruments is exhausted at
   this resolution.**

## 1. Goal

**Make a profit, using a research lab that can test more instruments than CME
futures.** Scored in money. The organising picture is the six-stage pipeline:
Research -> Build -> Optimise -> Forward Test -> Risk -> Approve -> Live.

**On the reference architecture.** It is the correct topology with no guards.
Its two decision diamonds have no stated criterion and its reject branch
loops back forever, so searched long enough it always says yes. The evidence
for what that costs is A1: 24 hand-written, individually pre-registered
hypotheses reached a corrected alpha of 1.70. **The topology is the diagram.
The conscience is the guards.**

## 2. Hard constraints

### R1 — Execution is built, gated, and off by default

Amended from v1 on the author's decision. The constraint is not removed; it
is relocated to a gate the system cannot pass.

- **R1.1** The autonomous adapter acts only on a Strategy in state `LIVE`.
  `APPROVED -> LIVE` is **human-only** and no agent, scheduler or automated
  process may perform it.
- **R1.2** Approval is a **cryptographic signature over the spec hash**, made
  with a key whose passphrase is typed interactively and stored nowhere a
  process can read. `LiveGate` verifies the signature, not the presence of a
  record. *(ADR-0009)*
- **R1.3** Live submission additionally requires a config flag and a CLI
  flag. Dry-run is the default mode.
- **R1.4** Write-ahead logging: `ORDER_INTENT` appended before submission,
  reconciled to `ORDER_RESULT` after. An unreconciled intent at startup
  halts.
- **R1.5** Kill paths: kill-file · heartbeat timeout · max daily loss · max
  open positions · broker/internal divergence · portfolio envelope breach.
- **R1.6** Reconciliation each heartbeat. Divergence **halts**; it never
  reconciles silently.
- **R1.7** The proposal path — Telegram card, human places the order —
  remains first-class, not a fallback. It is the default build and the only
  mode needing no credentials.

  > **Clarified 2026-09-10, confirmed by the author.** "No credentials" means
  > **no broker credentials.** The default build holds exactly one credential
  > — the Telegram bot token that sends the card — and it is an R5 credential:
  > environment, keychain or Parameter Store, never the repository, and its
  > shape is in the CI scan. What the default build does *not* hold is
  > anything that can place, amend or cancel an order, which is why R1.4-R1.6
  > do not apply to it (M0.17) and why it needs no execution host.

### R2 — Real capital is at risk

Losses are not capped by an entry fee. **No position is taken on an
unregistered, unmeasured thesis.**

### R3 — Pre-registration is non-negotiable

Mechanism, both interpretations, falsifier and power stated *before* any
measurement. **Refusals are recorded, never discarded** — the contents of the
bin are what make the alpha arithmetic honest.

- **R3.1 The lab states its own falsifier** *(ADR-0033)*. A count of resolved
  **mechanism** verdicts and an outcome at which the lab closes, declared at
  **M0.18** before the first Hypothesis resolves and evaluated mechanically
  against the Register. Superseded hypotheses still count. The system refuses
  to start without it. Distinct from alpha exhaustion, which stops the search
  and is repaired by new data; this stops the enterprise and is not.

### R4 — Alpha is a declared, decrementing, search-corrected budget

*(ADR-0011, ADR-0013, ADR-0016, ADR-0017, ADR-0027)*

- **R4.1** A **total** is declared in config. There is no implicit total.
- **R4.2** `information_axis` is a **closed enum** (A6).
- **R4.3** Config declares a budget for every axis plus distinct mechanism and
  implementation **per-test alpha allocations** for every runnable axis. Both
  test tiers draw from that one axis budget; a proposer spends only from its
  own axis.
- **R4.4** Registration spend is
  `configured_test_alpha x search_space_size`, computed from the declared
  sweep and test tier. **A proposer may set neither value.**
- **R4.5** **Exhaustion refuses registration on that axis.** Budget accrues
  only against observations no Hypothesis has consumed — replenishment is a
  computation, not a decision.
- **R4.6** Capability questions that are not market questions register at
  alpha 0.
- **R4.7** **Invariant, checked on every config load:**
  `sum(axis budgets) + reserve == declared total`. Per-test allocations are
  rates charged against an axis budget, not extra pools, and are never counted
  twice. An axis that cannot run is allocated **0** and receives a recorded
  transfer from reserve before it becomes viable.
- **R4.8** Registration — the act that spends alpha — **requires a human
  confirmation.** A proposer emits drafts only.
- **R4.9** A Hypothesis whose consumed observations overlap a resolved one on
  the same axis beyond a declared threshold is refused until it carries a
  `supersedes` link or a stated distinction.
- **R4.10** An implementation Hypothesis requires a resolved mechanism parent
  on the same axis and uses that axis's configured implementation allocation.
  Registration refuses if its corrected spend exceeds the remaining axis
  budget.

### R5 — No broker credentials in the repository, ever

CI fails the build if a credential-shaped string appears in a commit.

### R6 — Nothing public names the broker's terms

Where those terms are not already public.

### R7 — The repository is private until a publication gate

Publication is an explicit recorded decision. `prop-challenge-lab` passed
that gate without its own context file noticing.

### R8 — There is exactly one source of truth for strategy logic

The Python engine computes. Pine, cards and charts are **generated** from the
same specification and asserted against it. **No strategy logic may exist
only in Pine** (A4).

### R9 — Money parameters are required configuration with no defaults

**Four numbers, all required, system refuses to start without them:**
starting capital · **per-strategy** maximum drawdown · **portfolio** maximum
drawdown · risk per position. Plus account currency and an FX exposure limit.
**No default and no recommended value appears anywhere in the code or these
documents** — the number is the author's, and a default is a recommendation.

### R10 — Time is an instant, never a date

*(ADR-0020)* Bars, claims, signals and regime labels carry a **UTC instant**.
A bar is usable only if its close instant is **strictly after** the signal's
known-at instant. Calendar dates appear in rendering only. Date-only `as_of`
values are read conservatively as end-of-day.

### R11 — Research and execution are separate hosts

*(ADR-0009, ADR-0022, ADR-0030)* Internet-reading code and order-submitting code
share no machine, filesystem or credential set. **Research -> execution
carries signed approvals only.** Execution -> research carries fills and
state as schema-validated data, never commands. Neither mounts the other.

The execution host is a **single long-lived process on a small always-on
instance**, awake through venue hours, holding the credentials and the
write-ahead log. The research host is the **author's own machine**. Approvals
cross as signed files over a one-way transport with **no inbound network
path to the research host**. Scheduled invocation is excluded: a missed run
and a dead host are indistinguishable, which defeats the R1.5 heartbeat
timeout.

### R12 — Safety state is durable and fails closed

*(ADR-0024)* A halt survives restart. Resuming requires the halting condition
to have cleared **on its own terms** *and* an explicit recorded human action.

## 3. The domain model

Full glossary in `CONTEXT.md`. The load-bearing distinctions:

| Term | Definition | Why it matters |
|---|---|---|
| **Hypothesis** | a registered question with mechanism and falsifier. Resolves once. Costs **alpha** | *(ADR-0001)* |
| **Strategy** | a deployable spec. Costs **money**. Built as the apparatus that measures a Hypothesis | may become deployable only by citing a resolved Hypothesis |
| **Mechanism / Implementation Hypothesis** | two tiers: the effect, and whether one build clears its floor | *(ADR-0027)* a mechanism parent may have several implementation children at smaller allocations |
| **Spec hash** | identity of a StrategySpec — what the strategy **is**, not what it was measured under | *(ADR-0007)* |
| **Verdict** | one-time resolution against the floor declared beforehand. Null is a result | |
| **Refusal** | a guard's recorded decision, with reason and evidence | never discarded |
| **Detectable floor** | a **pair**: EV per trade in net R, and a minimum frequency | |
| **Net R** | EV per trade after all costs, in **instrument currency**, divided by R | *(ADR-0026)* scale-free, so the Register is publishable |
| **R** | planned risk, fixed in config in account currency, converted at entry | *(ADR-0003)* |

## 4. Functional requirements

### F0 — Two state machines, and every arrow is a guard

```
Hypothesis:  DRAFT -> REGISTERED -> MEASURED -> RESOLVED
Strategy:    SPECIFIED -> COMPILED -> MEASURED -> FORWARD -> APPROVED -> LIVE -> (HALTED) -> RETIRED
                                          \ REFUSED(reason, evidence, at_state) /
```

A Strategy may not enter `APPROVED` without citing a resolved Hypothesis
whose verdict supports it, and **the deployed spec hash must equal the
resolved spec hash** *(ADR-0002)*.

### F1 — Vendor the dependency-clean core, and nothing else

Verified import-closed: `archive -> charset, privacy, result`; `stats ->
audit -> archive`; `estimators -> audit`; `power`, `calibration`,
`experiment`, `backfill` have no internal imports. `report` is the only leak
and is dropped. **11 modules, 2,412 LOC, vendored unchanged under
`occams/core/`** with a provenance stamp and per-file hash test. Honest reuse
is **~37% of the donor by line**, not 75-80%.

> **Corrected at M1.3, 2026-09-10.** The closure record above was checked
> against the donor at `cfc5af8` before vendoring and is wrong in three
> places: `estimators -> execution` (unrecorded, and `execution` is not in
> the eleven), `calibration -> estimators` and `experiment -> archive, audit,
> power` (recorded as "no internal imports"). `execution` is import-closed
> itself (stdlib only, 202 LOC), so the set is **twelve modules, 2,614 LOC**,
> and `estimators` stays unchanged. The alternatives — patching `estimators`,
> or dropping it and `calibration` with it — were rejected because both
> violate "vendored unchanged" more than one extra file does. "Unchanged" is
> honoured up to two mechanical rules the vendoring script applies and
> `PROVENANCE.md` records: import paths gain `.core`, and the two `ROOT`
> lines gain one `.parent` for the deeper directory.

### F2 — `StrategySpec` with two compilers

Declarative, frozen, single source of truth. `to_engine(spec)` is
authoritative; `to_pine(spec)` is generated and never hand-edited.
`order_type` is a **validated field**: a spec whose order type contradicts
its entry geometry — the v1.8 defect — **fails to compile**. The spec carries
a `UniverseRule`, not an instrument list *(ADR-0025)*, and a
`required_capabilities` set *(ADR-0018)*.

### F3 — Point-in-time correctness, enforced in code

Under **R10**, by instant. A regime label at *t* must be computable from data
no later than *t*.

### F4 — Entry obtainability, adapted to equities

New auditors: **overnight gaps**, the **opening auction**, **halts**.
Auditors are **per strategy family**, not per venue, so the cost recurs with
each proposer. `fill(...)` needs prior close and next open — a signature
change, not an addition.

### F5 — Two simulators

Day-boxed and **position-boxed** with block bootstrap. **`horizon` selects
the simulator by type**; a `MULTI_DAY` spec routed to the day-boxed path
raises. Reusing the day-boxed harness for multi-day holds would silently
invalidate the null (A5).

### F6 — Cost model, bounded to approve and measured to supersede

*(ADR-0015)* A Strategy is approved only if it clears its floor under
**worst-case** costs, so a cost surprise can only be favourable. Measured
costs replace the bound via a **calibration campaign** — minimum size traded
purely to measure — which is a capability question and registers at **alpha
0**. FX conversion spread is a cost; **FX drift is not** *(ADR-0026)*.

### F7 — An account model replaces the challenge rules engine

Cash, settlement, FX sleeve, position limits, drawdown envelopes. `rules` and
`payout` are not inherited (A3).

### F8 — Two event stores, split on publishability

*(ADR-0008)* **Register**: hypotheses, floors, verdicts in net R, refusals,
alpha spend, spec hashes, reserve looks — **publishable by construction**, no
code path writes account currency into it. **Operations**: orders, fills,
money, position state, reconciliation — **never published**. Joined by spec
hash.

### F9 — Telegram proposals with automatic trade logging

**Acknowledgement, never a veto.** Card text generated from the spec (R8).

### F10 — TradingView and Pine, generated only

Blocker to check first: the free tier gives zero indicator alerts (**Q6**).

### F11 — Regime-conditional strategies

First proposer. **The classifier is frozen before any strategy question**,
committed on a priori grounds and calibrated only on the **definition
period** *(ADR-0005)*. Index-level vs per-instrument is a declared parameter,
and the resulting intra-cluster correlation is **measured**.

### F12 — Proposers

Indicator, regime-conditional, **fundamental (blocked, A2)**.

- **F12.1** A proposer emits a **Draft** — mechanism and falsifier — not a
  configuration. Neither present, refused at zero alpha cost.
- **F12.2** **A proposer has no authority**: read-only Register, write only to
  a draft queue, **no credentials**, no Operations access, allowlisted
  network, schema-validated output *(ADR-0016)*.
- **F12.3** Registration requires a human (**R4.8**). The alpha-drain attack
  is the one that matters: exhaustion is terminal, so an injection that
  registered freely would permanently close an axis.
- **F12.4** Retrieved content is **data, never instructions**.

### F13 — The venue is a port, swappable

`propose` is always present; `submit` is reachable only through `LiveGate`.
**Required capabilities are part of identity; the specific venue is context**
*(ADR-0018)*. An adapter's declaration is not evidence: `COMPILED` requires a
current venue-contract result for every required capability. Missing, stale,
or failed evidence refuses the Strategy. Only verified venues are
interchangeable.

### F14 — Deployable and reproducible by a third party

**Reproduction must fail loudly, never `pytest.skip`.** The private path
reproduces an exact Verdict from archived bars. The public path may publish
those bars only when the recorded licence permits it; otherwise it reproduces
the pipeline on legally redistributable or synthetic fixtures and makes no
claim to reproduce the exact historical Verdict.

### F15 — Prior-art and competitive survey before building

(a) reuse or avoid rebuilding; (b) the solution landscape. Use
`repo-security-scan` before cloning anything. Start from
`prop-challenge-lab/docs/EVIDENCE.md`.

### F16 — A small language model is a candidate, not a requirement

Best case is regime classification (F11), and only after F11 provides a
hand-written baseline to beat. Subject to every rule here.

### F17 — Alpha and search-budget accounting

Implements **R4** end to end, including consumed-observation tracking per
Hypothesis (R4.5), hierarchical mechanism/implementation spend (R4.10), and
the overlap gate (R4.9). **Built before any proposer.**

### F18 — Data architecture

- **F18.1** Prices are **as-printed**; splits, dividends and **delistings**
  are a separate dated **corporate-actions** series. A move explained by an
  action is not a gap and does not fire a stop *(ADR-0004)*.
- **F18.2** Bars require full **OHLC** — a close-only series cannot tell
  whether a stop was touched (A7).
- **F18.3** History is partitioned four ways: **definition · measurement ·
  reserve · forward**. Splits are config and stamped into every result.
- **F18.4** **The reserve permits one look per spec hash, ever.** The look is
  recorded; a second is refused *(ADR-0006)*.
- **F18.5** The archive **stores the bars**, content-addressed and immutable.
  Reproduction never touches the vendor *(ADR-0021)*.
- **F18.6** The universe is a **point-in-time rule** including names that
  later delisted — not a list chosen today *(ADR-0025)*.
- **F18.7** Every source has a recorded rights matrix covering private
  retention, internal exact reproduction, raw-bar redistribution, derived
  artifacts, and synthetic fixtures. Ingestion and publication refuse any use
  the recorded licence does not permit *(ADR-0021)*.

### F19 — Portfolio risk

*(ADR-0019)* The **portfolio envelope binds**. Breaching it **halts
everything and retires nothing** — a portfolio drawdown is evidence of
correlation, not of any one Strategy being broken. **Approving Strategy N+1
requires measuring its correlation to the live set** and refusing if the
combined envelope would breach.

### F20 — Live operations

- **F20.1** The **retirement rule is declared at approval**, derived from the
  Strategy's own Monte Carlo **path** distribution *(ADR-0010)*. The path
  distribution is archived at resolution, not just the summary statistic.
- **F20.2** **Halting is always allowed; resuming is not.** A retired
  Strategy returns only via a new Hypothesis.
- **F20.3** Halts are durable and clear on their own terms (**R12**).
- **F20.4** The **forward window is declared as (minimum trades, maximum
  duration)** *(ADR-0023)*. Too few trades at the deadline is a failure of
  the frequency half of the declared floor. **Forward testing falsifies; it
  does not confirm** — passing means no implementation, cost or obtainability
  defect was found, and the Register says so in those words *(ADR-0014)*.
- **F20.5** The forward window runs in **wall-clock time from entry into
  `FORWARD`** — after the single reserve look and **before** approval
  *(ADR-0031)*. It is not a slice of the archive and carries no split
  percentage; **three** configured splits partition history.
- **F20.6** The forward window **executes real orders at minimum size**
  through the proposal path *(ADR-0032)*. Cost and obtainability are
  properties of actual fills; a simulator tests the backtest's assumptions
  against themselves. Minimum size is configuration. A forward-window
  position is a live exposure and counts against the portfolio envelope.
  **This places real money at risk before `APPROVED` and is confirmed by the
  author alongside R9 config.**

## 5. Non-functional

- **N1.** Deterministic and reproducible: seeds recorded, `engine_sha`
  stamped, re-scoreable from the archive. **This is why the backtest cannot
  live in TradingView** — a Strategy Tester cannot be seeded, versioned or
  replayed against a null.
- **N2.** Runs locally at $0, no credentials, no network, except live data
  pulls. `make quickstart` in ten seconds.
- **N3.** **CI from the first commit.** The donor added it late and it found
  six defects in three runs, every one invisible while checks ran on one
  machine.
- **N4.** Local first, cloud second; cloud is a requirement. Tear down what
  is not running. **Only the execution host carries recurring cost**
  *(ADR-0030)*; the research host is the author's machine and stays inside
  N2. **M0.17 asks first whether the R1.7 default build needs a host at all** —
  that build holds no credentials, keeps no write-ahead log and reconciles no
  live position book — and prices an instance only if the answer is yes.
  **M0.14** depends on the answer either way.
- **N5.** Budget covers everything, with a **hard cap that does not reset per
  invocation**. **Data spend is already $128.09 of the $150 total cap, free
  credit exhausted.** M0 must cost every mandatory one-off and recurring item
  — data and licences, TradingView, calibration/execution, infrastructure, and
  contingency — before a go decision.
- **N6.** Every refusal is queryable. "What did we search, and what did it
  cost?" answerable from the Register without re-running anything.

## 6. Explicitly NOT in scope

Crypto · autonomous execution without the human gate · strategy logic in Pine
or a TradingView-authoritative backtest · intraday until F3 and F6 are solved
and data is priced · the **fundamental proposer** until A2 clears ·
rebuilding anything in the vendored core · a dashboard beyond the console.

## 7. Open questions

| # | Question | State |
|---|---|---|
| **Q1** | Does the M0 venue expose historical bars? | **OPEN — do first** |
| **Q2** | Real cost per round trip: spread, FX, fees | **OPEN — do first** |
| Q3 | Which instruments, in which currencies | OPEN |
| ~~Q4~~ | Capital and drawdown | **ANSWERED — required config, four numbers, no defaults (R9)** |
| ~~Q5~~ | Enough cleared claims for fundamentals? | **ANSWERED NO — 151 claims, 2 entities, effective n = 2** |
| Q6 | TradingView tier and cost | OPEN |
| Q7 | What does prior art solve? | OPEN |
| **Q8** | Alpha total, reserve, per-axis budgets, and mechanism/implementation per-test allocations for every runnable axis | **OPEN — author's call. Blocks F17** |
| Q9 | First live venue and its order types | OPEN. Blocks live, not research |
| **Q10** | Source, price, and rights matrix for **OHLC as-printed bars**, **corporate actions including delistings**, and **historical constituents/liquidity** | **OPEN — the largest cost, and it can stop the project.** Three dependencies no earlier draft priced, against $128.09 of the $150 total cap |
| **Q11** | Does the complete mandatory cost model fit inside the remaining total cap, including recurring commitments and contingency? | **OPEN — derived after Q2, Q6, Q9, and Q10. The project cannot start M1 on a partial-budget yes** |

**Q1, Q2, Q10, and the Q11 consolidation are the ones that reshape or stop
the project. All are cheap to answer.**

## 8. Audit against the requirements as originally stated

**Fifth run.** The first draft dropped six of ten by fitting itself to the
end of a conversation. **Run it again before writing code, and whenever the
spec starts sounding like it is arguing for one answer.**

| # | As originally stated | Where it lives | Satisfied |
|---|---|---|---|
| R1 | Research -> Build -> Optimise -> Forward Test -> Risk -> Approve | **F0** | yes, extended to Live per C1 |
| R2 | Telegram alerts + automatic trade logging | **F9** | yes |
| R3 | TradingView + Pine visualisation | **F10**, **F2** | yes — generated, Q6 flagged |
| R4 | AWS deploy via IaC, third-party deployable | **F14** | yes — and the archive now makes it possible |
| R5 | Flexible enough for other prop firms | **F13** | yes — capabilities are identity, venue is context |
| R6 | Profit goal; algos, indicators, backtest, forward test, SLM | §1, **F12**, **F16** | yes |
| R7 | Budget: fees, data, AWS, TradingView, execution | **N5**, **Q10**, **Q11** | yes — Q11 gates the whole programme, not only data |
| R8 | Regime-conditional strategies | **F11** | yes — first proposer |
| R9 | Survey GitHub prior art | **F15** | yes |
| R10 | Research prop-firm solutions, competing labs | **F15** | yes |
| R11 | Live execution (C1) | **R1**, **F13**, **F20** | yes — built, gated, off by default |

> **Sixth run — 2026-09-10, after M9 (standing check S4).** Re-read against
> what M0 found and what is now built. No row's *where it lives* has moved
> and no normative text contradicts another. Three *Satisfied* notes have
> drifted from the record and are corrected here, not rewritten above:
>
> - **R3** — "Q6 flagged" has resolved: the free TradingView tier gives **0**
>   technical alerts and the cheapest tier with any is outside the cap
>   (M0.8, M0.14). R3 stays satisfied *as a requirement* — Pine is generated
>   from the spec — and **is gated by M0.22** before it can be exercised.
> - **R7** — Q11 has answered: **go for M1-M10 on the default build at
>   $129.17; no-go inside the cap for M11's TradingView line and the
>   credentialed execution host** (M0.14). "Gates the whole programme" was
>   right; the gate has now split it.
> - **R11** — "built, gated, off by default" describes M10, which is not yet
>   built. What is built is the R1.7 path: the forward window executes real
>   orders at minimum size through a card a human places (ADR-0032, M9),
>   and the paper venue is refused for that job by name. The credentialed
>   path waits on M0.22.
>
> Everything else reads as it did. R1, R2, R5, R8, R9, R10 are satisfied in
> code as well as on paper (M2, M9, M9, M7, M0.9, M0.10). R4 and R6 are
> unchanged as requirements; R4's IaC is M11.8 and the default build needs no
> instance (M0.17).

> **Seventh run — 2026-09-21, for programme 3 (standing check S4, M14.4).**
> Re-read against three programmes, ADR-0033–0046 and the code as it
> stands. The table above is left as written; every row is re-audited
> here, drift named as drift. Two rows have changed *status by decision*
> since the sixth run and one has changed *where it lives*.
>
> - **R1** — the machine is F0 as built (`occams/strategy.py`, the legal set
>   a frozen literal); `APPROVED -> LIVE` stays human-only (R1.1, R1.2) and
>   **has never been taken**: by ADR-0044 `FORWARD` is a recorded state and
>   the lab holds one Strategy there (Q2-001's winner, 2026-09-17). LIVE and
>   HALTED are backed by `guards/halt.py` and `guards/resume.py`. Satisfied;
>   the tail of the chain is a record, not an execution.
> - **R2** — "Telegram alerts + automatic trade logging": the proposal path
>   (`occams/venues/proposal.py`, the card a human places, R1.7) is built and
>   the paper venue is refused by name; **ADR-0044 moved the alerting path
>   to the lab's own pages** — a signal is a row on `docs/console.html`,
>   rendered on every build. Drift from the wording, not from the intent:
>   *satisfied as decided*, with no Telegram send in this lab.
> - **R3** — "TradingView + Pine visualisation": **closed as not built, by
>   decision (ADR-0044, M11.1–M11.3)**. The sixth run's "satisfied as a
>   requirement, gated by M0.22" no longer holds: M0.22 closed by that ADR
>   and no `to_pine` exists. The obligation that a reader with no code can
>   see what the lab would do is met by the pages (M11.4, M12.4, M12.7).
>   Amending R3's text is the author's, by ADR; until then it reads as
>   *superseded by decision*.
> - **R4** — "AWS deploy via IaC, third-party deployable": the burst
>   (`tools/aws/burst.sh`, M12.3b) is the lab's compute deployment — an
>   idempotent `setup`, a launch template, a group of one, an S3 checkpoint,
>   `teardown --all`, every resource created and removed around a run, the
>   Register a parameter since programme 3. Reproduction is deployable by a
>   third party through `make reproduce-public` (M11.6) and exactly through
>   `make reproduce-private` with the licensed archive (M11.5). The
>   execution host's infrastructure is **deferred outside this lab**
>   (ADR-0044). Satisfied for what the lab runs; *where it lives* is now
>   **F14 and M12.3b**, not M11.8.
> - **R5** — capabilities are identity, venue is context (ADR-0018); every
>   compiled cell declares them and a target family declares
>   `RESTING_ORDERS` from its widest cell (2026-09-18). Unchanged.
> - **R6** — backtest and forward test are built; the profit goal is judged
>   by the floor and, since ADR-0043 and ADR-0045, against always-long at
>   the same geometry and gate; SLM stays parked (M7.6 not built). Unchanged
>   as a requirement; the fifth check and the margin surface are where the
>   "profit" of R6 is now measured.
> - **R7** — the budget: the go at $129.17 (M0.14) stands; data at $0;
>   three burst runs on spot instances, each torn down the same day, their
>   cost outside the repository by rule (no money in any Register or page).
>   The TradingView line and the execution host stayed no-go and were then
>   closed by ADR-0044, so "the gate has split it" resolved into a decision.
>   Satisfied.
> - **R8** — regime-conditional strategies: F11, the frozen causal
>   classifier, per programme (`ClassifierFrozen` #8 in each Register), the
>   instant gate (M4.11), and every gated survey cell and question carrying
>   its regime in the sentence (2026-09-20). Programme 2's supported verdict
>   and programme 3's registration are regime-gated. Satisfied, three
>   programmes deep.
> - **R9, R10** — prior art and competing labs: M0.9, M0.10, unchanged.
> - **R11** — live execution (C1): **deferred by ADR-0044**; the credentialed
>   host is not built or priced here, and nothing trades. The sixth run's
>   "waits on M0.22" resolved when M0.22 closed. Status: *deferred by
>   decision*, not built.
>
> Drift summary: R3 and R11 read as *superseded/deferred by decision*
> rather than *satisfied*; R2 is satisfied through the pages rather than a
> send; R4 lives in the burst and the reproduction targets. No normative
> text contradicts another; the amendments to R2, R3 and R11's wording are
> the author's, by ADR, and nothing in code claims what they no longer
> claim. Next re-run: at the next programme's M0, or when the spec starts
> arguing for one answer.
