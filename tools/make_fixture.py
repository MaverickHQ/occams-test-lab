"""Generate ``tests/fixtures/tiingo_synthetic.json`` — synthetic bars in
Tiingo's daily-prices response schema, so the parser and the port are
exercised without a vendor row in the repository (raw redistribution is
forbidden, M0.3). Deterministic: re-running rewrites the same bytes.

Planted for the tests: a 2:1 split on XSYN's 41st row and a cash dividend
on its 60th; YSYN has neither.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from occams.data.bars import random_walk  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "tiingo_synthetic.json"
START = date(2024, 1, 2)


def trading_dates(n: int) -> list[date]:
    out, d = [], START
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def rows_for(name: str, seed: int, n: int, *, split_at: int | None, split_ratio: float,
             dividend_at: int | None, dividend: float) -> list[dict]:
    b = random_walk(name, days=n, seed=seed, sigma_daily=0.015)
    factor = 1.0
    rows = []
    for i, d in enumerate(trading_dates(n)):
        if split_at is not None and i == split_at:
            factor *= split_ratio
        o, h, lo, c = (b.open[i] / factor, b.high[i] / factor, b.low[i] / factor, b.close[i] / factor)
        rows.append({
            "date": d.isoformat() + "T00:00:00.000Z",
            "open": round(o, 4), "high": round(h, 4), "low": round(lo, 4), "close": round(c, 4),
            "volume": int(b.volume[i] * factor),
            "adjOpen": round(o, 4), "adjHigh": round(h, 4), "adjLow": round(lo, 4), "adjClose": round(c, 4),
            "adjVolume": int(b.volume[i] * factor),
            "divCash": dividend if (dividend_at is not None and i == dividend_at) else 0.0,
            "splitFactor": split_ratio if (split_at is not None and i == split_at) else 1.0,
        })
    return rows


def main() -> int:
    data = {
        "XSYN": rows_for("XSYN", 101, 80, split_at=40, split_ratio=2.0, dividend_at=59, dividend=0.35),
        "YSYN": rows_for("YSYN", 202, 80, split_at=None, split_ratio=1.0, dividend_at=None, dividend=0.0),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(OUT.parents[2])}: {sum(len(v) for v in data.values())} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
