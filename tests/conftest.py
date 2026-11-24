"""Shared pytest fixtures. Test data and helpers: tests/helpers.py."""
import pytest

from helpers import TODAY
from library.clock import FixedClock
from library.db import Database
from library.rules import Rules
from library.services import build_services


@pytest.fixture(autouse=True)
def fast_password_hashing(monkeypatch):
    """Same salted PBKDF2 algorithm family, fewer iterations: hashing is not what these tests check."""
    monkeypatch.setattr("library.services.auth.HASH_METHOD", "pbkdf2:sha256:1000")


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
