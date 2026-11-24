"""Shared pytest fixtures. Test data conventions: docs/test-plan.md section 2.4."""
from datetime import date

import pytest

from library.clock import FixedClock
from library.db import Database
from library.rules import Rules

TODAY = date(2026, 12, 1)


@pytest.fixture
def rules():
    return Rules()


@pytest.fixture
def clock():
    return FixedClock(TODAY)


@pytest.fixture
def db():
    database = Database(":memory:")
    database.init_schema()
    yield database
    database.close()
