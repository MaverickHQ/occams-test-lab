"""The action series' per-name index visits exactly what a scan of the whole series would, in the same order (M12.3)."""

from __future__ import annotations

import random

from occams.data.actions import Action, ActionKind, ActionSeries, rebase


def brute(series, name, lo, hi):
    f = 1.0
    for a in series.actions:
        if a.kind is ActionKind.SPLIT and a.name == name and lo < a.day <= hi:
            f *= a.ratio
    d = sum(a.amount for a in series.actions if a.kind is ActionKind.DIVIDEND and a.name == name and lo < a.day <= hi)
    dl = next((a for a in series.actions if a.kind is ActionKind.DELISTING and a.name == name), None)
    return f, d, dl


def series_of(rng, *, sorted_days: bool) -> ActionSeries:
    acts = []
    for name in ("AAA", "BBB", "CCC"):
        days = sorted(rng.sample(range(1000, 1400), 60))
        if not sorted_days:
            rng.shuffle(days)
        for d in days:
            k = rng.choice((ActionKind.SPLIT, ActionKind.DIVIDEND, ActionKind.DIVIDEND, ActionKind.DIVIDEND))
            acts.append(Action(k, name, d, ratio=rng.choice((2.0, 3.0, 1.5, 0.5)) if k is ActionKind.SPLIT else None,
                               amount=round(rng.uniform(0.01, 2.0), 6) if k is ActionKind.DIVIDEND else None))
        acts.append(Action(ActionKind.DELISTING, name, 1500, terms=1.0))
    return ActionSeries(tuple(acts))


def test_the_index_is_bit_identical_to_the_scan_sorted_and_unsorted():
    rng = random.Random(3)
    for sorted_days in (True, False):
        s = series_of(rng, sorted_days=sorted_days)
        for _ in range(300):
            name = rng.choice(("AAA", "BBB", "CCC", "ZZZ"))
            lo = rng.randint(900, 1450)
            hi = rng.randint(lo, 1500)
            f, d, dl = brute(s, name, lo, hi)
            assert s.split_factor(name, lo, hi) == f and s.dividends_between(name, lo, hi) == d and s.delisting(name) is dl
            assert rebase(123.456, name=name, from_day=lo, to_day=hi, series=s) == 123.456 / f - d
        assert s.for_name("AAA") == tuple(a for a in s.actions if a.name == "AAA") and s.on_day("BBB", 1500)[0].kind is ActionKind.DELISTING
    assert ActionSeries().split_factor("AAA", 0, 10) == 1.0 and ActionSeries().dividends_between("AAA", 0, 10) == 0 and ActionSeries().delisting("AAA") is None
