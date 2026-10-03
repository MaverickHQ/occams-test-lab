# Readiness under the fifth check — grid-002 seed 20260920

**Dated 2026-09-20. Zero alpha; the definition partition only (D13); nothing here is a verdict.** Survey record #9, 38,976 cells screened, results `f5b7a3470c77`; always-long re-run now on engine `795472e4a03209a2` (the survey's screen was `795472e4a03209a2`); 4,000 draws, seed 20260920. *Fifth check* is ADR-0043's test as the guard would apply it here: the cell's EV against a Monte Carlo of always-long at the same geometry and gate, at the axis's corrected alpha. *Margin by era* is the cell's EV less always-long's in each third of the definition partition, oldest first — the survey's tiers pooled these.

**Measured priors** — every question registered from a survey and resolved, screen beside measurement (M12.6), this programme's and the earlier programmes' read-only:

- `Q2-001` (programme-2.jsonl) from cell `f2199b5b297d85bb`: definition margin +0.239 → measured margin -0.001 (Δ -0.240); EV +0.256 → +0.213.
- `Q2-002` (programme-2.jsonl) from cell `f8500a69db544a3c`: definition margin +0.201 → measured margin +0.075 (Δ -0.127); EV +0.333 → +0.109.

| # | Cell | Universe | Tier | EV | Always-long, survey → now | Margin now | p vs α | Fifth check | Margin by era | Sweep · alpha |
|---:|---|---|---|---:|---|---:|---|---|---|---|
| 1 | `5da80c610ab6da80` | dow_30 | held | +0.296 | -0.075 → -0.075 | +0.371 | 0.0000 vs 0.01 | **pass** | +0.344 / +0.367 / +0.408 | 30 · 0.3 |
| 2 | `151ea6728ab85559` | index_etfs | held | +0.233 | -0.108 → -0.108 | +0.341 | 0.0000 vs 0.01 | **pass** | +0.173 / +0.327 / +0.422 | 30 · 0.3 |
| 3 | `2f89cd3fc3abbd83` | sp_100 | held | +0.230 | -0.085 → -0.085 | +0.315 | 0.0000 vs 0.01 | **pass** | +0.341 / +0.287 / +0.331 | 30 · 0.3 |
| 4 | `5834abf51248fbb5` | index_etfs | held | +0.211 | -0.098 → -0.098 | +0.309 | 0.0000 vs 0.01 | **pass** | +0.173 / +0.336 / +0.361 | 15 · 0.15 |
| 5 | `42f89ac43ea32bac` | dow_30 | held | +0.274 | +0.004 → +0.004 | +0.270 | 0.0000 vs 0.01 | **pass** | +0.204 / +0.489 / +0.181 | 30 · 0.3 |
| 6 | `71a0d8161a682950` | sp_100 | held | +0.173 | -0.093 → -0.093 | +0.266 | 0.0000 vs 0.01 | **pass** | +0.336 / +0.262 / +0.250 | 30 · 0.3 |
| 7 | `8e17b913b3c624f2` | index_etfs | held | +0.147 | -0.119 → -0.119 | +0.265 | 0.0000 vs 0.01 | **pass** | +0.022 / +0.354 / +0.289 | 30 · 0.3 |
| 8 | `0dc23760a36e1a1b` | sp_100 | held | +0.175 | -0.085 → -0.085 | +0.260 | 0.0000 vs 0.01 | **pass** | +0.328 / +0.230 / +0.250 | 30 · 0.3 |
| 9 | `83acca56f082d646` | dow_30 | held | +0.168 | -0.087 → -0.087 | +0.254 | 0.0000 vs 0.01 | **pass** | +0.296 / +0.269 / +0.250 | 30 · 0.3 |
| 10 | `9ed03d49b0d204e4` | sp_100 | held | +0.154 | -0.093 → -0.093 | +0.247 | 0.0000 vs 0.01 | **pass** | +0.304 / +0.229 / +0.230 | 30 · 0.3 |
| 11 | `9c62b6cd8da2bbb3` | sp_100 | held | +0.233 | -0.010 → -0.010 | +0.243 | 0.0000 vs 0.01 | **pass** | +0.122 / +0.492 / +0.154 | 30 · 0.3 |
| 12 | `f2199b5b297d85bb` | sp_100 | held | +0.255 | +0.016 → +0.016 | +0.238 | 0.0000 vs 0.01 | **pass** | +0.179 / +0.335 / +0.165 | 15 · 0.15 |
| 13 | `5d78cf45a8e7aa9a` | sp_100 | held | +0.217 | -0.020 → -0.020 | +0.237 | 0.0000 vs 0.01 | **pass** | +0.190 / +0.388 / +0.186 | 30 · 0.3 |
| 14 | `8373d84db5ffd36b` | dow_30 | held | +0.153 | -0.075 → -0.075 | +0.228 | 0.0000 vs 0.01 | **pass** | +0.208 / +0.223 / +0.262 | 30 · 0.3 |
| 15 | `e02384ae41677547` | sector_etfs | held | +0.216 | -0.010 → -0.010 | +0.226 | 0.0003 vs 0.01 | **pass** | +0.119 / +0.395 / +0.115 | 15 · 0.15 |
| 16 | `f9d09f4299ed5aa7` | sp_100 | held | +0.236 | +0.011 → +0.011 | +0.225 | 0.0000 vs 0.01 | **pass** | +0.214 / +0.284 / +0.145 | 30 · 0.3 |
| 17 | `69ecf3439041f4eb` | sp_100 | held | +0.099 | -0.118 → -0.118 | +0.218 | 0.0000 vs 0.01 | **pass** | +0.318 / +0.146 / +0.217 | 30 · 0.3 |
| 18 | `4d1eee50721ff72a` | sector_etfs | held | +0.203 | -0.014 → -0.014 | +0.217 | 0.0000 vs 0.01 | **pass** | +0.087 / +0.372 / +0.123 | 30 · 0.3 |
| 19 | `5193d48bac341ff2` | index_etfs | held | +0.180 | -0.037 → -0.037 | +0.217 | 0.0000 vs 0.01 | **pass** | +0.263 / +0.349 / +0.166 | 30 · 0.3 |
| 20 | `387611fc36db0b29` | dow_30 | held | +0.111 | -0.105 → -0.105 | +0.216 | 0.0000 vs 0.01 | **pass** | +0.308 / +0.172 / +0.210 | 30 · 0.3 |

20 of 20 candidates pass the fifth check on the definition partition; 0 of 20 have no margin over always-long in the latest definition era. A pass here is the gate shown passable before alpha moves, not a verdict; the measurement partition decides, once, at registration's cost. Registration is the author's `--yes`.
