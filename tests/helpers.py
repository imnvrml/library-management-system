"""Test data and helpers shared by all test levels (test plan section 2.4)."""
from datetime import date

from library.domain import Role

TODAY = date(2026, 12, 1)
PASSWORD = "secret123"
DUNE = "9780441172719"
DUNE_MESSIAH = "9780441172696"
CLEAN_CODE = "9780132350884"
CSRF = "test-csrf-token"


def add_member(svc, name="Ann", password=PASSWORD):
    return svc.members.register(name, f"{name.lower()}@example.com", "+994501234567", password)


def add_librarian(svc, name="Lib"):
    return svc.members.register(name, f"{name.lower()}@example.com", None, PASSWORD, role=Role.LIBRARIAN)


def add_title(svc, isbn=DUNE, title="Dune", author="Frank Herbert", year=1990):
    return svc.catalogue.add_title(isbn, title, author, "Ace", year)


def add_copies(svc, title, *codes):
    return [svc.catalogue.add_copy(title.id, code) for code in codes]


def login(client, email):
    return client.post("/login", data={"email": email, "password": PASSWORD, "csrf_token": CSRF})


def post(client, url, **form):
    return client.post(url, data={"csrf_token": CSRF, **form}, follow_redirects=True)
