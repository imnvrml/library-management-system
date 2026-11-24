"""Domain objects (design class diagram 5.2). Money is in qəpik (BR-14)."""
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class Role(StrEnum):
    LIBRARIAN = "librarian"
    MEMBER = "member"


class CopyStatus(StrEnum):
    AVAILABLE = "available"
    ON_LOAN = "on_loan"
    ON_HOLD = "on_hold"
    WITHDRAWN = "withdrawn"
    LOST = "lost"


class ReservationStatus(StrEnum):
    WAITING = "waiting"
    READY = "ready"
    FULFILLED = "fulfilled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

    @property
    def is_active(self) -> bool:
        return self in (ReservationStatus.WAITING, ReservationStatus.READY)


@dataclass
class User:
    id: int | None
    email: str
    password_hash: str
    full_name: str
    phone: str | None
    role: Role
    is_active: bool = True


@dataclass
class Title:
    id: int | None
    isbn: str
    title: str
    author: str
    publisher: str | None
    pub_year: int


@dataclass
class Copy:
    id: int | None
    title_id: int
    code: str
    status: CopyStatus = CopyStatus.AVAILABLE


@dataclass
class Loan:
    id: int | None
    copy_id: int
    member_id: int
    checkout_date: date
    due_date: date
    return_date: date | None = None
    renewal_count: int = 0
    fine_qepik: int = 0

    def is_overdue(self, today: date) -> bool:
        """BR-06: overdue when today is later than the due date and the copy is not back."""
        return self.return_date is None and today > self.due_date


@dataclass
class Reservation:
    id: int | None
    title_id: int
    member_id: int
    placed_at: datetime
    status: ReservationStatus = ReservationStatus.WAITING
    held_copy_id: int | None = None
    pickup_deadline: date | None = None


@dataclass
class Payment:
    id: int | None
    member_id: int
    librarian_id: int
    amount_qepik: int
    paid_at: datetime


@dataclass(frozen=True)
class MemberFacts:
    """What EligibilityPolicy needs to know about a borrower (models 5.1)."""
    is_active: bool
    active_loans: int
    has_overdue: bool
    balance_qepik: int


def azn(qepik: int) -> str:
    """Format qəpik as AZN with two decimals, e.g. 40 -> '0.40 AZN'."""
    return f"{qepik // 100}.{qepik % 100:02d} AZN"
