"""Shared pytest fixtures. Test data conventions: docs/test-plan.md section 2.4."""
from datetime import date

import pytest

from library.clock import FixedClock
from library.db import Database
from library.domain import Role
from library.rules import Rules
from library.services import build_services

TODAY = date(2026, 12, 1)
PASSWORD = "secret123"
DUNE = "9780441172719"
DUNE_MESSIAH = "9780441172696"
CLEAN_CODE = "9780132350884"


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


@pytest.fixture
def svc(db, clock, rules):
    """All services wired on an in-memory database, today = 2026-12-01."""
    return build_services(db, clock, rules)


# ---------- test data helpers ----------

def add_member(svc, name="Ann", password=PASSWORD):
    return svc.members.register(name, f"{name.lower()}@example.com", "+994501234567", password)


def add_librarian(svc, name="Lib"):
    return svc.members.register(name, f"{name.lower()}@example.com", None, PASSWORD, role=Role.LIBRARIAN)


def add_title(svc, isbn=DUNE, title="Dune", author="Frank Herbert", year=1990):
    return svc.catalogue.add_title(isbn, title, author, "Ace", year)


def add_copies(svc, title, *codes):
    return [svc.catalogue.add_copy(title.id, code) for code in codes]
