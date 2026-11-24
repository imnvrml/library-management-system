"""Clock strategy (models 5.1): the only place the system reads "today" (assumption A-10)."""
from datetime import date, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def today(self) -> date: ...
    def now(self) -> datetime: ...


class SystemClock:
    def today(self) -> date:
        return date.today()

    def now(self) -> datetime:
        return datetime.now().replace(microsecond=0)


class FixedClock:
    """Test double: time stands still until advance() is called."""

    def __init__(self, day: date):
        self.day = day
        self._tick = 0

    def today(self) -> date:
        return self.day

    def now(self) -> datetime:
        # each call is one second later, so records created in a row keep their order (reservation queue)
        self._tick += 1
        return datetime(self.day.year, self.day.month, self.day.day, 9, 0) + timedelta(seconds=self._tick)

    def advance(self, days: int) -> None:
        self.day += timedelta(days=days)
