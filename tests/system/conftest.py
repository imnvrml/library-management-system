"""System-test fixtures: the whole Flask app on a temporary database file, today = 2026-12-01."""
import pytest

from conftest import PASSWORD, add_copies, add_librarian, add_member, add_title
from library import create_app
from library.clock import FixedClock
from conftest import TODAY

CSRF = "test-csrf-token"


@pytest.fixture
def app(tmp_path):
    return create_app({"DATABASE": str(tmp_path / "system.db"), "TESTING": True, "CLOCK": FixedClock(TODAY)})


@pytest.fixture
def svc(app):
    return app.extensions["library"]


@pytest.fixture
def client(app):
    c = app.test_client()
    with c.session_transaction() as s:
        s["csrf"] = CSRF
    return c


@pytest.fixture
def data(svc):
    """Ann, Ben (members), Lib (librarian); *Dune* with copies C-001 and C-002."""
    dune = add_title(svc)
    add_copies(svc, dune, "C-001", "C-002")
    return {"ann": add_member(svc, "Ann"), "ben": add_member(svc, "Ben"), "lib": add_librarian(svc), "dune": dune}


def login(client, email):
    return client.post("/login", data={"email": email, "password": PASSWORD, "csrf_token": CSRF})


def post(client, url, **form):
    return client.post(url, data={"csrf_token": CSRF, **form}, follow_redirects=True)
