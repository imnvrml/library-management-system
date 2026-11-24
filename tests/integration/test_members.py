"""Members and authentication: TC-MEM-01..07, TC-AUTH-04, TC-NFR-02 (FR-01, FR-07, FR-08, NFR-02)."""
from datetime import date

import pytest

from helpers import PASSWORD, add_member
from library.domain import Loan, Role
from library.errors import BusinessRuleError


def test_TC_MEM_01_register_member_can_log_in(svc):
    dan = add_member(svc, "Dan")
    assert dan.role == Role.MEMBER and dan.is_active
    assert svc.auth.login("dan@example.com", PASSWORD).id == dan.id


def test_TC_MEM_02_duplicate_email(svc):
    add_member(svc, "Ann")
    with pytest.raises(BusinessRuleError, match="E-mail already registered"):
        svc.members.register("Ann Two", "ANN@example.com", None, PASSWORD)


def test_TC_MEM_03_password_of_7_characters(svc):
    with pytest.raises(BusinessRuleError, match="Password too short"):
        add_member(svc, "Dan", password="1234567")


def test_TC_MEM_04_password_of_8_characters(svc):
    assert add_member(svc, "Dan", password="12345678").id is not None


def test_TC_MEM_05_deactivate_member_without_loans_or_balance(svc):
    ben = add_member(svc, "Ben")
    assert svc.members.deactivate(ben.id).is_active is False
    with pytest.raises(BusinessRuleError, match="Account is deactivated"):
        svc.auth.login("ben@example.com", PASSWORD)


def open_loan(svc, member_id, due=date(2026, 12, 15), returned=None, fine=0):
    con = svc.db.connection()
    title_id = con.execute(
        "INSERT INTO title (isbn, title, author, pub_year) VALUES (?, 'T', 'A', 2000)",
        (f"97800000{member_id:05d}",),
    ).lastrowid
    copy_id = con.execute(
        "INSERT INTO copy (title_id, code, status) VALUES (?, ?, 'on_loan')", (title_id, f"X-{title_id}")
    ).lastrowid
    return svc.loans.add(Loan(None, copy_id, member_id, date(2026, 11, 20), due, returned, 0, fine))


def test_TC_MEM_06_deactivate_member_with_open_loan(svc):
    ann = add_member(svc, "Ann")
    open_loan(svc, ann.id)
    with pytest.raises(BusinessRuleError, match="open loans"):
        svc.members.deactivate(ann.id)


def test_TC_MEM_07_deactivate_member_with_balance(svc):
    ann = add_member(svc, "Ann")
    open_loan(svc, ann.id, returned=date(2026, 11, 30), fine=20)
    assert svc.members.balance(ann.id) == 20
    with pytest.raises(BusinessRuleError, match="outstanding balance"):
        svc.members.deactivate(ann.id)


def test_TC_AUTH_04_deactivated_member_cannot_log_in(svc):
    cem = add_member(svc, "Cem")
    svc.members.deactivate(cem.id)
    with pytest.raises(BusinessRuleError, match="Account is deactivated"):
        svc.auth.login("cem@example.com", PASSWORD)


@pytest.mark.parametrize("email, password", [("ann@example.com", "wrong-pass"), ("nobody@example.com", PASSWORD)])
def test_login_uses_one_message_for_wrong_password_and_unknown_email(svc, email, password):
    add_member(svc, "Ann")
    with pytest.raises(BusinessRuleError, match="^Invalid e-mail or password$"):
        svc.auth.login(email, password)


def test_TC_NFR_02_password_is_stored_as_salted_hash(svc):
    ann = add_member(svc, "Ann", password="secret123")
    stored = svc.db.connection().execute("SELECT * FROM user WHERE id = ?", (ann.id,)).fetchone()
    assert stored["password_hash"] != "secret123"
    assert stored["password_hash"].startswith(("scrypt:", "pbkdf2:"))
    assert all("secret123" not in str(value) for value in tuple(stored))
