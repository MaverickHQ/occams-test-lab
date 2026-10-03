---
title: "Occams — M0 answers"
type: evidence
status: "stages 1-3 run 2026-09-10 — verdicts in the table below; stage 4 is the author's and is untouched"
created: 2026-09-10
relates_to: "TASKS-v4.md §M0 · REQUIREMENTS-v4.md §8 · ADR-0028 · ADR-0029 · ADR-0030 · ADR-0032 · ADR-0033 · DRAFT-001 · DRAFT-002"
convention: "Append-only. Every figure carries a source and an access date. A price is as displayed on the day, in the currency displayed; no exchange-rate conversion is asserted anywhere in this file. Declared ranges are labelled as declared."
---

# M0 answers

Run 2026-09-10 in the sequence the order block in `TASKS-v4.md` prescribes:
stage 1 free lookups, stage 2 derived arithmetic, stage 3 the M0.14
consolidation. **Stage 4 — M0.11, M0.13, M0.18 — is not here.** Those are
the author's numbers and nothing in this file picks, recommends or defaults
them.

**Method.** Primary pages were fetched; where a page was a script shell it
was rendered in a browser and its text read; two PDFs were text-extracted;
two event counts were computed from published lists with the method stated
inline. Nothing was purchased, no account was logged into, no repository was
cloned (so `repo-security-scan` was not needed for M0.9), and the one
verification request to EDGAR used a generic `User-Agent` without a contact
address — see M0.20 for why that matters. Every price is *as displayed on
2026-09-10* and will drift; the access date is the provenance.

## Verdict table

| task | state | one line |
|---|---|---|
| **M0.1** | **DONE** | **No.** The Public API exposes no bars, candles or market data of any kind. Every bar in the lab comes from M0.3 |
| **M0.2** | **DONE** | Per-class round-trip cost recorded with provenance; the **spread is unpublished** and is a declared range here, measured on the demo account later. **CFD costs are unpriceable with provenance** — two of three components are in-app only |
| **M0.3** | **DONE** | As-printed daily OHLC exists at **$0** (Tiingo Starter, US-listed) and at **£19.99/mo** (EODHD, world incl. LSE, delisted). Rights matrix recorded |
| **M0.4** | **DONE — with a finding** | Splits and dividends: yes at $0 (listed names). **Delisting returns and acquisition terms: no vendor supplies them**; Norgate says so in writing. D9's term must be hand-built or declared |
| **M0.5** | **DONE** | Free for *membership-change events* (FTSE 100 PDF, S&P 500 compiled list); paid for daily point-in-time membership across families (Norgate Platinum $630/yr; EODHD add-on £29.99/mo) |
| **M0.6** | **DONE — go at $0** | Data subtotal **$0** on the Tiingo path with three declared limits. **Every paid line is a no-go inside $21.91.** A conflict between Norgate's deletion-on-expiry clause and D12's immutable archive is recorded |
| **M0.7** | **DONE — conditional on M0.13 currency** | Class: **currently-listed, liquid US-listed ETFs and large-cap shares on daily bars.** Four-way position stated. The account-currency choice moves `c` by 0.30 % per round trip — the whole floor at a 2 % stop |
| **M0.8** | **DONE** | Basic £0 gives **0 technical alerts** (Q6 confirmed). Essential £12.95/mo (annual billing) is the floor for M11 |
| **M0.9** | **DONE** | Reuse / avoid / ignore table, twelve repositories, licence and activity from the GitHub API |
| **M0.10** | **DONE** | Landscape appended below. **No surveyed platform supports Trading 212**; none offers pre-registration, alpha budgeting or a null harness |
| **M0.11** | OPEN — author | Alpha total, reserve, split. Gates M6 |
| **M0.12** | **DONE** | Capability-evidence plan recorded: every venue claim, its source, and how it is verified on the demo environment |
| **M0.13** | OPEN — author | Money, incl. forward-window minimum size and **currency, which M0.16 shows is not cosmetic** |
| **M0.14** | **DONE — split verdict** | **Go for M1-M10 on the default build: $129.17 time-bounded over twelve months, inside $150.** **No-go inside the current cap for M11's TradingView line and for the credentialed execution host.** M1 is unblocked |
| **M0.15** | **DONE — split verdict** | `price_daily` / `regime` on the M0.7 class: **go on paper** across the declared ranges, conditional on concurrency `rho`. `cross_sectional` (DRAFT-001) and DRAFT-002: **no-go at any floor ≤ 0.25R** — `N_eff` lands at 40-190 against 257-1,442 required |
| **M0.16** | **DONE** | Break-even ratio and admissible stop band per class. UK single names excluded below a 4 % stop at a 0.15R floor; CFDs excluded on evidence |
| **M0.17** | **DONE — $0** | The R1.7 default build needs no host. The credentialed path will; it is outside the cap by construction and unpriced here by design |
| **M0.18** | OPEN — author | Lab falsifier count. Gates M6 |
| **M0.19** | **DONE** | Free lists exist for FTSE 100 (1984→) and S&P 500 (1963→). **Index-rule deletions run ~7/yr and ~8/yr respectively** — the M0.15 term, and it is too small |
| **M0.20** | **DONE** | XML from May 2013; as-filed separable from 13F-HR/A; acceptance timestamp available; 10 req/s; free. **Yes — the filing history answers the constituent half of M0.5 at zero cost for a 13F-defined universe** |

**None of the six stop-capable tasks stops the project.** What they do is
narrower and more useful: they confirm ADR-0028's allocation from a second,
independent direction (M0.15 — `cross_sectional` is unaffordable in *trades*,
not only in money), they surface two cap decisions that are the author's
(M0.14), and they show the account currency is a cost parameter (M0.16).

---

## Stage 1 — free lookups

### M0.1 — Q1: does Trading 212 expose historical bars?

**Answer. No.** The Trading 212 Public API (v0, "currently in beta and is
under active development") exposes exactly these groups: **Accounts**
(`GET /api/v0/equity/account/summary`), **Instruments**
(`/equity/metadata/exchanges`, `/equity/metadata/instruments`), **Orders**
(`GET /equity/orders`, `POST /equity/orders/limit|market|stop|stop_limit`,
`GET|DELETE /equity/orders/{id}`), **Positions** (`GET /equity/positions`),
**Historical events** (`/equity/history/dividends|orders|transactions`,
`GET|POST /equity/history/exports` — CSV reports) and **Pies (deprecated)**.
There is no market-data, quote, candle or bar endpoint. "The API described
here is enabled and usable only for Invest and Stocks ISA account types."
"Orders can be executed only in the primary account currency." Two
environments: `https://demo.trading212.com/api/v0` (paper) and
`https://live.trading212.com/api/v0`.

**Source.** `https://docs.trading212.com/api`, rendered in a browser
2026-09-10 (the page is a script shell; a plain fetch returns only the
title). API keys: help centre article 14584770928157 — generated in-app,
under practice mode first.

**Consequence.** The venue is an execution and reconciliation surface only.
Every bar, every corporate action and every universe fact comes from M0.3-M0.5
and M0.19-M0.20. The "live data pulls" N2 permits are vendor pulls, not
broker pulls. One positive: `/equity/history/orders` and `/transactions` plus
the CSV export are the **real-fill source ADR-0032 needs**, on both demo and
live.

### M0.2 — Q2: real cost per round trip

**Answer.** Published components, Invest / Stocks ISA (help centre article
11471996799517, accessed 2026-09-10): trading commission "Free"; custody
"Free"; FX fee "0.15%". Exchange and tax-authority charges (article
360007081637): LSE shares "Stamp Duty Reserve Tax is charged at 0.5% on share
purchases" — "no Stamp Duty charge applied to gilts, bonds or ETFs", "Most
stocks traded on the LSE AIM are exempt"; "PTM Levy … £1.5 per trade for
orders over £10,000" on purchase and sale; NYSE/NASDAQ/OTC: SEC transaction
fee on sells (the two articles print it as "$0.00206 of the value" and
"$0.00206%" — negligible on either reading) and "FINRA Fee … $0.000195 x
quantity sold"; Euronext Paris "French Financial Transaction Tax … 0.4% …
purchase of shares of French companies with a market cap of over 1 billion".
**Neither article mentions the spread.** CFD (article 11471872562461):
commission "Free"; FX "0.5%", charged "on the results of closed positions" per
third-party summaries and the article's wording; "Spreads are dynamic and
change depending on the underlying market conditions"; "Positions held in
your account overnight will incur an overnight interest … can be positive or
negative" — per instrument, in-app only.

**The round-trip fixed cost `c_fixed` per class, as a fraction of notional,
spread excluded:**

| class | `c_fixed` | composition |
|---|---|---|
| LSE share, GBP account | **0.50 %** | SDRT on the purchase; +£3.00 if both legs exceed £10,000 |
| LSE-listed GBP-denominated ETF / ETC / investment trust, GBP account | **0.00 %** | no SDRT, no FX |
| US-listed share or ETF, GBP account | **0.30 %** | FX 0.15 % on each of two conversions (a reading of "0.15%" that third-party reviews share; the article does not say "each side") + SEC/FINRA, negligible |
| US-listed share or ETF, USD account | **≈ 0.00 %** | SEC/FINRA only; the FX cost moves to funding, once |
| Xetra / Euronext share, GBP account | **0.30 %** (+0.40 % FFT on large French names) | FX both ways |
| CFD, any | **unpriceable** | spread in-app, overnight in-app, FX 0.5 % of the result |

**The spread** is the remaining term and it is not published. It is
**declared here as a range** and **measured by the author on the demo
account** per instrument class before M5 closes: liquid US ETF / large cap
0.02-0.10 %, FTSE 100 name 0.05-0.15 %, FTSE 250 name 0.20-0.60 %, small cap
1-3 %, index CFD 0.05-0.20 % — provenance: none beyond common observation, which
is why they are ranges and why M5's Done-when must replace them.

**Consequence.** Feeds M0.16 directly. CFDs are excluded from M0.7 **on
evidence grounds** — a cost that lives only in an app cannot carry the
provenance R3 requires — not on merit. Blocks M5 until the spread is
measured; the ranges above are for the on-paper gates only.

### M0.3 — Q10a: full OHLC as-printed daily equity bars

| source | as-printed OHLC | history | delisted | price (as displayed 2026-09-10) | rights | source |
|---|---|---|---|---|---|---|
| **Tiingo Starter** | fields `open high low close adjOpen adjHigh adjLow adjClose volume adjVolume divCash splitFactor`; "Both raw prices and adjusted prices are available" | "30+ Years" | **not stated** | **$0** — 500 unique symbols/mo, 50 req/hr, 1,000 req/day, 1 GB/mo | "Internal Use Only"; redistribution priced separately on request | tiingo.com/about/pricing; tiingo.com/documentation/end-of-day |
| Tiingo Power | same | same | not stated | $30/mo or $300/yr — 109,894 symbols/mo, 10k/hr, 100k/day, 40 GB | "Internal Use Only" | same |
| **EODHD "EOD Historical Data — All World"** | "The OHLC values (open, high, low, close) are raw — adjusted for neither splits nor dividends" + `adjusted_close` | US "from earliest available (e.g. Ford Motors from Jun 1972)"; non-US "mostly from Jan 3, 2000" | **yes** — delisted tickers carry the suffix `_old` | **£19.99/mo or £199.90/yr** — 100,000 calls/day; Splits & Dividends ✓; Delisted ✓; Fundamentals ✗; Bulk EOD ✗ | Non-Professional: "permitted to store, manipulate, and analyze the data for private, non-commercial purposes"; prohibited from "selling, reselling, retransmitting, redistributing, displaying, or granting access"; derived data / publication **not addressed** | eodhd.com/pricing; eodhd.com/financial-apis/api-for-historical-data-and-volumes; eodhd.com/financial-apis/terms-conditions |
| EODHD Free | raw OHLC | limited | — | £0 — 20 calls/day, no splits/dividends | same | eodhd.com/pricing |
| **Norgate Data, US Stocks** | "Unadjusted (raw)" is one of four adjustment modes | Silver 10 yrs · Gold 20 yrs · Platinum "Back to 1990" · Diamond "Back to 1950" | Platinum and Diamond only | Silver $270/yr · Gold $360/yr · **Platinum $630/yr** · Diamond $787.50/yr (6-month: $148.50 / $198 / $346.50 / $433.13) | EULA: "use the Content for a personal purpose such as investment or trading"; "will not … redistribute the Content in any way or form except where express permission has been sought and obtained to publish limited extracts"; **"Following any expiration of a Subscription the Licensee must delete all Content"**; "permitted to retain Derived Data" — defined to include "simulated trading (backtests), and statistics related to those results"; FAQ: "no alternative business/commercial licensing" | norgatedata.com/stockmarketpackages.php; /data-package-faq.php; /subscribe/eula.php; /faq.php |
| Massive (formerly Polygon) Stocks | not stated | Basic 2 yrs · Starter 5 yrs · Developer 10 yrs · Advanced "20+ Years" | not stated | Basic $0 (5 calls/min) · Starter $29/mo · Developer $79/mo · Advanced $199/mo ("Non-pros only"); annual −20 % | not stated on the page | massive.com/pricing (polygon.io 301-redirects there) |
| Sharadar SEP (Nasdaq Data Link) | not verified | "end-of-day US stock and fund prices with history since 1998" | yes, per vendor | **not displayed** — the pricing page is a script shell behind a cookie wall and a login; the vendor site shows no prices | not verified | sharadar.com; quantrocket.com/sharadar; data.nasdaq.com/databases/SEP/pricing |
| Stooq | — | — | — | — | — | the donor adapter is dead (TASKS); not re-priced |

**Answer.** As-printed daily bars exist at **$0** for US-listed names
(Tiingo Starter, raw and adjusted side by side with the dividend and split
factors in the same row) and at **£19.99/mo** for world coverage including
the LSE with delisted names (EODHD). Norgate is the survivorship-complete
option at **$630/yr**.

**Rights, for every required use (F18.7).** *Private retention*: permitted
by all while subscribed; **Norgate requires deletion at expiry**. *Exact
internal reproduction*: permitted by all while subscribed (Tiingo's "internal
use" covers a private repository). *Raw redistribution*: **prohibited by
all**. *Derived artefacts*: Norgate permits explicitly (backtests, statistics,
rules); **Tiingo and EODHD do not address it** — treated as not permitted for
publication until asked. *Synthetic fixtures*: unaffected — not the vendor's
data.

**Consequence.** M0.6 has a $0 path. D12's public-reproduction rule — archived
bars only where rights permit, otherwise redistributable or synthetic
fixtures — is engaged for every source above, so the archive is private and
the public proof is synthetic, as D12 already provides.

### M0.4 — Q10b: corporate-actions series — splits, dividends, delistings, acquisition terms

| source | splits / dividends | delisting dates | delisting return / acquisition terms |
|---|---|---|---|
| Tiingo | `divCash`, `splitFactor` per date, listed names | not stated | not stated |
| EODHD £19.99 | Splits & Dividends API ✓ | `_old` tickers ✓ | not stated; a "Corporate Events Calendar API" is in the £99.99 ALL-IN-ONE — events, not terms |
| Norgate Platinum | applied as adjustments | ✓ | **"Norgate Data does not provide information about the reason for delisting or delisting return"**; on takeovers "there is no single value that could be supplied consistently" |
| Sharadar ACTIONS | ✓ per datasheet | ✓ | not verified |
| Massive paid | "Corporate Actions" listed | not stated | not stated |

**Answer.** Splits and dividends: yes, at $0 for listed names, with the
vendor's own dates. Delisting *dates*: EODHD, Norgate, Sharadar. **Delisting
returns and acquisition terms — the D9 term that Shumway (1997) shows is
where the bias lives — are supplied by no priced vendor.** Norgate says so in
writing and explains why.

**Consequence.** D9's series is either **hand-built from filings** (EDGAR
8-K and merger documents are free; the labour is not) or **declared** — a
Shumway-style convention recorded as a parameter with provenance, which is
exactly ADR-0034's discharge-in-configuration rule and exactly the kind of
assumption it warns about. This binds only where a universe contains
delistings, i.e. `cross_sectional`; it does not touch a currently-listed
deployment instrument (M0.7). Does not stop the project; keeps
`cross_sectional` at 0 for a third reason.

### M0.5 — Q10c: historical constituents and liquidity

| source | what | coverage | price (as displayed) | rights |
|---|---|---|---|---|
| Norgate Platinum / Diamond | daily true/false membership per stock for S&P 500/100/400/600, Russell 1000/2000/3000, NASDAQ-100, DJIA | Platinum back to 1990 | $630/yr | EULA as M0.3 |
| EODHD marketplace "S&P and Dow Jones Indices Historical Constituents" | S&P 500/100/400/600 and ~21 industry indices, 12 years; DJ indices 2 years; "direct contract with S&P Global" | 12 yrs | **£29.99/mo** promotional, separate from the £19.99 plan | not stated beyond the S&P contract |
| Sharadar SP500 table | additions and removals "since 1957" | 1957→ | on login | not verified |
| **LSEG, "FTSE 100 — Historic Additions and Deletions"** (PDF, August 2026, 19 pp) | every change since 1984-01-19 with `Date · Added · Deleted · Notes` | 1984→2026, **543 rows parsed** | **free** | "No part of this information may be reproduced … without prior written permission"; "Use and distribution of LSEG data requires a licence" — private research use is not licensed *explicitly* |
| **Wikipedia, "Historical components of the S&P 500"** | every change with `Date · Added · Removed · Reason`, citing S&P DJI announcement PDFs | 1963→ | free | CC BY-SA; unofficial; the cited S&P PDFs are the primary record and fetch freely (the S&P media-centre index returned 403 to a scripted fetch) |
| Liquidity | volume in every bar source above | — | included | — |

**Answer.** The *event* half — who left which index, when, and why — is free
for the two headline indices. The *daily point-in-time membership* half
across families is paid, and its cheapest form (EODHD, £29.99/mo) reaches
only 12 years. Liquidity comes with the bars.

**Consequence.** M0.19 is answered from the same fetch. The daily-membership
licence is a no-go inside the cap (M0.6); the event lists are enough for an
event study's *entries* but not for a universe. M0.20 supplies a different
free universe.

### M0.8 — Q6: TradingView tier for indicator alerts

**Answer**, rendered page, prices in GBP, annual billing, "Special price"
label as displayed 2026-09-10 — monthly billing was not displayed in the
extraction and is higher:

| plan | price | price alerts | **technical alerts** | webhooks |
|---|---|---|---|---|
| Basic | £0 | 3 | **0** | — |
| Essential | £12.95/mo | 20 | **20** | ✓ |
| Plus | £29.95/mo | 100 | 100 | ✓ |
| Premium | £59.95/mo | 400 | 400 | ✓ |
| Ultimate | £199.95/mo | 1,000 | 1,000 | ✓ |

A first automated extraction read Essential as 100 technical alerts; the
rendered page says 20. The rendered page is the record.

**Consequence.** Q6's blocker is confirmed — the free tier gives zero
indicator alerts. M11 needs Essential at minimum: **£155.40 over twelve
months**, which M0.14 shows does not fit the cap. Blocks M11 only.

### M0.9 — Q7: prior art (F15a)

Licence, last push and stars from the GitHub API, 2026-09-10. Nothing was
cloned. Reuse means *ideas*; no framework becomes a dependency — the vendored
donor core is the base (ADR record, TASKS M1).

| repository | licence | last push | ★ | verdict | reason |
|---|---|---|---|---|---|
| `mementum/backtrader` | GPL-3.0 | 2024-08-19 | 23.2k | **avoid** | dormant a year; GPL would bind any published derivative; third-party critiques of its fill model on thin names match A4's lesson |
| `stefan-jansen/zipline-reloaded` | Apache-2.0 | 2026-01-06 | 1.9k | **reuse ideas** | the best open treatment of splits, dividends and point-in-time bundles; too heavy as a dependency |
| `polakowo/vectorbt` | no SPDX (custom) | 2026-08-02 | 9.1k | **avoid** | open version in maintenance mode behind a paid PRO (third-party, ~$25/mo); licence not machine-readable |
| `nautechsystems/nautilus_trader` | LGPL-3.0 | 2026-09-10 | 28.7k | **ignore for v1** | multi-asset event-driven with a Rust core — far heavier than a daily-bar lab; no Trading 212 adapter |
| `kernc/backtesting.py` | AGPL-3.0 | 2026-08-05 | 9.0k | **avoid** | AGPL; single-instrument by design |
| `QuantConnect/Lean` | Apache-2.0 | 2026-09-09 | 21.6k | **reuse ideas** | fill and slippage models are worth reading; C#, cloud-shaped; no Trading 212 brokerage (M0.10) |
| `pst-group/pysystemtrade` | GPL-3.0 | 2026-07-18 | 3.5k | **reuse ideas** | Carver's cost "speed limit" and volatility targeting are the closest published relatives of M0.16; GPL |
| `microsoft/qlib` | MIT | 2026-09-02 | 48.5k | **ignore** | ML-factor platform; the wrong problem |
| `quantopian/alphalens` | Apache-2.0 | 2024-02-12 | 4.4k | **reuse ideas** | IC and breadth diagnostics (Grinold); dormant |
| `ranaroussi/quantstats` | Apache-2.0 | 2026-07-20 | 7.6k | **maybe reuse** | reporting only; not core |
| `freqtrade/freqtrade` | GPL-3.0 | 2026-09-10 | 54.2k | **ignore** | crypto; parked (C2) |
| `hudson-and-thames/mlfinlab` | no SPDX (proprietary) | 2023-10-02 | 4.9k | **avoid** | closed; the ideas are in López de Prado's book, already cited |

**Consequence.** No dependency changes. Two design relatives are named for
M5/M6 reading: pysystemtrade's cost speed limit (M0.16) and zipline-reloaded's
corporate-action semantics (M4 ports).

### M0.10 — F15b: solution landscape

**Starting point, the donor's `EVIDENCE.md` (2026-07-05).** Its landscape is
the prop-challenge funnel: 16.8 % of evaluation attempts pass, 33.3 % of
funded traders receive a payout in-window, so ~5.6 % of attempts end in a
paid trader; discipline is the survival variable and edge the qualification
variable; plain ORB "showed no tradeable edge after costs" in one quant
blog's backtests. What carries into this project is the method — verified
claims with dissent recorded — and the prior that a validated NO-GO is the
expected outcome.

**The retail research-platform landscape, 2026-09-10.**

| platform | shape | price (as found) | Trading 212 | pre-registration / alpha budget / null harness |
|---|---|---|---|---|
| QuantConnect | cloud IDE, Python/C#, backtest + paper + live | not displayed on quantconnect.com/pricing ("difficult to predict every use case"); a third party quotes $120/mo for live | **not among fourteen listed brokerages** | none |
| QuantRocket | Docker/Jupyter, Sharadar reseller, IB-centric | on login | no | none |
| Composer | no-code ETF rotation with execution | ~$19-29/mo (third party) | no | none |
| Tradetron | no-code strategy builder with copy-trading | $50/mo (third party) | no | none |
| Portfolio123, TrendSpider, Quant-Builder.ai, Backtrex | screeners / ML / no-code | various | no | none |
| TradingView | charting, Pine, alerts | M0.8 | no execution | none |

**Answer.** Every platform surveyed sells a backtest. **None sells a refusal.**
None pre-registers a floor, budgets alpha across a search, records what was
searched and refused, or runs a null through the same pipeline. And **none
integrates Trading 212**, so the venue adapter is bespoke by necessity, not
by preference — which is the strongest argument for keeping it thin (R1.7
first-class).

**Consequence.** The differentiation claim in the design stands on evidence:
the product is the discipline, not the engine. F15b closed.

### M0.12 — Q9: first live venue and its capability-evidence plan

Venue: Trading 212, Invest or Stocks ISA (the only API-enabled types).

| claim | source | verified how | when |
|---|---|---|---|
| Market, limit, stop, stop-limit orders | docs: `POST /api/v0/equity/orders/{market,limit,stop,stop_limit}` | place each type on the **demo** environment; archive request and response schemas | M10 |
| Paper environment exists and mirrors live paths | docs: `demo.trading212.com/api/v0` | first call; diff the two servers' OpenAPI documents (`api.json` / `api.yaml` download offered on the docs page) | M10 |
| Real fills are retrievable (ADR-0032) | docs: `/equity/history/orders`, `/transactions`, CSV `exports` | reconcile a hand-placed demo order against the export, field by field | M9 |
| Rate limits are per account, exposed in headers | docs: `x-ratelimit-limit/period/remaining/reset/used`; worked example "50 requests per 1 minute" | read the headers on every call; pin per-endpoint limits from the spec | M10 |
| Invest/ISA only; primary currency only; "Multi-currency accounts are not currently supported" | docs | a constraint, not a claim — design against it | now |
| "maximum of 50 pending orders allowed per ticker" | docs | constraint | now |
| Beta, "under active development" | docs | pin the OpenAPI document's hash; a changed hash halts the credentialed path until re-verified | M10 |
| Optional IP restriction on keys | docs | enable on the live key | M10 |
| Sell = negative quantity | docs: "you must provide a negative value for the quantity parameter" | a type-level rule in the adapter, tested | M10 |
| No market data | M0.1 | — | closed |

**Credentials.** Basic auth, `API_KEY:API_SECRET` Base64 — generated in-app
(help centre 14584770928157), held in Parameter Store or the local keychain,
never the repository (R5). The demo key is not the live key; the credentialed
path can run demo-only until a human performs `APPROVED -> LIVE`.

**Consequence.** No calibration campaign is needed for order *types*; one is
needed for *fill quality*, and ADR-0032's forward window is it. **CFDs are
outside the API entirely**, so any CFD path would be R1.7-manual only —
another reason M0.7 excludes them. Blocks M10 until the demo checks above
have run.

### M0.19 — index deletion events

| family | source | coverage | reason code | cost | rights |
|---|---|---|---|---|---|
| FTSE 100 | LSEG PDF "FTSE 100 — Historic Additions and Deletions", August 2026 | 1984-01-19 → 2026; 543 rows | `Notes`: "Corporate Event – …", "Fast Entry", or blank | free | LSEG reproduction notice (M0.5) |
| FTSE 250 / All-Share | quarterly review press releases, one per quarter | per release; no compiled history found | in text | free | same |
| S&P 500 | S&P DJI announcement PDFs (primary); Wikipedia compiled table (secondary) | 1963→ | `Reason` column | free | CC BY-SA (compiled); S&P PDFs public |
| S&P 400 / 600 | EODHD add-on (12 yrs) · Norgate Platinum · Sharadar | 12-35 yrs | membership only; reasons from announcements | £29.99/mo · $630/yr · on login | vendor |
| Russell 2000 | annual reconstitution lists | per year | rank-based | free | LSEG |

**The counts — the term M0.15 needs.** Method: FTSE rows dated 2015-2025
classified by the `Notes` text (a blank note read as a periodic-review
deletion — *a reading, not a published code*); S&P rows dated 2016-2025
classified by keyword over the `Reason` cell (acquired/merged → M&A;
bankruptcy/delisted → insolvency; spin-off/split; "market capitalization" /
"no longer representative" / moved to MidCap/SmallCap → index-rule).

| family | all deletions / yr | **index-rule deletions / yr** | M&A | insolvency | spin-off | other |
|---|---|---|---|---|---|---|
| FTSE 100, 2015-2025 | 10.5 | **~7.2** (unannotated) | 3.3 (annotated corporate events) | — | — | — |
| S&P 500, 2016-2025 | 21.3 | **8.1** | 10.0 | 0.4 | 1.2 | 1.6 (name/ticker changes) |

**Answer.** The narrow ask is free for the two headline indices, with reasons,
and back to 1984 and 1963. The count is the problem: **about fifteen
index-rule deletions a year across both**, arriving on roughly four review
dates.

**Consequence.** M0.15 below: at ~15 events a year over 26 years and a 40 %
measurement partition, `N_eff` is ~125 at `rho = 0.3` against 714 required at
a 0.15R floor. **DRAFT-001 is deferred on evidence, not only on money.** The
families that would fix the count (S&P 400/600, FTSE 250) have paid
membership data and unpriced deletion counts. `cross_sectional` does not
reopen by this route.

### M0.20 — EDGAR 13F coverage and rights

- **Structured history.** "The EDGAR Form 13F Data Set consists of XML data
  submitted from MAY 2013 through current period" (form_13f_readme.pdf,
  extracted 2026-09-10); the page states "July 2013 - May 2026" and quarterly
  updates. Text-format 13F-HR filings precede it on EDGAR — Berkshire's
  submissions index reaches 1998-08-10 (an example, not a coverage claim).
- **As-filed vs amendment.** `SUBMISSIONTYPE ∈ {13F-HR, 13F-HR/A, 13F-NT,
  13F-NT/A}`; `COVERPAGE` carries `ISAMENDMENT`, `AMENDMENTNO` and
  `AMENDMENTTYPE` — "a restatement or adds new holdings entries". Originals
  and restatements are separable mechanically. ✓
- **Acceptance timestamp.** The data sets carry `FILING_DATE` (date only).
  The submissions API carries `acceptanceDateTime` per filing — verified
  2026-09-10 on one CIK: `13F-HR · filingDate 2026-08-14 ·
  acceptanceDateTime 2026-08-14T20:05:04.000Z · reportDate 2026-06-30`. ✓
  DRAFT-002's entry instant exists.
- **Bulk access.** Quarterly data-set zips; `submissions.zip` "updated and
  republished nightly at approximately 3:00 a.m. ET"; `full-index` and
  `daily-index`; "Current max request rate: 10 requests/second"; a declared
  `User-Agent` of the form "Sample Company Name AdminContact@<domain>.com";
  no authentication; "please use efficient scripting … download only what
  you need"; no technical support. **The one verification request in this
  run used a generic `User-Agent` without a contact address**, which is not
  the form the SEC asks for. A production script must carry a contact; whose
  is the author's decision, since it is personal data.
- **Rights.** US government data; the page's only caveat is that the data
  sets are "not a substitute for such filings". No redistribution restriction
  stated.
- **The constituent question — yes.** A universe defined as *names appearing
  in `INFOTABLE` for period P* is point-in-time by construction, free, from
  2013 Q2, with three caveats: long positions only; 13F-eligible securities
  only; keyed by CUSIP, so delisted names need a CUSIP→ticker map that no free
  source was verified to supply. **The expensive half stays expensive**: the
  prices of names that later delisted are Tiingo-unstated and EODHD £19.99.
- **Delisted coverage — probed 2026-09-12 (M12.1b), no longer unstated.**
  Three names known to have delisted were requested through
  `python -m occams ingest` for 1993-01-01 → 2026-09-12, three of the
  month's 500 symbols, $0. **FRC** (delisted 2023-05): HTTP 404, the
  vendor's words *"Ticker 'FRC' not found"*. **BBBY** (delisted 2023-05):
  HTTP 200 and no rows — the symbol is known, its history is not served.
  **SHLD** (the company traded under it 2005-03 → 2018-10): 752 bars from
  2023-09-13 with six semi-annual distributions — the symbol's *current*
  holder, a fund listed in 2023-09, not the company; the vendor served the
  reassigned symbol's new instrument with no sign that the old one existed.
  **Finding: Tiingo Starter does not serve the price history of delisted
  names, and a reassigned symbol silently serves its new holder.**
  Survivorship cannot be removed at $0 and stays a named bias on every
  single-name universe; M12.1c (point-in-time membership) cannot be done
  from this source and is closed. Any delisted-capable source bought later
  must be keyed by an instrument identity, not a symbol — the same
  identity map the 13F path above needs, in the other direction. The 752
  SHLD bars are in the local archive under that symbol and belong to no
  declared universe.
- **Close-only prints — observed 2026-09-12 (M12.3).** A census of the four
  declared universes' definition partitions for bars with no printed range
  (open = high = low) or no volume: index_etfs 0; sector_etfs 3 (XLB
  1998-12-29 and 1999-02-26, XLI 1999-01-26); dow_30 9 across seven names;
  **sp_100 319, of which C carries 254 — every bar of 1996** with real
  volume and a different close each day but open, high and low collapsed
  onto the close. A source defect in the early history of some names, not
  halts. The lab's fill auditor (M5.5) refuses a fill on such a bar, which
  is right; what it costs is recorded in the M12.3 status log.

**Consequence.** DRAFT-002 is registrable in *data* terms and **underpowered
in trade terms** (M0.15). M0.5's constituent half is answered at $0 for a
13F-defined universe; `cross_sectional` still does not reopen, because
membership is not the binding constraint — sample size is.

---

## Stage 2 — derived

### M0.6 — data subtotal against $21.91

| path | lines | subtotal | fits $21.91 | every required use permitted or fallback named |
|---|---|---|---|---|
| **$0** | Tiingo Starter (US-listed, raw + adjusted + div/split) · EDGAR · FTSE 100 PDF · S&P 500 compiled list | **$0** | **yes** | retention ✓ · internal reproduction ✓ · raw redistribution ✗ → synthetic fixtures (D12) · derived publication: not addressed by Tiingo → **ask before publishing** · fixtures ✓ |
| cheapest LSE-inclusive with delisted | EODHD £19.99/mo | £239.88/yr | **no** — one month exceeds $21.91 at any GBPUSD rate above 1.10 | rights as M0.3 |
| survivorship-complete US | Norgate Platinum $630/yr | $630 | **no** | rights as M0.3, **and see the D12 conflict** |
| daily membership add-on | EODHD £29.99/mo | £359.88/yr | no | — |

**Go/no-go: go, at $0, on US-listed names via Tiingo Starter**, with three
declared limits carried into M0.7 and M0.15: **(1)** delisted coverage is
unstated, so nothing here lifts survivorship for a universe — `cross_sectional`
is untouched; **(2)** 500 unique symbols a month bounds the tradeable list
at tens of names, not a Russell; **(3)** internal use only — publication of
raw-derived artefacts waits on a written answer from the vendor.

> *2026-09-12 (M12.1b):* limit **(1)** is now measured, not unstated — the
> source does not serve delisted history, and a reassigned symbol serves
> its new holder; see the M0.3 observation. Survivorship stays named.

**Finding for any future purchase.** Norgate's EULA requires deleting all
Content at expiry. D12 stores bars content-addressed and immutable so that a
run reproduces forever. **The two are incompatible unless the subscription is
perpetual**; a lapsed Norgate subscription would make every archived run
legally irreproducible, which is the failure D12 exists to prevent. EODHD's
terms do not address retention after cancellation — to be asked before
purchase.

**Gap closed.** ADR-0028's replacement class (FX pairs, index CFDs) had no
priced data line. EODHD's "All World" plan covers FX and indices at the same
£19.99; Tiingo offers FX endpoints whose free-tier terms were not verified.
Moot for M0.7, which does not choose that class.

### M0.16 — break-even cost ratio and the admissible stop band

`cost_in_R = c / s` — round-trip cost as a fraction of notional over stop
distance as a fraction of price. Net EV per trade in R is gross EV minus
`c/s`. **Break-even** is `c/s = gross EV`. The EV half of a declared floor
`f` holds only if gross EV ≥ `f + c/s`; since gross EV is unknown before
measuring, the on-paper band uses **a declared convention: cost no larger
than the floor itself**, `c/s ≤ f`, so gross must be at least `2f`. That is a
convention, recorded as one.

**`c/s` by class and stop** (`c` = `c_fixed` + one full spread crossed per
round trip; spreads are the M0.2 declared ranges):

| class | spread | `c` | s=1 % | s=2 % | s=3 % | s=5 % | s=10 % |
|---|---|---|---|---|---|---|---|
| UK share, GBP account | 0.10 % | 0.60 % | 0.60R | 0.30R | 0.20R | 0.12R | 0.06R |
| UK share, GBP account | 0.30 % | 0.80 % | 0.80R | 0.40R | 0.27R | 0.16R | 0.08R |
| UK share, GBP account | 1.00 % | 1.50 % | 1.50R | 0.75R | 0.50R | 0.30R | 0.15R |
| US name, GBP account | 0.02 % | 0.32 % | 0.32R | 0.16R | 0.11R | 0.06R | 0.03R |
| US name, GBP account | 0.10 % | 0.40 % | 0.40R | 0.20R | 0.13R | 0.08R | 0.04R |
| US name, GBP account | 0.50 % | 0.80 % | 0.80R | 0.40R | 0.27R | 0.16R | 0.08R |
| US name, USD account | 0.02 % | 0.02 % | 0.02R | 0.01R | 0.01R | 0.00R | 0.00R |
| US name, USD account | 0.10 % | 0.10 % | 0.10R | 0.05R | 0.03R | 0.02R | 0.01R |
| US name, USD account | 0.50 % | 0.50 % | 0.50R | 0.25R | 0.17R | 0.10R | 0.05R |
| LSE GBP ETF, GBP account | 0.05 % | 0.05 % | 0.05R | 0.03R | 0.02R | 0.01R | 0.01R |
| LSE GBP ETF, GBP account | 0.20 % | 0.20 % | 0.20R | 0.10R | 0.07R | 0.04R | 0.02R |

**Minimum stop `s_min = c / f`** at which cost equals the floor:

| class | `c` | f=0.10R | f=0.15R | f=0.20R | f=0.25R |
|---|---|---|---|---|---|
| UK share, GBP account | 0.60-1.50 % | 6.0-15.0 % | **4.0-10.0 %** | 3.0-7.5 % | 2.4-6.0 % |
| US name, GBP account | 0.32-0.80 % | 3.2-8.0 % | **2.1-5.3 %** | 1.6-4.0 % | 1.3-3.2 % |
| US name, USD account | 0.02-0.50 % | 0.2-5.0 % | **0.1-3.3 %** | 0.1-2.5 % | 0.1-2.0 % |
| LSE GBP ETF, GBP account | 0.05-0.20 % | 0.5-2.0 % | **0.3-1.3 %** | 0.2-1.0 % | 0.2-0.8 % |

**The frequency half.** For a driftless walk with symmetric barriers at ±`s`
and daily volatility `σ_d`, expected time to resolve is `E[T] ≈ (s/σ_d)²`
days, so **trades per year per instrument ≤ 252 · (σ_d/s)²** — an
always-in-position upper bound, not a forecast:

| `σ_d` | s=2 % | s=3 % | s=5 % | s=10 % |
|---|---|---|---|---|
| 1 % | 63 | 28 | 10 | 3 |
| 2 % | 252 | 112 | 40 | 10 |
| 3 % | 567 | 252 | 91 | 23 |

**The band.** Both halves hold at once only where
`c/f ≤ s ≤ σ_d · √(252·n / F)` for `n` instruments and a frequency floor `F`
per year. Read off: a UK single name in a GBP account at `f = 0.15R` needs
`s ≥ 4 %`; at `σ_d = 1 %` that caps one instrument at ~16 trades a year, so a
frequency floor of 100/yr needs seven or more such names held in parallel —
and then `rho` across them bites (M0.15). A US ETF in a GBP account needs
`s ≥ 2.1-2.7 %` and gives ~28-57 trades a year per instrument at `σ_d = 1 %`.
In a USD account the cost half nearly vanishes and the band is set by the
frequency half alone.

**Excluded before M0.7 selects:** UK single names below a 4 % stop; any
FX-paying class below a ~2 % stop; CFDs (M0.2, unpriceable); intraday
(parked). **Declared parameters:** the spread ranges (M0.2), `σ_d` ∈ {1, 2,
3} %, the cost-equals-floor convention. **The account currency moves `c` by
0.30 % per round trip on US names, which at a 2 % stop is 0.15R — the whole
floor.** That is an M0.13 fact, recorded for the author, not a recommendation.

### M0.7 — Q3: instruments, currencies, and the four-way position

**Instruments (help centre 11717160183197, 2026-09-10).** Invest / Stocks
ISA: "Ordinary shares, Preferred shares, Exchange-traded funds (ETFs),
Exchange-traded products (ETPs), Exchange-traded commodities (ETCs), Real
Estate Investment trusts (REITs), Investment Trusts" — third parties count
~16 exchanges and ~11,000 instruments including LSE, NYSE, NASDAQ, Xetra and
Euronext (the venue's page gives no count). CFD: "FOREX, Stocks, ETFs, Index
futures, Commodity futures, FOREX futures, Treasury futures,
Cryptocurrencies" — not API-enabled (M0.1). **Currencies:** the listing
currency per instrument (GBP/GBX, USD, EUR); one primary account currency,
which is R9's `currency` and the author's (M0.13); the API trades only in it.

**The chosen class: currently-listed, liquid US-listed ETFs and large-cap
shares, daily bars, held for days.** Its four-way position:

| axis | what it gives up | why that is the right thing to give up |
|---|---|---|
| **Capacity** (the only structural retail edge) | **All of it.** Large liquid names are exactly where funds already are | `cross_sectional` is at 0 (ADR-0028) and M0.15 shows it stays there on sample size as well as money. v1's job is an apparatus and a verdict, not the edge; ADR-0028 rejected "build the machinery and measure nothing" |
| **`cost_in_R`** | Nothing — the best available: `c` ≈ 0.02-0.40 % by account currency, `s_min` 0.1-2.7 % at a 0.15R floor | — |
| **Sample size** | Nothing on count — tens of names trading daily give thousands of trades on paper. **The binding limit becomes `rho` across concurrent positions**, measured on the definition period | Honest: the risk moves from "not enough trades" to "not enough independent trades", which M0.15 now states |
| **Data affordability** | Nothing — $0 (M0.6). Dividends and splits are in the same row as the bar (`divCash`, `splitFactor`) | The class keeps **one declared bias: the instrument's own survival.** A currently-listed deployment instrument is measured on itself, not selected from a universe, so ADR-0025's objection to declared survivorship applies to *selection* hypotheses only. Mechanism hypotheses on this class are about the instrument's dynamics (`regime`, `price_daily`) — ADR-0028's two runnable axes |

**Alternatives and why not.** *LSE-listed GBP ETFs in a GBP account* have the
lowest per-trade cost of any class (no SDRT, no FX, spread 0.05-0.20 %) but
no $0 data source — Tiingo does not cover the LSE; EODHD is £19.99/mo. *UK
single names*: SDRT alone is 0.5 % per round trip. *EU names*: FX plus FTT.
*CFDs*: unpriceable and outside the API. *Small caps*: the capacity edge
lives there, but it needs the universe data and the sample the lab cannot
yet afford.

**What this leaves the author.** The class is fixed; **the FX term is 0 or
0.30 % per round trip by the M0.13 currency choice**, and the trade-off is
recorded above without a recommendation.

### M0.15 — statistical affordability, on paper

`N = ((z_α + z_β) · σ / f)²`, α = 0.05 two-sided, Bonferroni over
`search_space_size = k`, power 80 % (`z_β = 0.842`). **Declared:** `σ` ∈
[1.0, 1.5] R — provenance: a fixed-stop system bounds losses near −1R and
leaves a right tail; DRAFT-001's provisional 1.2R sits inside; the
definition-period measurement supersedes. `rho` ∈ [0.1, 0.5]. Measurement
partition `p` = 0.4 of the archive, declared range 0.3-0.5 (D11's split is
configuration). The go/no-go must hold across the whole range.

**Required N:**

| floor | σ | k=1 | k=4 | k=8 | k=16 | k=4 @ 90 % |
|---|---|---|---|---|---|---|
| 0.10R | 1.0 | 785 | 1,115 | 1,279 | 1,442 | 1,428 |
| 0.10R | 1.5 | 1,766 | 2,509 | 2,877 | 3,244 | 3,214 |
| 0.15R | 1.0 | 349 | 496 | 568 | 641 | 635 |
| 0.15R | 1.2 | 502 | **714** | **818** | 923 | 914 |
| 0.15R | 1.5 | 785 | 1,115 | 1,279 | 1,442 | 1,428 |
| 0.20R | 1.2 | 283 | 401 | 460 | 519 | 514 |
| 0.25R | 1.0 | 126 | 178 | 205 | 231 | 229 |
| 0.25R | 1.2 | 181 | **257** | 295 | 332 | 329 |
| 0.25R | 1.5 | 283 | 401 | 460 | 519 | 514 |

**Available N, measurement partition only.** Event studies cluster on ~4
dates a year; `N_eff = k / (1 + (k−1)·rho)` per date.

| axis / event set | events or trades | years | raw N (p=0.4) | `N_eff` rho=0.1 | rho=0.3 | rho=0.5 |
|---|---|---|---|---|---|---|
| FTSE 100 index-rule deletions | 7.2/yr | 26 | 75 | 69 | 60 | 53 |
| S&P 500 index-rule deletions | 8.1/yr | 26 | 84 | 76 | 64 | 55 |
| **both, DRAFT-001** | ~15/yr | 26 | ~160 | ~145 | **~125** | ~108 |
| DRAFT-002, 20 filers | 4 dates/yr | 13 | 416 | 143 | 62 | 40 |
| DRAFT-002, 50 filers | 4 dates/yr | 13 | 1,040 | 176 | 66 | 41 |
| DRAFT-002, 100 filers | 4 dates/yr | 13 | 2,080 | 191 | 68 | 41 |
| `price_daily` / `regime`, 10 names, 25 trades/yr bound | — | 20 | 2,000 | not calendar-clustered; concurrency `rho` applies where holds overlap | | |
| `price_daily` / `regime`, 50 names, 63 trades/yr bound | — | 20 | 25,200 | same | | |

**Go/no-go.**

- **`price_daily` and `regime` on the M0.7 class: go on paper.** Raw N of
  1,000-25,000 against 496-1,442 required at a 0.15R floor holds across the
  σ range at k ≤ 16. **Conditional:** if a strategy holds many names at once,
  `rho` across them can collapse `N_eff` by an order of magnitude (fifty
  names at `rho = 0.5` on one date are two observations). The condition is
  measured on the definition period and re-checked at M8.2, which refuses if
  it fails.
- **`cross_sectional`, DRAFT-001: no-go at any floor ≤ 0.25R.** ~125
  effective observations against 257 (0.25R, σ=1.2, k=4) and 714 (0.15R).
  Consistent with ADR-0028 from an independent direction. Reopens only with
  the mid- and small-cap families, which are paid.
- **DRAFT-002: no-go.** 40-190 effective against 818 (0.15R, σ=1.2, k=8).
  Opens only if `rho` across filers is near zero, which is a measurement,
  not an assumption.

**Consequence.** DESIGN-v4 §10's rule holds before anything is built: a
sample problem found now is a refusal now. M8.2 keeps the same refusal at
registration. The two Drafts stay Drafts.

### M0.17 — execution host: does the R1.7 default build need one?

**Finding: no.** R1.4 (unreconciled `ORDER_INTENT` at startup), R1.5
(heartbeat-timeout kill path) and R1.6 (reconcile each heartbeat) are
properties of a process that holds broker credentials and a live position
book. The default build holds neither: its one scheduled act is producing a
Telegram proposal card after the daily bar closes, and a missed run is a
missed proposal — safe by construction ("halting is free; resuming is not").
ADR-0030's argument that "a missed run and a dead host are indistinguishable"
is correct and applies to the credentialed path only.

**What the default build needs.** The research host (the author's machine,
N2, $0); a Telegram bot token — **a credential under R5, kept in Parameter
Store or the local keychain and never the repository**, but not a *broker*
credential. R1.7's "the only mode needing no credentials" is read here as
*no broker credentials*; the reading is recorded so it can be corrected.
Telegram's Bot API fee was not consulted this run and is carried at $0
pending M11.

**Recurring cost: $0**, plus the existing S3 bucket `occams-research`
(~$0.09/mo, KEEP, already recurring). **The credentialed path (M10) will
need ADR-0030's always-on process.** It is not priced here, by the task's own
rescope, and M0.14 records it as a line outside the cap by construction.
That path also inherits the API's limits: beta, Invest/ISA only, one
currency.

---

## Stage 3 — M0.14: whole-programme affordability

| line | one-off | recurring | 12-month | provenance |
|---|---|---|---|---|
| Prior spend | $128.09 | — | $128.09 | TASKS §Inherited state |
| Data — Tiingo Starter | $0 | $0 | $0 | M0.3, M0.6 |
| EDGAR · FTSE 100 PDF · S&P 500 compiled list | $0 | $0 | $0 | M0.19, M0.20 |
| Execution host — default build | $0 | $0 | $0 | M0.17 |
| S3 `occams-research` (KEEP) | — | ~$0.09/mo | ~$1.08 | TASKS §Inherited state |
| Telegram Bot API | $0 | $0 | $0 | not consulted this run; carried at $0 |
| Per-trade costs (fees, FX, SDRT, spread) | — | per trade | — | **money, not cap** — R9, M0.13 |
| Contingency | — | — | — | **the author's**; $20.83 of headroom exists and is not allocated here |
| **Subtotal, M1-M10 default build** | | | **$129.17** | **≤ $150 — go** |
| TradingView Essential (M11 only) | — | £12.95/mo (annual billing) | £155.40 | M0.8 |
| **Subtotal with M11 as designed** | | | $129.17 + £155.40 | **exceeds $150 at any GBPUSD rate — no-go inside the cap** |
| Execution host — credentialed path (M10) | — | unpriced | — | ADR-0030; outside the cap by construction |
| AWS account cleanup ($8.72 of $10.50, SignalFlow/FitnessCore) | — | — | — | separate brief; **not folded in** (TASKS §Explicitly parked) |

**Decision recorded.**

1. **Go for M1-M10 on the R1.7 default build**, time-bounded twelve months
   from 2026-09-10, at **$129.17 against $150**, arithmetic above. **M1 is
   unblocked.**
2. **No-go, inside the current cap, for M11's TradingView dependency.** Two
   months of the cheapest tier with technical alerts exceed the remaining
   $21.91. Resolving this is either a cap decision (the author's, R9
   reasoning) or a design change — an alerting path for Pine that does not
   need TradingView, or M11 without Pine — which needs an ADR and is not made
   here.
3. **No-go, inside the current cap, for the credentialed execution path**, on
   the same reasoning: ADR-0030's host is recurring and the cap does not
   reset. It gates `APPROVED -> LIVE` automation only; R1.7 remains
   first-class and sufficient for a verdict and for real money placed by hand.
4. **`cross_sectional` does not reopen at M0.14.** ADR-0028's amendment
   named it first to reconsider "if M0.14 leaves room"; $20.83 of room does
   not buy the data, and M0.15 shows the data would not buy the sample.

---

## What stops, what remains, what the author decides

**Stops: none.** M0.3 found a $0 source; M0.4's gap binds only
`cross_sectional`; M0.5 has free events and paid membership; M0.6 is a go at
$0; M0.15 is a go for the two runnable axes; M0.14 is a go for M1-M10.

**Surfaced for the author — decisions, not numbers picked here:**

- **M0.13 currency.** 0 or 0.30 % per round trip on the chosen class (M0.16).
- **The M11 cap question** and **the credentialed-path cap question** (M0.14).
- **The M0.7 class** — derived, and confirmable or overridable like an ADR.
- **The R1.7 reading** — "no credentials" as "no broker credentials" (M0.17).
- **EDGAR contact** in the `User-Agent` (M0.20).
- **Two vendor asks, both optional for the go path:** Tiingo, in writing, on
  publishing derived artefacts; Sharadar pricing, which needs a login.

**Stage 4, untouched:** M0.11, M0.13, M0.18. They gate M6, not M1.

**Two disciplines confirmed by this run rather than assumed.** The spread
must be measured, not declared, before M5 closes. And every price in this
file is dated; a price without an access date is a price without provenance.
