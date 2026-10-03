"""``python -m occams whatif [config ...]`` — the consequence surface of a
configuration, on paper, before it is adopted.

Every table the author was shown by hand on 2026-09-10 is derived here from
the config alone: R in money and as a share of capital, breadth by stop,
halts in R with the false-halt probability of a working strategy, cost in
R by instrument class in the configured currency, the trades a cell needs
at the configured rates, how many mechanism verdicts the budgets afford,
and whether the falsifier can ever fire. Two or more configs print side by
side. The report *prints* the author's values because it is written for
the author, on the author's machine; nothing here writes to any record.

What this is not: a way to re-run a registered question under new inputs.
A registration is stamped with the config it ran under (M6); changing
alpha, the partitions or the falsifier afterwards is a recorded decision.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from occams.config import Config, ConfigRefused, load
from occams.core import power
from occams.costs.equity import EquityCosts, InstrumentClass

STOPS = (0.02, 0.025, 0.03, 0.05)
FALSIFIER_N = (3, 5, 8, 12)                  # counts to show the closing probability for (M12.0)
BASE_RATES = (0.05, 0.10, 0.20, 0.30, 0.50)  # the share of registered questions that carry a real edge at the floor
SIGNAL_RATES = (0.05, 0.10, 0.20)            # trades per name-day a mechanism might fire at
FLOORS_WIDE = (0.05, 0.075, 0.10, 0.15, 0.20, 0.25)
HALT_TRADES = (100, 200, 500)
FLOORS = (0.10, 0.15, 0.20, 0.25)
SIGMA_R = 1.2      # the on-paper sigma the M0.15 tables used; a Hypothesis declares its own
FLOOR_EV = 0.15    # the M0.15 headline floor; a Hypothesis declares its own
CELLS = (4, 9)     # the two sweep sizes in use (DRAFT-001, the controls)
SEED = 20260910


def config_sha(cfg: Config) -> str:
    return hashlib.sha256(Path(cfg.path).read_bytes()).hexdigest()[:12]


def false_halt_probability(halt_r: float, n_trades: int, *, ev: float = FLOOR_EV, sigma: float = SIGMA_R,
                           draws: int = 4000, seed: int = SEED) -> float:
    """P(a working strategy at ``ev`` draws down through ``halt_r`` within n trades)."""
    rng = np.random.default_rng([seed, n_trades])
    x = rng.standard_normal((draws, n_trades)) * sigma + ev
    path = np.cumsum(x, axis=1)
    peak = np.maximum.accumulate(np.maximum(path, 0), axis=1)
    return float(((peak - path).max(axis=1) >= halt_r).mean())


def close_probability(n: int, base_rate: float, *, power: float = 0.8) -> float:
    """P(the first ``n`` mechanism verdicts are all null) when a share
    ``base_rate`` of the questions registered carry a real edge at the floor
    and the plan's power is ``power``: a true edge resolves null with
    probability 1 - power, a false one with probability about 1. This is
    what a falsifier count buys: a count of three closes a lab whose
    questions are one-in-five real more than half the time (M12.0)."""
    return (1.0 - float(base_rate) * float(power)) ** int(n)


def universe_rho(bars_by_name) -> tuple[float, float, int]:
    """Same-day ICC(1) of close-to-close returns across the names — the
    pooled set's concurrency on paper, by the same estimator the lab uses on
    trades (M7.7) — with the mean names per day and the day count."""
    from occams.measurement import Trade
    from occams.proposers.clustering import ClusterLevel, measure_clustering

    trades = [Trade(b.close[i] / b.close[i - 1] - 1.0, name, b.day[i]) for name, b in bars_by_name.items() for i in range(1, b.n)]
    cm = measure_clustering(trades, level=ClusterLevel.INDEX, provenance="daily close-to-close returns, definition partition")
    return float(cm.rho), float(cm.cluster_size), int(cm.n_clusters)


def affordability(cfg: Config, bars_by_name, *, span: tuple[int, int], name: str) -> dict:
    """On paper, for one universe: the trades a mechanism firing at each
    SIGNAL_RATE would afford on the measurement partition after the design
    effect at the universe's own same-day rho (measured on the definition
    partition, never the measurement one), and the LOWEST floor in
    FLOORS_WIDE that count can detect at each sweep size — a lower floor
    needs more trades. The floor stays the author's; this says what each
    one would cost in trades."""
    from occams.data.partitions import Partitions

    parts = Partitions.from_config(cfg)
    b = parts.bounds_over(*span)
    definition = {n: parts.slice(bb, "definition", span=span)[0] for n, bb in bars_by_name.items()}
    definition = {n: bb for n, bb in definition.items() if bb.n > 1}
    rho, _, _ = universe_rho(definition) if len(definition) > 1 else (0.0, 1.0, 0)
    days = b["measurement"][1] - b["measurement"][0]
    m = len(bars_by_name)
    axis = next((a for ax, a in cfg.alpha.axes.items() if ax.value == "price_daily" and a.runnable),
                next((a for a in cfg.alpha.axes.values() if a.runnable), None))
    rates = {}
    for r in SIGNAL_RATES:
        n_raw = r * days * m * 252 / 365.25
        m_day = (m * r) / (1.0 - (1.0 - r) ** m)          # trades per firing day, on paper
        n_eff = n_raw / (1.0 + (m_day - 1.0) * rho)
        afford = {}
        for k in CELLS:
            ok = [f for f in FLOORS_WIDE
                  if axis is not None and power.n_for_mean_shift(f / SIGMA_R, alpha=axis.mechanism_test_alpha / k, power=0.8) <= n_eff]
            afford[k] = min(ok) if ok else None
        rates[r] = {"n_raw": int(n_raw), "n_eff": int(n_eff), "affordable_floor": afford}
    return {"name": name, "names": m, "measurement_days": days, "rho": rho, "rates": rates,
            "mech_alpha": axis.mechanism_test_alpha if axis is not None else None}


def universes(cfg: Config, archive, register=None) -> list[dict]:
    """Every universe the archive can speak for: the whole archive, and
    each ``UniverseDeclared`` record (M12.1) whose members are archived."""
    from occams.data.partitions import Partitions, span_for

    latest = {n: b for n, (b, _a) in archive.latest_bars().items()}
    if not latest:
        return []
    parts = Partitions.from_config(cfg)
    span = span_for(register, latest, parts) if register is not None else Partitions.common_span(latest)
    out = [affordability(cfg, latest, span=span, name="archive: " + ", ".join(sorted(latest)))]
    declared: dict[str, dict] = {}
    for r in (register.records() if register is not None else []):
        if r["type"] == "UniverseDeclared":
            declared[r["name"]] = r    # the latest record under a name supersedes the earlier ones (ADR-0042): one row per universe
    # each declared universe on its own calendar (M12.1): its members' frozen span, never the archive's
    return out + [affordability(cfg, {n: latest[n] for n in r["members"]},
                                span=span_for(register, {n: latest[n] for n in r["members"]}, parts, universe=r["name"]),
                                name=r["name"])
                  for r in declared.values() if all(n in latest for n in r["members"])]


@dataclass(frozen=True)
class Flag:
    severity: str  # refuse | warn
    text: str


def derive(cfg: Config) -> dict:
    cap = cfg.capital
    r_pct = cap.risk_per_trade / cap.starting
    halt_s = cap.max_drawdown_per_strategy / cap.risk_per_trade
    halt_p = cap.max_drawdown_portfolio / cap.risk_per_trade
    out: dict = {
        "config": str(cfg.path), "sha": config_sha(cfg), "currency": cap.currency,
        "R": cap.risk_per_trade, "R_pct": r_pct,
        "breadth": {s: int(s / r_pct) for s in STOPS},
        "notional": {s: cap.risk_per_trade / s for s in STOPS},
        "halt_strategy_R": halt_s, "halt_portfolio_R": halt_p,
        "false_halt_strategy": {n: false_halt_probability(halt_s, n) for n in HALT_TRADES},
        "false_halt_portfolio": {n: false_halt_probability(halt_p, n) for n in HALT_TRADES},
        "min_size_R": cap.forward_window_min_size / cap.risk_per_trade,
        "fx_limit": cap.fx_exposure_limit,
    }
    # cost in R for the M0.7 class from this account currency, spread at the bound
    us = EquityCosts.declared(InstrumentClass.US_LARGE, instrument_currency="USD", account_currency=cap.currency).bound()
    out["cost_in_r_us"] = {s: us.cost_in_r(entry_price=100.0, stop_distance=100.0 * s) for s in STOPS}
    out["fx_per_trade"] = us.fixed_fraction()
    # alpha: per-cell rates -> required N, spend per question, affordable questions, falsifier affordability
    axes = {}
    for ax, a in cfg.alpha.axes.items():
        if not a.runnable:
            continue
        axes[ax.value] = {
            "budget": a.budget,
            "mech_rate": a.mechanism_test_alpha, "impl_rate": a.implementation_test_alpha,
            "spend_per_question": {k: a.mechanism_test_alpha * k for k in CELLS},
            "questions_affordable": {k: int(a.budget // (a.mechanism_test_alpha * k)) for k in CELLS},
            "required_n_mech": {f: power.n_for_mean_shift(f / SIGMA_R, alpha=a.mechanism_test_alpha, power=0.8) for f in FLOORS},
            "required_n_impl": {f: power.n_for_mean_shift(f / SIGMA_R, alpha=a.implementation_test_alpha, power=0.8) for f in FLOORS},
        }
    out["axes"] = axes
    runnable_total = sum(a["budget"] for a in axes.values())
    affordable = {k: sum(a["questions_affordable"][k] for a in axes.values()) for k in CELLS}
    out["verdicts_affordable"] = affordable
    out["falsifier_count"] = cfg.lab.falsifier_count
    out["p_all_null_with_edge"] = 0.2 ** cfg.lab.falsifier_count  # at 80 % power
    out["p_close"] = {n: {p_: close_probability(n, p_) for p_ in BASE_RATES}
                      for n in sorted(set(FALSIFIER_N) | {cfg.lab.falsifier_count})}
    out["alpha_total"] = cfg.alpha.total
    out["alpha_reserve"] = cfg.alpha.reserve
    out["runnable_total"] = runnable_total
    out["partitions"] = (cfg.partitions.definition, cfg.partitions.measurement, cfg.partitions.reserve)
    # flags: the consequences that should stop a set being adopted unread
    flags: list[Flag] = []
    if cap.currency != "USD" and cap.fx_exposure_limit < min(out["notional"].values()):
        flags.append(Flag("refuse", f"fx_exposure_limit {cap.fx_exposure_limit:,.0f} {cap.currency} is below one US-listed position's "
                                    f"notional at every stop ({min(out['notional'].values()):,.0f}+): the M0.7 class would be refused at M10"))
    if cfg.lab.falsifier_count > affordable[max(CELLS)]:
        flags.append(Flag("warn", f"falsifier_count {cfg.lab.falsifier_count} exceeds the {affordable[max(CELLS)]} mechanism verdicts "
                                  f"the runnable budgets afford at {max(CELLS)}-cell sweeps: it can only fire at smaller sweeps"))
    if cfg.lab.falsifier_count > affordable[min(CELLS)]:
        flags.append(Flag("refuse", f"falsifier_count {cfg.lab.falsifier_count} exceeds the {affordable[min(CELLS)]} verdicts affordable even at "
                                    f"{min(CELLS)}-cell sweeps: it can never fire"))
    if out["false_halt_strategy"][200] > 0.5:
        flags.append(Flag("warn", f"per-strategy halt at {halt_s:.0f}R false-halts a working strategy "
                                  f"{out['false_halt_strategy'][200]:.0%} of the time within 200 trades"))
    if out["breadth"][0.025] < 2:
        flags.append(Flag("warn", f"R at {r_pct:.2%} of capital allows {out['breadth'][0.025]} concurrent position at a 2.5 % stop: breadth is one"))
    if cap.max_drawdown_portfolio <= cap.max_drawdown_per_strategy:
        flags.append(Flag("warn", "the portfolio halt is not above the per-strategy halt; correlated strategies need room (D21)"))
    if cap.currency != "USD":
        flags.append(Flag("warn", f"from a {cap.currency} account the US-listed class pays {out['fx_per_trade']:.2%} in FX legs per round trip "
                                  f"= {out['cost_in_r_us'][0.025]:.2f}R at a 2.5 % stop against a {FLOOR_EV}R floor"))
    out["flags"] = flags
    return out


def _cols(ds: list[dict], f) -> str:
    return " | ".join(f(d) for d in ds)


def falsifier_table(ds: list[dict]) -> str:
    """P(the first N mechanism verdicts are all null) by base rate, one
    block per config, the declared count marked."""
    lines = ["", "**Falsifier arithmetic** — P(the first N mechanism verdicts are all null) when a share p of the questions "
             "registered carry a real edge at the floor, at 80 % power. A count that closes the lab before the base "
             "rate can show is a test of *edges are common*, not of *an edge exists*.", ""]
    for d in ds:
        lines.append(f"`{Path(d['config']).name}` · declared count {d['falsifier_count']}")
        lines.append("| N | " + " | ".join(f"p = {p_:.0%}" for p_ in BASE_RATES) + " |")
        lines.append("|---|" + "---|" * len(BASE_RATES))
        for n, row in d["p_close"].items():
            mark = " ← declared" if n == d["falsifier_count"] else ""
            lines.append(f"| {n}{mark} | " + " | ".join(f"{row[p_]:.0%}" for p_ in BASE_RATES) + " |")
        lines.append("")
    return "\n".join(lines)


def affordability_table(cfg: Config, us: list[dict]) -> str:
    """Per universe and signal rate: the trades the measurement partition
    affords after the design effect, and the lowest floor they detect."""
    if not us:
        return ""
    lines = ["", f"**Universe affordability, on paper** (`{Path(cfg.path).name}`) — trades a mechanism firing at r per name-day "
             "would afford on the measurement partition after the design effect at the universe's own same-day rho "
             "(daily returns, definition partition only), and the lowest floor in "
             + "/".join(f"{f:g}" for f in FLOORS_WIDE) + "R that count can detect at each sweep size — a lower floor needs more trades. The floor stays the author's.", "",
             "| universe | names | meas. days | rho | rate | N raw | N effective | lowest detectable floor at " + " / ".join(f"k={k}" for k in CELLS) + " |",
             "|---|---|---|---|---|---|---|---|"]
    for u in us:
        for r, row in u["rates"].items():
            afford = " / ".join(f"{row['affordable_floor'][k]:g}R" if row["affordable_floor"][k] is not None else "none" for k in CELLS)
            lines.append(f"| {u['name']} | {u['names']} | {u['measurement_days']:,} | {u['rho']:.2f} | {r:.2f} | {row['n_raw']:,} | {row['n_eff']:,} | {afford} |")
    lines.append("")
    return "\n".join(lines)


def report(cfgs: list[Config], universes_: list[dict] | None = None) -> str:
    ds = [derive(c) for c in cfgs]
    heads = " | ".join(f"`{Path(d['config']).name}` @{d['sha']}" for d in ds)
    sep = "|---|" + "---|" * len(ds)
    lines = [f"| what-if | {heads} |", sep,
             f"| currency | {_cols(ds, lambda d: d['currency'])} |",
             f"| R | {_cols(ds, lambda d: f'{d['R']:,.2f} ({d['R_pct']:.2%} of capital)')} |"]
    for s in STOPS:
        lines.append(f"| breadth · notional at {s:.1%} stop | {_cols(ds, lambda d, s=s: f'{d['breadth'][s]} · {d['notional'][s]:,.0f}')} |")
    lines.append(f"| per-strategy halt | {_cols(ds, lambda d: f'{d['halt_strategy_R']:.1f}R')} |")
    for n in HALT_TRADES:
        lines.append(f"| P(false halt, strategy) in {n} trades | {_cols(ds, lambda d, n=n: f'{d['false_halt_strategy'][n]:.0%}')} |")
    lines.append(f"| portfolio halt | {_cols(ds, lambda d: f'{d['halt_portfolio_R']:.1f}R')} |")
    lines.append(f"| P(false halt, portfolio) in 200 trades | {_cols(ds, lambda d: f'{d['false_halt_portfolio'][200]:.0%}')} |")
    lines.append(f"| forward minimum size | {_cols(ds, lambda d: f'{d['min_size_R']:.2f}R')} |")
    lines.append(f"| FX legs per round trip (US-listed) | {_cols(ds, lambda d: f'{d['fx_per_trade']:.2%}')} |")
    for s in STOPS:
        lines.append(f"| cost in R at {s:.1%} stop (US-listed, bound) | {_cols(ds, lambda d, s=s: f'{d['cost_in_r_us'][s]:.2f}R')} |")
    lines.append(f"| alpha total · reserve · runnable | {_cols(ds, lambda d: f'{d['alpha_total']} · {d['alpha_reserve']} · {d['runnable_total']:.3g}')} |")
    for ax in sorted({a for d in ds for a in d['axes']}):
        for k in CELLS:
            lines.append(f"| {ax}: spend per {k}-cell question · affordable | "
                         f"{_cols(ds, lambda d, ax=ax, k=k: (f'{d['axes'][ax]['spend_per_question'][k]:.3f} · {d['axes'][ax]['questions_affordable'][k]}' if ax in d['axes'] else '—'))} |")
        lines.append(f"| {ax}: N per cell, mechanism, at {'/'.join(str(f) for f in FLOORS)}R | "
                     f"{_cols(ds, lambda d, ax=ax: ('/'.join(str(d['axes'][ax]['required_n_mech'][f]) for f in FLOORS) if ax in d['axes'] else '—'))} |")
        lines.append(f"| {ax}: N per cell, implementation | "
                     f"{_cols(ds, lambda d, ax=ax: ('/'.join(str(d['axes'][ax]['required_n_impl'][f]) for f in FLOORS) if ax in d['axes'] else '—'))} |")
    lines.append(f"| mechanism verdicts affordable at {CELLS[0]}/{CELLS[1]} cells | {_cols(ds, lambda d: f'{d['verdicts_affordable'][CELLS[0]]} / {d['verdicts_affordable'][CELLS[1]]}')} |")
    lines.append(f"| falsifier count · P(all null with a real edge) | {_cols(ds, lambda d: f'{d['falsifier_count']} · {d['p_all_null_with_edge']:.1%}')} |")
    lines.append(f"| partitions def/meas/res | {_cols(ds, lambda d: '/'.join(f'{x:g}' for x in d['partitions']))} |")
    lines.append("")
    for d in ds:
        for fl in d["flags"]:
            lines.append(f"{'REFUSE' if fl.severity == 'refuse' else 'warn'} [{Path(d['config']).name}]: {fl.text}")
    lines.append("")
    lines.append(f"On paper: sigma {SIGMA_R}R and a {FLOOR_EV}R floor are the M0.15 conventions; a Hypothesis declares its own. "
                 "A registered question is stamped with its config; changing alpha, partitions or the falsifier afterwards is a recorded decision, not a re-run.")
    lines.append(falsifier_table(ds))
    if universes_:
        lines.append(affordability_table(cfgs[0], universes_))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="python -m occams whatif")
    ap.add_argument("configs", nargs="*", help="candidate configs; none means the working directory's occams.toml")
    ap.add_argument("--archive", default=None, help="with an archive: the universe affordability table (M12.0)")
    ap.add_argument("--register", default=None, help="with --archive: read the frozen calendar and any declared universes")
    a = ap.parse_args(argv)
    paths = a.configs or [None]
    cfgs = []
    for p in paths:
        try:
            cfgs.append(load(p))
        except ConfigRefused as e:
            print(f"REFUSED: {p or 'default config'} does not load, so it has no consequences to show:")
            for r in e.reasons:
                print(f"  - {r}")
            return 2
    us = None
    if a.archive:
        from occams.data.archive import BarArchive
        from occams.register import Register

        us = universes(cfgs[0], BarArchive(Path(a.archive)), Register(Path(a.register)) if a.register else None)
    print(report(cfgs, us))
    return 1 if any(f.severity == "refuse" for c in cfgs for f in derive(c)["flags"]) else 0


if __name__ == "__main__":
    sys.exit(main())
