"""Circulation integration tests: checkout, return, renewal, payments, overdue list, copy state machine.

TC-CHK-13..17, TC-RET-01..04, TC-REN-07..09, TC-PAY-06, TC-OVD-01..02, TC-STC-01..04, TC-NFR-04.
"""
from datetime import date

import pytest

from helpers import CLEAN_CODE, add_copies, add_librarian, add_member, add_title
from library.domain import CopyStatus, ReservationStatus
from library.errors import AccessDeniedError, BusinessRuleError


def on(clock, day):
    clock.day = day


def status(svc, code):
    return svc.copies.find_by_code(code).status


@pytest.fixture
def dune(svc):
    title = add_title(svc)
    add_copies(svc, title, "C-001", "C-002")
    return title


# ---------- checkout (FR-09) ----------

def test_TC_CHK_13_checkout_creates_loan_due_in_14_days(svc, dune):
    ann = add_member(svc, "Ann")
    loan = svc.circulation.checkout(ann.id, "C-001")
    assert loan.checkout_date == date(2026, 12, 1) and loan.due_date == date(2026, 12, 15)
    assert status(svc, "C-001") == CopyStatus.ON_LOAN


def test_TC_CHK_14_holder_borrows_held_copy(svc, clock):
    title = add_title(svc)
    add_copies(svc, title, "C-001")
    ann, ben = add_member(svc, "Ann"), add_member(svc, "Ben")
    svc.circulation.checkout(ben.id, "C-001")
    reservation = svc.queue.place(ann.id, title.id)
    svc.circulation.return_copy("C-001")
    assert status(svc, "C-001") == CopyStatus.ON_HOLD

    svc.circulation.checkout(ann.id, "C-001")
    assert status(svc, "C-001") == CopyStatus.ON_LOAN
    assert svc.reservations.get(reservation.id).status == ReservationStatus.FULFILLED


def test_TC_CHK_15_member_with_overdue_loan_cannot_borrow(svc, clock, dune):
    ann = add_member(svc, "Ann")
    on(clock, date(2026, 11, 16))
    svc.circulation.checkout(ann.id, "C-001")  # due 2026-11-30
    on(clock, date(2026, 12, 1))
    with pytest.raises(BusinessRuleError, match="Member has overdue items"):
        svc.circulation.checkout(ann.id, "C-002")


def test_TC_CHK_16_loan_due_today_is_not_overdue(svc, clock, dune):
    ann = add_member(svc, "Ann")
    on(clock, date(2026, 11, 17))
    svc.circulation.checkout(ann.id, "C-001")  # due 2026-12-01
    on(clock, date(2026, 12, 1))
    assert svc.circulation.checkout(ann.id, "C-002").due_date == date(2026, 12, 15)


def test_TC_CHK_17_unknown_copy_code(svc, dune):
    ann = add_member(svc, "Ann")
    with pytest.raises(BusinessRuleError, match="Copy not found"):
        svc.circulation.checkout(ann.id, "NOPE")
    assert svc.loans.open_loans_of(ann.id) == []


def test_checkout_refusal_saves_nothing(svc, dune):
    ann = add_member(svc, "Ann")
    svc.catalogue.withdraw_copy(svc.copies.find_by_code("C-001").id)
    with pytest.raises(BusinessRuleError, match="Copy is not available"):
        svc.circulation.checkout(ann.id, "C-001")
    assert svc.loans.open_loans_of(ann.id) == []


# ---------- return (FR-10, FR-12, FR-14) ----------

def test_TC_RET_01_return_on_due_date(svc, clock, dune):
    ann = add_member(svc, "Ann")
    svc.circulation.checkout(ann.id, "C-001")
    on(clock, date(2026, 12, 15))
    loan = svc.circulation.return_copy("C-001")
    assert loan.return_date == date(2026, 12, 15) and loan.fine_qepik == 0
    assert status(svc, "C-001") == CopyStatus.AVAILABLE


def test_TC_RET_02_returned_copy_goes_to_first_in_queue(svc):
    title = add_title(svc)
    add_copies(svc, title, "C-001")
    ann, ben, cem = add_member(svc, "Ann"), add_member(svc, "Ben"), add_member(svc, "Cem")
    svc.circulation.checkout(cem.id, "C-001")
    first = svc.queue.place(ann.id, title.id)
    second = svc.queue.place(ben.id, title.id)

    svc.circulation.return_copy("C-001")

    first = svc.reservations.get(first.id)
    assert status(svc, "C-001") == CopyStatus.ON_HOLD
    assert first.status == ReservationStatus.READY and first.pickup_deadline == date(2026, 12, 4)
    assert svc.queue.position(svc.reservations.get(second.id)) == 1


def test_TC_RET_03_return_available_copy(svc, dune):
    with pytest.raises(BusinessRuleError, match="Copy is not on loan"):
        svc.circulation.return_copy("C-001")


def test_TC_RET_04_late_return_charges_fine(svc, clock, dune):
    ann = add_member(svc, "Ann")
    on(clock, date(2026, 11, 15))
    svc.circulation.checkout(ann.id, "C-001")  # due 2026-11-29
    on(clock, date(2026, 12, 1))
    assert svc.circulation.return_copy("C-001").fine_qepik == 40
    assert svc.members.balance(ann.id) == 40


# ---------- renewal (FR-11) ----------

def test_TC_REN_07_renew_extends_from_due_date(svc, clock, dune):
    ann = add_member(svc, "Ann")
    loan = svc.circulation.checkout(ann.id, "C-001")
    on(clock, date(2026, 12, 10))
    renewed = svc.circulation.renew(loan.id, ann)
    assert renewed.due_date == date(2026, 12, 29) and renewed.renewal_count == 1


def test_TC_REN_08_member_cannot_renew_another_members_loan(svc, dune):
    ann, ben = add_member(svc, "Ann"), add_member(svc, "Ben")
    loan = svc.circulation.checkout(ben.id, "C-001")
    with pytest.raises(AccessDeniedError):
        svc.circulation.renew(loan.id, ann)
    assert svc.loans.get(loan.id).due_date == date(2026, 12, 15)


def test_TC_REN_09_title_reserved_by_another_member(svc):
    title = add_title(svc)
    add_copies(svc, title, "C-001")
    ann, ben = add_member(svc, "Ann"), add_member(svc, "Ben")
    loan = svc.circulation.checkout(ann.id, "C-001")
    svc.queue.place(ben.id, title.id)
    with pytest.raises(BusinessRuleError, match="Title is reserved by another member"):
        svc.circulation.renew(loan.id, ann)


def test_librarian_can_renew_any_loan(svc, dune):
    ann, lib = add_member(svc, "Ann"), add_librarian(svc)
    loan = svc.circulation.checkout(ann.id, "C-001")
    assert svc.circulation.renew(loan.id, lib).renewal_count == 1


# ---------- payments and overdue list (FR-18, FR-19) ----------

def test_TC_PAY_06_payment_reduces_balance(svc, clock, dune):
    ann, lib = add_member(svc, "Ann"), add_librarian(svc)
    on(clock, date(2026, 11, 12))
    svc.circulation.checkout(ann.id, "C-001")  # due 2026-11-26
    on(clock, date(2026, 12, 1))
    svc.circulation.return_copy("C-001")       # 5 days late -> 100
    assert svc.members.balance(ann.id) == 100
    svc.members.record_payment(ann.id, 60, lib.id)
    assert svc.members.balance(ann.id) == 40


def test_TC_OVD_01_overdue_list_sorted_by_days_late(svc, clock, dune):
    ann, ben = add_member(svc, "Ann"), add_member(svc, "Ben")
    on(clock, date(2026, 11, 14))
    svc.circulation.checkout(ben.id, "C-002")  # due 11-28
    on(clock, date(2026, 11, 7))
    svc.circulation.checkout(ann.id, "C-001")  # due 11-21
    on(clock, date(2026, 12, 1))
    rows = svc.circulation.overdue_loans()
    assert [(r.copy_code, r.days_late, r.fine_so_far_qepik) for r in rows] == [("C-001", 10, 200), ("C-002", 3, 60)]
    assert rows[0].member_name == "Ann" and rows[0].title == "Dune"


def test_TC_OVD_02_loan_due_today_not_listed(svc, clock, dune):
    ann = add_member(svc, "Ann")
    on(clock, date(2026, 11, 17))
    svc.circulation.checkout(ann.id, "C-001")  # due 12-01
    on(clock, date(2026, 12, 1))
    assert svc.circulation.overdue_loans() == []


# ---------- copy state machine: invalid events and a full path (ST-1) ----------

@pytest.fixture
def held_copy(svc):
    """C-001 of *Dune* On hold for Ann (Ben borrowed it, Ann reserved, Ben returned)."""
    title = add_title(svc)
    add_copies(svc, title, "C-001")
    ann, ben = add_member(svc, "Ann"), add_member(svc, "Ben")
    svc.circulation.checkout(ben.id, "C-001")
    svc.queue.place(ann.id, title.id)
    svc.circulation.return_copy("C-001")
    return svc.copies.find_by_code("C-001")


def test_TC_STC_01_withdraw_copy_on_hold(svc, held_copy):
    with pytest.raises(BusinessRuleError, match="Copy is not on the shelf"):
        svc.catalogue.withdraw_copy(held_copy.id)


def test_TC_STC_02_return_copy_on_hold(svc, held_copy):
    with pytest.raises(BusinessRuleError, match="Copy is not on loan"):
        svc.circulation.return_copy("C-001")


def test_TC_STC_03_return_withdrawn_copy(svc, dune):
    svc.catalogue.withdraw_copy(svc.copies.find_by_code("C-001").id)
    with pytest.raises(BusinessRuleError, match="Copy is not on loan"):
        svc.circulation.return_copy("C-001")


def test_TC_STC_04_full_life_cycle_of_one_copy(svc, clock):
    title = add_title(svc)
    add_copies(svc, title, "C-001")
    ann, ben, cem = add_member(svc, "Ann"), add_member(svc, "Ben"), add_member(svc, "Cem")
    seen = []

    svc.circulation.checkout(ann.id, "C-001")
    seen.append(status(svc, "C-001"))
    ben_res = svc.queue.place(ben.id, title.id)
    svc.queue.place(cem.id, title.id)
    svc.circulation.return_copy("C-001")
    seen.append((status(svc, "C-001"), svc.reservations.ready_for_copy(1).member_id))
    on(clock, date(2026, 12, 5))                       # Ben's deadline was 12-04
    svc.queue.expire_holds()
    seen.append((status(svc, "C-001"), svc.reservations.ready_for_copy(1).member_id))
    svc.circulation.checkout(cem.id, "C-001")
    seen.append(status(svc, "C-001"))
    svc.circulation.return_copy("C-001")
    seen.append(status(svc, "C-001"))

    assert seen == [CopyStatus.ON_LOAN, (CopyStatus.ON_HOLD, ben.id), (CopyStatus.ON_HOLD, cem.id),
                    CopyStatus.ON_LOAN, CopyStatus.AVAILABLE]
    assert svc.reservations.get(ben_res.id).status == ReservationStatus.EXPIRED


# ---------- NFR-04 atomic operations ----------

def test_TC_NFR_04_failure_during_return_changes_nothing(svc, dune, monkeypatch):
    ann = add_member(svc, "Ann")
    svc.circulation.checkout(ann.id, "C-001")

    def broken(copy):
        raise RuntimeError("simulated failure")
    monkeypatch.setattr(svc.queue, "serve_queue", broken)

    with pytest.raises(RuntimeError):
        svc.circulation.return_copy("C-001")
    loan = svc.loans.open_loan_for_copy(svc.copies.find_by_code("C-001").id)
    assert loan is not None and loan.return_date is None and loan.fine_qepik == 0
    assert status(svc, "C-001") == CopyStatus.ON_LOAN


def test_unrelated_title_is_not_affected(svc, dune):
    add_title(svc, CLEAN_CODE, "Clean Code", "Robert C. Martin", 2008)
    assert [s.title for s in svc.catalogue.search("")] == ["Clean Code", "Dune"]
