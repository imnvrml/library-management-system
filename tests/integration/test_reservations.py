"""Reservation queue integration tests: TC-RES-07..08, TC-CAT-11, TC-EXP-01..04, TC-CAN-01..03, TC-STR-01..02.

FR-04 AC3, FR-13 to FR-16, reservation state machine (ST-2).
"""
from datetime import date

import pytest

from helpers import add_copies, add_librarian, add_member, add_title
from library.domain import CopyStatus, ReservationStatus
from library.errors import AccessDeniedError, BusinessRuleError


def on(clock, day):
    clock.day = day


@pytest.fixture
def people(svc):
    return {name: add_member(svc, name) for name in ("Ann", "Ben", "Cem", "Dan")}


@pytest.fixture
def dune(svc):
    """*Dune* with one copy C-001, lent to Dan, so the title can be reserved."""
    title = add_title(svc)
    add_copies(svc, title, "C-001")
    return title


def lend_to_dan(svc, people):
    svc.circulation.checkout(people["Dan"].id, "C-001")


def state(svc, reservation):
    return svc.reservations.get(reservation.id).status


def test_TC_RES_07_queue_positions_follow_reservation_order(svc, dune, people):
    lend_to_dan(svc, people)
    ann_res = svc.queue.place(people["Ann"].id, dune.id)
    ben_res = svc.queue.place(people["Ben"].id, dune.id)
    assert ann_res.status == ReservationStatus.WAITING
    assert (svc.queue.position(ann_res), svc.queue.position(ben_res)) == (1, 2)


def test_TC_RES_08_reserve_when_only_copy_is_on_hold(svc, dune, people):
    lend_to_dan(svc, people)
    svc.queue.place(people["Ben"].id, dune.id)
    svc.circulation.return_copy("C-001")          # now On hold for Ben
    assert svc.queue.place(people["Ann"].id, dune.id).status == ReservationStatus.WAITING


def test_reservation_refused_when_copy_on_shelf(svc, dune, people):
    with pytest.raises(BusinessRuleError, match="A copy is available"):
        svc.queue.place(people["Ann"].id, dune.id)


def test_TC_CAT_11_new_copy_goes_to_waiting_member(svc, dune, people):
    lend_to_dan(svc, people)
    ann_res = svc.queue.place(people["Ann"].id, dune.id)
    new_copy = svc.catalogue.add_copy(dune.id, "C-002")
    assert new_copy.status == CopyStatus.ON_HOLD
    ann_res = svc.reservations.get(ann_res.id)
    assert ann_res.status == ReservationStatus.READY and ann_res.held_copy_id == new_copy.id
    assert ann_res.pickup_deadline == date(2026, 12, 4)


@pytest.fixture
def ann_holds_from_12_15(svc, clock, dune, people):
    """Ann's hold starts 12-15 with deadline 12-18."""
    lend_to_dan(svc, people)
    res = svc.queue.place(people["Ann"].id, dune.id)
    on(clock, date(2026, 12, 15))
    svc.circulation.return_copy("C-001")
    assert svc.reservations.get(res.id).pickup_deadline == date(2026, 12, 18)
    return res


def test_TC_EXP_01_hold_expires_after_deadline(svc, clock, ann_holds_from_12_15):
    on(clock, date(2026, 12, 19))
    assert svc.queue.expire_holds() == 1
    assert state(svc, ann_holds_from_12_15) == ReservationStatus.EXPIRED
    assert svc.copies.find_by_code("C-001").status == CopyStatus.AVAILABLE


def test_TC_EXP_02_expired_hold_passes_to_next_member(svc, clock, dune, people):
    lend_to_dan(svc, people)
    svc.queue.place(people["Ann"].id, dune.id)
    ben_res = svc.queue.place(people["Ben"].id, dune.id)
    on(clock, date(2026, 12, 15))
    svc.circulation.return_copy("C-001")
    on(clock, date(2026, 12, 19))
    svc.queue.expire_holds()
    ben_res = svc.reservations.get(ben_res.id)
    assert ben_res.status == ReservationStatus.READY and ben_res.pickup_deadline == date(2026, 12, 22)
    assert svc.copies.find_by_code("C-001").status == CopyStatus.ON_HOLD


def test_TC_EXP_03_nothing_expires_on_deadline_day(svc, clock, ann_holds_from_12_15):
    on(clock, date(2026, 12, 18))
    assert svc.queue.expire_holds() == 0
    assert state(svc, ann_holds_from_12_15) == ReservationStatus.READY


def test_TC_EXP_04_checkout_processes_expired_holds_first(svc, clock, dune, people):
    lend_to_dan(svc, people)
    svc.queue.place(people["Ann"].id, dune.id)
    svc.queue.place(people["Ben"].id, dune.id)
    on(clock, date(2026, 12, 15))
    svc.circulation.return_copy("C-001")
    on(clock, date(2026, 12, 19))                 # no explicit expire_holds()
    assert svc.circulation.checkout(people["Ben"].id, "C-001").member_id == people["Ben"].id


def test_TC_CAN_01_cancel_waiting_moves_queue_up(svc, dune, people):
    lend_to_dan(svc, people)
    ann_res = svc.queue.place(people["Ann"].id, dune.id)
    ben_res = svc.queue.place(people["Ben"].id, dune.id)
    svc.queue.place(people["Cem"].id, dune.id)
    svc.queue.cancel(ann_res.id, people["Ann"])
    assert state(svc, ann_res) == ReservationStatus.CANCELLED
    assert svc.queue.position(svc.reservations.get(ben_res.id)) == 1


def test_TC_CAN_02_cancel_ready_passes_copy_to_next(svc, dune, people):
    lend_to_dan(svc, people)
    ann_res = svc.queue.place(people["Ann"].id, dune.id)
    ben_res = svc.queue.place(people["Ben"].id, dune.id)
    svc.circulation.return_copy("C-001")
    svc.queue.cancel(ann_res.id, people["Ann"])
    assert state(svc, ben_res) == ReservationStatus.READY
    assert svc.reservations.ready_for_copy(svc.copies.find_by_code("C-001").id).member_id == people["Ben"].id


def test_TC_CAN_03_cancel_ready_with_empty_queue(svc, dune, people):
    lend_to_dan(svc, people)
    ann_res = svc.queue.place(people["Ann"].id, dune.id)
    svc.circulation.return_copy("C-001")
    svc.queue.cancel(ann_res.id, people["Ann"])
    assert svc.copies.find_by_code("C-001").status == CopyStatus.AVAILABLE


def test_TC_STR_01_cannot_cancel_fulfilled_reservation(svc, dune, people):
    lend_to_dan(svc, people)
    ann_res = svc.queue.place(people["Ann"].id, dune.id)
    svc.circulation.return_copy("C-001")
    svc.circulation.checkout(people["Ann"].id, "C-001")
    with pytest.raises(BusinessRuleError, match="Reservation is not active"):
        svc.queue.cancel(ann_res.id, people["Ann"])


def test_TC_STR_02_cannot_cancel_expired_reservation(svc, clock, ann_holds_from_12_15, people):
    on(clock, date(2026, 12, 19))
    svc.queue.expire_holds()
    with pytest.raises(BusinessRuleError, match="Reservation is not active"):
        svc.queue.cancel(ann_holds_from_12_15.id, people["Ann"])


def test_member_cannot_cancel_another_members_reservation(svc, dune, people):
    lend_to_dan(svc, people)
    ben_res = svc.queue.place(people["Ben"].id, dune.id)
    with pytest.raises(AccessDeniedError):
        svc.queue.cancel(ben_res.id, people["Ann"])
    assert state(svc, ben_res) == ReservationStatus.WAITING


def test_librarian_can_cancel_any_reservation(svc, dune, people):
    lend_to_dan(svc, people)
    ben_res = svc.queue.place(people["Ben"].id, dune.id)
    svc.queue.cancel(ben_res.id, add_librarian(svc))
    assert state(svc, ben_res) == ReservationStatus.CANCELLED
