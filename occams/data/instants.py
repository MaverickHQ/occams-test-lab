"""Time is an instant, never a date (R10, ADR-0020, D10).

A bar is usable for a claim only if the bar's close instant is strictly
after the claim's known-at instant. A date-only ``as_of`` is read
conservatively as the last instant of that calendar date in UTC, which
makes every bar closing on that date unusable for that claim (M4.5) — the
one reading under which no venue's close can leak.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc


class NotAnInstant(TypeError):
    """A date, or a naive datetime, where an instant is required."""


def instant(value) -> datetime:
    """Accept only a timezone-aware datetime; return it in UTC."""
    if isinstance(value, datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise NotAnInstant(f"{value!r} is naive — an instant carries its zone")
        return value.astimezone(UTC)
    if isinstance(value, date):
        raise NotAnInstant(f"{value!r} is a date — dates are for rendering, never for deciding")
    raise NotAnInstant(f"{value!r} is not an instant")


def end_of_day_utc(d: date) -> datetime:
    """The conservative reading of a date-only as_of: the last instant of
    that calendar date, so nothing printed on that date can be earlier."""
    if isinstance(d, datetime):
        raise NotAnInstant("end_of_day_utc takes a date; a datetime is already an instant")
    return datetime.combine(d, time(23, 59, 59, 999999), tzinfo=UTC)


# Regular session closes. Venue calendars proper (half days, holidays)
# arrive with the venue adapter; these are the closes the point-in-time
# gate needs to tell two venues' "today" apart.
VENUE_CLOSE: dict[str, tuple[str, time]] = {
    "LSE": ("Europe/London", time(16, 30)),
    "NYSE": ("America/New_York", time(16, 0)),
    "NASDAQ": ("America/New_York", time(16, 0)),
}


def session_close(d: date, venue: str) -> datetime:
    zone, at = VENUE_CLOSE[venue]
    return datetime.combine(d, at, tzinfo=ZoneInfo(zone)).astimezone(UTC)


def usable(bar_close_at, known_at) -> bool:
    """The gate. Strictly after, by instant."""
    return instant(bar_close_at) > instant(known_at)


@dataclass(frozen=True)
class Claim:
    """Anything known at an instant: a regime label, a filing, a fact."""

    text: str
    known_at: datetime

    def __post_init__(self):
        object.__setattr__(self, "known_at", instant(self.known_at))

    @classmethod
    def from_as_of(cls, text: str, as_of) -> "Claim":
        """A datetime is taken as the instant; a date is read as end of day (M4.5)."""
        if isinstance(as_of, datetime):
            return cls(text, as_of)
        return cls(text, end_of_day_utc(as_of))
