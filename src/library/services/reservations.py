"""ReservationService (FR-13 to FR-16): the reservation queue, holds and their expiry."""
from dataclasses import dataclass
from datetime import timedelta

from library.clock import Clock
from library.db import Database
from library.domain import Copy, CopyStatus, Reservation, ReservationStatus, Role, User
from library.errors import AccessDeniedError, BusinessRuleError
from library.repositories import CopyRepository, LoanRepository, ReservationRepository, TitleRepository
from library.rules import Rules
from library.services.policies import EligibilityPolicy


@dataclass
class ReservationView:
    """A reservation as the member sees it (FR-17): no other members' names (NFR-06)."""
    reservation: Reservation
    title: str
    position: int  # 1 = next in line; 0 = ready for pickup


class ReservationService:
    def __init__(self, db: Database, reservations: ReservationRepository, copies: CopyRepository,
                 loans: LoanRepository, titles: TitleRepository, policy: EligibilityPolicy, clock: Clock,
                 rules: Rules):
        self.db, self.reservations, self.copies, self.loans, self.titles = db, reservations, copies, loans, titles
        self.policy, self.clock, self.rules = policy, clock, rules

    def place(self, member_id: int, title_id: int) -> Reservation:
        """FR-13 (UC-08)."""
        with self.db.transaction():
            self.expire_holds()
            if self.titles.get(title_id) is None:
                raise BusinessRuleError("Title not found")
            active = self.reservations.active_of(member_id)
            refusal = self.policy.reservation_refusal(
                available=self.copies.count_available(title_id),
                already_reserved=any(r.title_id == title_id for r in active),
                on_loan=self.loans.member_has_title_on_loan(member_id, title_id),
                active=len(active),
            )
            if refusal:
                raise BusinessRuleError(refusal)
            return self.reservations.add(Reservation(None, title_id, member_id, self.clock.now()))

    def cancel(self, reservation_id: int, actor: User) -> Reservation:
        """FR-16 (UC-09). Cancelling a ready reservation passes the held copy on."""
        with self.db.transaction():
            r = self.reservations.get(reservation_id)
            if r is None:
                raise BusinessRuleError("Reservation not found")
            if actor.role == Role.MEMBER and r.member_id != actor.id:
                raise AccessDeniedError()
            if not r.status.is_active:
                raise BusinessRuleError("Reservation is not active")
            was_ready = r.status == ReservationStatus.READY
            r.status = ReservationStatus.CANCELLED
            self.reservations.update(r)
            if was_ready:
                self.serve_queue(self.copies.get(r.held_copy_id))
            return r

    def serve_queue(self, copy: Copy) -> bool:
        """FR-14 (UC-15): give a free copy to the oldest Waiting reservation, else put it on the shelf."""
        queue = self.reservations.waiting_queue(copy.title_id)
        if not queue:
            self.copies.set_status(copy.id, CopyStatus.AVAILABLE)
            return False
        first = queue[0]
        first.status = ReservationStatus.READY
        first.held_copy_id = copy.id
        first.pickup_deadline = self.clock.today() + timedelta(days=self.rules.pickup_days)
        self.reservations.update(first)
        self.copies.set_status(copy.id, CopyStatus.ON_HOLD)
        return True

    def expire_holds(self) -> int:
        """FR-15 (UC-14): holds not collected by the end of the deadline day expire. Returns how many."""
        with self.db.transaction():
            expired = self.reservations.expired_holds(self.clock.today())
            for r in expired:
                r.status = ReservationStatus.EXPIRED
                self.reservations.update(r)
                self.serve_queue(self.copies.get(r.held_copy_id))
            return len(expired)

    def fulfil_hold(self, copy: Copy, member_id: int) -> None:
        r = self.reservations.ready_for_copy(copy.id)
        if r is not None and r.member_id == member_id:
            r.status = ReservationStatus.FULFILLED
            self.reservations.update(r)

    def holder_of(self, copy: Copy) -> int | None:
        r = self.reservations.ready_for_copy(copy.id)
        return r.member_id if r else None

    def has_waiting(self, title_id: int, exclude_member_id: int) -> bool:
        return any(r.member_id != exclude_member_id for r in self.reservations.waiting_queue(title_id))

    def position(self, reservation: Reservation) -> int:
        if reservation.status == ReservationStatus.READY:
            return 0
        ids = [r.id for r in self.reservations.waiting_queue(reservation.title_id)]
        return ids.index(reservation.id) + 1 if reservation.id in ids else 0

    def active_of(self, member_id: int) -> list[ReservationView]:
        return [ReservationView(r, self.titles.get(r.title_id).title, self.position(r))
                for r in self.reservations.active_of(member_id)]
