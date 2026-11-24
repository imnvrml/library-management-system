"""Login and access control through HTTP: TC-AUTH-01..03, 05, TC-ACC-01..05, TC-NFR-03 (FR-01, FR-02, NFR-03)."""
import pytest
from flask import url_for

from library.domain import Role
from system.conftest import CSRF, login, post

PUBLIC = {"static", "auth.login", "auth.logout", "home"}


def protected_endpoints(app):
    """(endpoint, method, url) for every page except the public ones; ids filled with 1."""
    result = []
    with app.test_request_context():
        for rule in app.url_map.iter_rules():
            if rule.endpoint in PUBLIC:
                continue
            url = url_for(rule.endpoint, **{arg: 1 for arg in rule.arguments})
            method = "POST" if "POST" in rule.methods else "GET"
            result.append((rule.endpoint, method, url, app.view_functions[rule.endpoint]))
    return result


def call(client, method, url):
    if method == "POST":
        return client.post(url, data={"csrf_token": CSRF})
    return client.get(url)


def test_TC_AUTH_01_login_redirects_to_role_home(client, data):
    assert login(client, "ann@example.com").headers["Location"].endswith("/account")
    client.post("/logout", data={"csrf_token": CSRF})
    assert login(client, "lib@example.com").headers["Location"].endswith("/dashboard")


def test_TC_AUTH_02_wrong_password(client, data):
    page = client.post("/login", data={"email": "ann@example.com", "password": "wrong-pass", "csrf_token": CSRF})
    assert b"Invalid e-mail or password" in page.data
    with client.session_transaction() as s:
        assert "user_id" not in s


def test_TC_AUTH_03_unknown_email_same_message(client, data):
    page = client.post("/login", data={"email": "nobody@example.com", "password": "x" * 8, "csrf_token": CSRF})
    assert b"Invalid e-mail or password" in page.data
    with client.session_transaction() as s:
        assert "user_id" not in s


def test_TC_AUTH_05_logout_protects_pages_again(client, data):
    login(client, "ann@example.com")
    client.post("/logout", data={"csrf_token": CSRF})
    assert client.get("/account").headers["Location"].startswith("/login")


def test_TC_ACC_01_member_gets_403_on_every_librarian_page(app, client, data):
    login(client, "ann@example.com")
    librarian_only = [e for e in protected_endpoints(app) if e[3].allowed_roles == (Role.LIBRARIAN,)]
    assert len(librarian_only) >= 10
    for endpoint, method, url, _ in librarian_only:
        assert call(client, method, url).status_code == 403, endpoint


def test_TC_ACC_02_visitor_is_sent_to_login_from_every_protected_page(app, client, data):
    for endpoint, method, url, _ in protected_endpoints(app):
        response = call(client, method, url)
        assert response.status_code == 302 and response.headers["Location"].startswith("/login"), endpoint


def test_TC_ACC_03_member_cannot_renew_another_members_loan(client, svc, data):
    loan = svc.circulation.checkout(data["ben"].id, "C-001")
    login(client, "ann@example.com")
    assert client.post(f"/loans/{loan.id}/renew", data={"csrf_token": CSRF}).status_code == 403
    assert svc.loans.get(loan.id).renewal_count == 0


def test_TC_ACC_04_member_cannot_cancel_another_members_reservation(client, svc, data):
    svc.circulation.checkout(data["ann"].id, "C-001")
    svc.circulation.checkout(data["ann"].id, "C-002")
    reservation = svc.queue.place(data["ben"].id, data["dune"].id)
    login(client, "ann@example.com")
    assert client.post(f"/reservations/{reservation.id}/cancel", data={"csrf_token": CSRF}).status_code == 403
    assert svc.reservations.get(reservation.id).status == "waiting"


def test_TC_ACC_05_librarian_reaches_every_librarian_page(app, client, data):
    login(client, "lib@example.com")
    for endpoint, method, url, view in protected_endpoints(app):
        if Role.LIBRARIAN in view.allowed_roles:
            expected = (200,) if method == "GET" else (200, 302)
            assert call(client, method, url).status_code in expected, endpoint


def test_TC_NFR_03_every_protected_page_declares_its_roles(app):
    endpoints = protected_endpoints(app)
    assert endpoints and all(hasattr(view, "allowed_roles") for *_, view in endpoints)


def test_post_without_csrf_token_is_rejected(client, data):
    response = client.post("/login", data={"email": "ann@example.com", "password": "secret123"})
    assert response.status_code == 400


@pytest.mark.parametrize("path", ["/", "/titles"])
def test_visitor_redirected_to_login(client, path):
    assert client.get(path).headers["Location"].startswith("/login")


def test_member_session_for_deactivated_account_is_closed(client, svc, data):
    login(client, "ben@example.com")
    svc.members.deactivate(data["ben"].id)
    assert client.get("/account").headers["Location"].startswith("/login")


def test_flash_messages_shown_after_redirect(client, data):
    login(client, "lib@example.com")
    page = post(client, "/circulation/checkout", member_email="nobody@example.com", copy_code="C-001")
    assert b"Member not found" in page.data
