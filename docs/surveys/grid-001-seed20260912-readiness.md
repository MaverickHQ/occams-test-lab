# Readiness under the fifth check — grid-001 seed 20260912

**Dated 2026-09-18. Zero alpha; the definition partition only (D13); nothing here is a verdict.** Survey record #9, 38,976 cells screened, results `80f551b4de5c`; always-long re-run now on engine `42d88a252ed70c61` (the survey's screen was unstamped: the box ran before the stamp existed); 4,000 draws, seed 20260912. *Fifth check* is ADR-0043's test as the guard would apply it here: the cell's EV against a Monte Carlo of always-long at the same geometry and gate, at the axis's corrected alpha. *Margin by era* is the cell's EV less always-long's in each third of the definition partition, oldest first — the survey's tiers pooled these.

**Restated 2026-10-03 (M16.8, ADR-0048 §4).** The *p vs α* column is counted plus one — (draws at or above the cell's EV + 1) / (draws + 1) — from the same 4,000 draws; no cell was re-run and no result changed. As first committed the column printed `0.0000` where no draw reached the cell: a Monte Carlo p is never zero, and none is printed as zero.

**Measured priors** — every question registered from a survey and resolved, screen beside measurement (M12.6):

- `Q2-001` from cell `f2199b5b297d85bb`: definition margin +0.239 → measured margin -0.001 (Δ -0.240); EV +0.256 → +0.213.

| # | Cell | Universe | Tier | EV | Always-long, survey → now | Margin now | p vs α | Fifth check | Margin by era | Sweep · alpha |
|---:|---|---|---|---:|---|---:|---|---|---|---|
| 1 | `f2199b5b297d85bb` | sp_100 | held | +0.256 | +0.017 → +0.016 | +0.239 | 0.0002 vs 0.01 | **pass** | +0.186 / +0.331 / +0.169 | 15 · 0.15 |
| 2 | `e02384ae41677547` | sector_etfs | held | +0.216 | -0.010 → -0.010 | +0.226 | 0.0002 vs 0.01 | **pass** | +0.119 / +0.395 / +0.115 | 15 · 0.15 |
| 3 | `f9d09f4299ed5aa7` | sp_100 | held | +0.236 | +0.012 → +0.011 | +0.225 | 0.0002 vs 0.01 | **pass** | +0.216 / +0.284 / +0.144 | 30 · 0.3 |
| 4 | `4d1eee50721ff72a` | sector_etfs | held | +0.203 | -0.014 → -0.014 | +0.217 | 0.0002 vs 0.01 | **pass** | +0.087 / +0.372 / +0.123 | 30 · 0.3 |
| 5 | `5193d48bac341ff2` | index_etfs | held | +0.180 | -0.037 → -0.037 | +0.217 | 0.0002 vs 0.01 | **pass** | +0.263 / +0.349 / +0.166 | 30 · 0.3 |
| 6 | `3fff965a58639eae` | dow_30 | held | +0.128 | -0.087 → -0.087 | +0.215 | 0.0002 vs 0.01 | **pass** | +0.253 / +0.223 / +0.171 | 30 · 0.3 |
| 7 | `89200ec086be73e6` | index_etfs | held | +0.128 | -0.085 → -0.085 | +0.213 | 0.0002 vs 0.01 | **pass** | +0.440 / +0.373 / +0.231 | 15 · 0.15 |
| 8 | `4f0326e3644df864` | dow_30 | held | +0.184 | -0.027 → -0.027 | +0.211 | 0.0002 vs 0.01 | **pass** | +0.218 / +0.100 / +0.262 | 30 · 0.3 |
| 9 | `c00c0c7e6fe3d5fb` | sp_100 | held | +0.156 | -0.054 → -0.054 | +0.211 | 0.0002 vs 0.01 | **pass** | +0.269 / +0.267 / +0.137 | 30 · 0.3 |
| 10 | `78e13cce5e21fb83` | index_etfs | held | +0.168 | -0.039 → -0.039 | +0.207 | 0.0002 vs 0.01 | **pass** | +0.263 / +0.349 / +0.151 | 15 · 0.15 |
| 11 | `bb3394ed0820ae72` | sp_100 | held | +0.185 | -0.021 → -0.020 | +0.205 | 0.0002 vs 0.01 | **pass** | +0.133 / +0.220 / +0.242 | 30 · 0.3 |
| 12 | `7ac7bd72aaa1e5f4` | sp_100 | held | +0.248 | +0.044 → +0.045 | +0.203 | 0.0002 vs 0.01 | **pass** | +0.160 / +0.281 / +0.186 | 15 · 0.15 |
| 13 | `8835b76f08d63847` | index_etfs | held | +0.168 | -0.035 → -0.035 | +0.203 | 0.0002 vs 0.01 | **pass** | +0.691 / +0.319 / +0.284 | 30 · 0.3 |
| 14 | `f8500a69db544a3c` | sp_100 | held | +0.333 | +0.132 → +0.132 | +0.201 | 0.0002 vs 0.01 | **pass** | +0.077 / +0.319 / +0.194 | 15 · 0.15 |
| 15 | `719063aad2318c00` | sector_etfs | held | +0.231 | +0.032 → +0.032 | +0.199 | 0.0002 vs 0.01 | **pass** | +0.042 / +0.295 / +0.178 | 30 · 0.3 |
| 16 | `7d8f04aa2066452a` | dow_30 | held | +0.202 | +0.005 → +0.005 | +0.196 | 0.0002 vs 0.01 | **pass** | +0.228 / +0.239 / +0.150 | 15 · 0.15 |
| 17 | `6fe5444b518075b9` | dow_30 | held | +0.175 | -0.012 → -0.012 | +0.188 | 0.0002 vs 0.01 | **pass** | +0.233 / +0.162 / +0.184 | 30 · 0.3 |
| 18 | `64d656ca7e638722` | sector_etfs | held | +0.206 | +0.019 → +0.019 | +0.187 | 0.0002 vs 0.01 | **pass** | +0.000 / +0.279 / +0.200 | 15 · 0.15 |
| 19 | `edcf23b4b5e9b4f6` | dow_30 | held | +0.106 | -0.076 → -0.074 | +0.181 | 0.0002 vs 0.01 | **pass** | +0.126 / +0.061 / +0.209 | 30 · 0.3 |
| 20 | `abd742abc807e288` | index_etfs | held | +0.098 | -0.079 → -0.079 | +0.177 | 0.0002 vs 0.01 | **pass** | +0.440 / +0.378 / +0.187 | 30 · 0.3 |

20 of 20 candidates pass the fifth check on the definition partition; 0 of 20 have no margin over always-long in the latest definition era. A pass here is the gate shown passable before alpha moves, not a verdict; the measurement partition decides, once, at registration's cost. Registration is the author's `--yes`.
