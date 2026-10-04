"""``occams.toml`` — the author's numbers, loaded strictly and never defaulted.

R9: capital, drawdowns, risk per position, currency, FX exposure limit and
the forward-window minimum size are REQUIRED. R4: the alpha total, reserve,
the per-axis budgets and both per-test allocations are REQUIRED, and
``sum(axis budgets) + reserve == total`` holds on every load (S8, R4.7).
ADR-0033: the lab falsifier is REQUIRED — a missing falsifier is a refusal,
not a default of infinity.

**No default and no recommended value appears in this module** (R9). The
loader knows the *shape* of every field and nothing about its value; the
only literals below are zero (the allocation a non-runnable axis must carry,
ADR-0017) and one (the smallest count a falsifier can name).

The file is git-ignored. Its path comes from ``OCCAMS_CONFIG`` or the
argument; there is no search path, because a config found by accident is a
config nobody chose.
"""

from __future__ import annotations

import enum
import math
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ENV = "OCCAMS_CONFIG"
DEFAULT_PATH = "occams.toml"  # a location, not a value


class InformationAxis(enum.Enum):
    """Closed (R4.2, A6). A free-text axis is a construction error, not data."""

    REGIME = "regime"
    PRICE_DAILY = "price_daily"
    CROSS_SECTIONAL = "cross_sectional"
    FUNDAMENTAL = "fundamental"


CORRECTIONS = frozenset({"bonferroni"})
FALSIFIER_OUTCOMES = frozenset({"null"})  # "that many mechanism verdicts, none clearing its floor"

CAPITAL_FIELDS: dict[str, type] = {
    "starting": float,
    "max_drawdown_per_strategy": float,
    "max_drawdown_portfolio": float,
    "risk_per_trade": float,
    "currency": str,
    "fx_exposure_limit": float,
    "forward_window_min_size": float,  # ADR-0032, confirmed 2026-09-06
}
ALPHA_FIELDS: dict[str, type] = {"total": float, "reserve": float, "correction": str}
AXIS_FIELDS: dict[str, type] = {
    "budget": float, "mechanism_test_alpha": float, "implementation_test_alpha": float}
LAB_FIELDS: dict[str, type] = {"falsifier_count": int, "falsifier_outcome": str, "overlap_threshold": float}
PARTITION_FIELDS: dict[str, type] = {"definition": float, "measurement": float, "reserve": float}


class ConfigRefused(Exception):
    """Startup refused. ``reasons`` lists every defect found, not the first."""

    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("occams.toml refused:\n  - " + "\n  - ".join(reasons))


@dataclass(frozen=True)
class AxisAlpha:
    axis: InformationAxis
    budget: float
    mechanism_test_alpha: float
    implementation_test_alpha: float

    @property
    def runnable(self) -> bool:
        return self.budget > 0


@dataclass(frozen=True)
class Capital:
    starting: float
    max_drawdown_per_strategy: float
    max_drawdown_portfolio: float
    risk_per_trade: float
    currency: str
    fx_exposure_limit: float
    forward_window_min_size: float


@dataclass(frozen=True)
class Alpha:
    total: float
    reserve: float
    correction: str
    axes: dict[InformationAxis, AxisAlpha]


@dataclass(frozen=True)
class Lab:
    falsifier_count: int
    falsifier_outcome: str
    overlap_threshold: float  # R4.9: consumed-observation overlap above this refuses registration


@dataclass(frozen=True)
class PartitionSplit:
    """Three splits over the archive (D11). The forward window is not one."""

    definition: float
    measurement: float
    reserve: float


@dataclass(frozen=True)
class Config:
    capital: Capital
    alpha: Alpha
    lab: Lab
    partitions: PartitionSplit
    path: Path


REGISTRATION_KEYS = {
    "floor.ev_net_r": "the detectable floor, EV per trade in net R (R3, D5)",
    "floor.min_trades_per_year": "the floor's frequency half",
    "power.alternative_ev_net_r": "the EV the question wants power at, strictly above its floor (ADR-0050)",
    "gates.plateau_slack_se": "the plateau's slack in the winner's own standard errors (ADR-0051)",
}


def schema() -> str:
    """Every required key, no values. Printing a value would be recommending one."""
    lines = ["[capital]  # amounts in the account currency, not fractions; R9"]
    lines += [f"{k} = <{t.__name__}>  # required" for k, t in CAPITAL_FIELDS.items()]
    lines += ["", "[alpha]  # probabilities in (0, 1], not money; R4"]
    lines += [f"{k} = <{t.__name__}>  # required" for k, t in ALPHA_FIELDS.items()]
    for ax in InformationAxis:
        lines += ["", f"[alpha.axes.{ax.value}]"] + [f"{k} = <{t.__name__}>  # required" for k, t in AXIS_FIELDS.items()]
    lines += ["", "[lab]"] + [f"{k} = <{t.__name__}>  # required" for k, t in LAB_FIELDS.items()]
    lines += ["", "[partitions]"] + [f"{k} = <{t.__name__}>  # required; the three sum to 1; no fourth" for k, t in PARTITION_FIELDS.items()]
    lines += ["", f"# correction: one of {sorted(CORRECTIONS)}",
              f"# falsifier_outcome: one of {sorted(FALSIFIER_OUTCOMES)}",
              "# invariant: sum(axis budgets) + reserve == total",
              "# runnable axis (budget > 0): 0 < implementation_test_alpha < mechanism_test_alpha",
              "# non-runnable axis (budget == 0): all three fields exactly 0"]
    lines += ["", "# declared per question, at registration and never in this file — each the author's, none with a default:"]
    lines += [f"#   {k} = <float>  # {why}" for k, why in REGISTRATION_KEYS.items()]
    return "\n".join(lines)


def _section(raw: dict[str, Any], name: str, fields: dict[str, type], reasons: list[str],
             label: str | None = None) -> dict[str, Any] | None:
    label = label or name
    sec = raw.get(name)
    if not isinstance(sec, dict):
        reasons.append(f"[{label}] missing")
        return None
    out: dict[str, Any] = {}
    for key, typ in fields.items():
        if key not in sec:
            reasons.append(f"[{label}].{key} missing")
            continue
        v = sec[key]
        ok = (isinstance(v, (int, float)) and not isinstance(v, bool)) if typ is float else isinstance(v, typ) and not isinstance(v, bool)
        if not ok:
            reasons.append(f"[{label}].{key} must be {typ.__name__}")
            continue
        out[key] = float(v) if typ is float else v
    for key in sec:
        if key not in fields and not (name == "alpha" and key == "axes"):
            reasons.append(f"[{label}].{key} is not a known field")
    return out


def parse(raw: dict[str, Any], path: Path) -> Config:  # noqa: C901 — one refusal per missing or malformed key, in order; split, the schema scatters
    reasons: list[str] = []
    cap = _section(raw, "capital", CAPITAL_FIELDS, reasons)
    alp = _section(raw, "alpha", ALPHA_FIELDS, reasons)
    lab = _section(raw, "lab", LAB_FIELDS, reasons)
    parts = _section(raw, "partitions", PARTITION_FIELDS, reasons)
    for key in raw:
        if key not in ("capital", "alpha", "lab", "partitions"):
            reasons.append(f"[{key}] is not a known section")

    axes: dict[InformationAxis, AxisAlpha] = {}
    axes_raw = raw.get("alpha", {}).get("axes") if isinstance(raw.get("alpha"), dict) else None
    if not isinstance(axes_raw, dict):
        reasons.append("[alpha.axes] missing")
    else:
        for ax in InformationAxis:
            sec = _section(axes_raw, ax.value, AXIS_FIELDS, reasons, label=f"alpha.axes.{ax.value}")
            if sec is None or len(sec) != len(AXIS_FIELDS):
                continue
            a = AxisAlpha(ax, sec["budget"], sec["mechanism_test_alpha"], sec["implementation_test_alpha"])
            if a.budget < 0 or a.mechanism_test_alpha < 0 or a.implementation_test_alpha < 0:
                reasons.append(f"[alpha.axes.{ax.value}] fields must be >= 0")
            elif a.budget > 1 or a.mechanism_test_alpha > 1 or a.implementation_test_alpha > 1:
                reasons.append(f"[alpha.axes.{ax.value}] fields are probabilities, at most 1")
            elif a.runnable:
                if not (0 < a.implementation_test_alpha < a.mechanism_test_alpha):
                    reasons.append(f"[alpha.axes.{ax.value}] runnable axis needs 0 < implementation_test_alpha < mechanism_test_alpha")
            elif a.mechanism_test_alpha != 0 or a.implementation_test_alpha != 0:
                reasons.append(f"[alpha.axes.{ax.value}] budget is 0 so both allocations must be exactly 0 (ADR-0017)")
            axes[ax] = a
        for key in axes_raw:
            if key not in {ax.value for ax in InformationAxis}:
                reasons.append(f"[alpha.axes.{key}] is not a closed-enum axis (R4.2)")

    if cap is not None and len(cap) == len(CAPITAL_FIELDS):
        for k in ("starting", "max_drawdown_per_strategy", "max_drawdown_portfolio", "risk_per_trade", "forward_window_min_size"):
            if cap[k] <= 0:
                reasons.append(f"[capital].{k} must be > 0")
        if cap["fx_exposure_limit"] < 0:
            reasons.append("[capital].fx_exposure_limit must be >= 0")
        # shape, not value: every amount is in the account currency, so a
        # fraction typed where an amount belongs shows up here, not in a trade
        if cap["risk_per_trade"] >= cap["starting"]:
            reasons.append("[capital].risk_per_trade must be less than starting — amounts, not fractions")
        if cap["max_drawdown_per_strategy"] > cap["starting"] or cap["max_drawdown_portfolio"] > cap["starting"]:
            reasons.append("[capital] drawdown limits cannot exceed starting capital — amounts, not fractions")
        if cap["forward_window_min_size"] > cap["risk_per_trade"]:
            reasons.append("[capital].forward_window_min_size cannot exceed risk_per_trade — the window trades at minimum size")
        if not (len(cap["currency"]) == 3 and cap["currency"].isalpha() and cap["currency"].isupper()):
            reasons.append("[capital].currency must be a three-letter ISO code")

    if alp is not None and len(alp) == len(ALPHA_FIELDS):
        if not (0 < alp["total"] <= 1):
            reasons.append("[alpha].total is a probability in (0, 1] — the donor's search-corrected 1.70 is the state this forbids (ADR-0017)")
        if not (0 <= alp["reserve"] <= alp["total"]):
            reasons.append("[alpha].reserve must be within [0, total]")
        if alp["correction"] not in CORRECTIONS:
            reasons.append(f"[alpha].correction must be one of {sorted(CORRECTIONS)}")
        if len(axes) == len(InformationAxis):
            total = sum(a.budget for a in axes.values()) + alp["reserve"]
            if not math.isclose(total, alp["total"], rel_tol=0, abs_tol=1e-12):
                reasons.append("S8: sum(axis budgets) + reserve != [alpha].total")

    if lab is not None and len(lab) == len(LAB_FIELDS):
        if lab["falsifier_count"] < 1:
            reasons.append("[lab].falsifier_count must be >= 1")
        if lab["falsifier_outcome"] not in FALSIFIER_OUTCOMES:
            reasons.append(f"[lab].falsifier_outcome must be one of {sorted(FALSIFIER_OUTCOMES)}")
        if not (0 < lab["overlap_threshold"] <= 1):
            reasons.append("[lab].overlap_threshold is a fraction in (0, 1]")

    if parts is not None and len(parts) == len(PARTITION_FIELDS):
        for k, v in parts.items():
            if not (0 < v < 1):
                reasons.append(f"[partitions].{k} must be strictly between 0 and 1")
        if not math.isclose(sum(parts.values()), 1, rel_tol=0, abs_tol=1e-12):
            reasons.append("[partitions] must sum to exactly 1 — three splits over the archive (D11)")

    if reasons:
        raise ConfigRefused(reasons)
    assert cap is not None and alp is not None and lab is not None and parts is not None
    return Config(Capital(**cap), Alpha(alp["total"], alp["reserve"], alp["correction"], axes),
                  Lab(lab["falsifier_count"], lab["falsifier_outcome"], lab["overlap_threshold"]),
                  PartitionSplit(**parts), path)


def load(path: str | os.PathLike[str] | None = None) -> Config:
    p = Path(path if path is not None else os.environ.get(ENV, DEFAULT_PATH))
    if not p.exists():
        raise ConfigRefused([f"{p} does not exist — the author's numbers are required and never defaulted (R9, R4, ADR-0033)"])
    with p.open("rb") as f:
        try:
            raw = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ConfigRefused([f"{p} is not valid TOML: {e}"]) from None
    return parse(raw, p)
