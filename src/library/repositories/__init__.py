"""Repository pattern (models 5.2): the only place with SQL. Each repository maps one table to dataclasses."""
from dataclasses import dataclass
from datetime import date, datetime

from library.db import Database
from library.domain import (
    Copy, CopyStatus, Loan, Payment, Reservation, ReservationStatus, Role, Title, User,
)


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value else None


class _Repository:
    def __init__(self, db: Database):
        self.db = db

    def _rows(self, sql: str, params=()):
        return self.db.connection().execute(sql, params).fetchall()

    def _row(self, sql: str, params=()):
        return self.db.connection().execute(sql, params).fetchone()

    def _exec(self, sql: str, params=()):
        return self.db.connection().execute(sql, params)


class UserRepository(_Repository):
    @staticmethod
    def _map(r) -> User | None:
        if r is None:
            return None
        return User(r["id"], r["email"], r["password_hash"], r["full_name"], r["phone"], Role(r["role"]),
                    bool(r["is_active"]))

    def get(self, id: int) -> User | None:
        return self._map(self._row("SELECT * FROM user WHERE id = ?", (id,)))

    def find_by_email(self, email: str) -> User | None:
        return self._map(self._row("SELECT * FROM user WHERE email = ?", (email.strip().lower(),)))

    def add(self, user: User, created_at: datetime) -> User:
        user.email = user.email.strip().lower()
        user.id = self._exec(
            "INSERT INTO user (email, password_hash, full_name, phone, role, is_active, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user.email, user.password_hash, user.full_name, user.phone, str(user.role), int(user.is_active),
             _iso(created_at)),
        ).lastrowid
        return user

    def set_active(self, id: int, active: bool) -> None:
        self._exec("UPDATE user SET is_active = ? WHERE id = ?", (int(active), id))

    def members(self) -> list[User]:
        return [self._map(r) for r in self._rows("SELECT * FROM user WHERE role = 'member' ORDER BY full_name")]


@dataclass
class TitleSummary:
    """A search result row: the title and its copy counts (FR-06)."""
    id: int
    isbn: str
    title: str
    author: str
    pub_year: int
    available: int
    total: int


class TitleRepository(_Repository):
    @staticmethod
    def _map(r) -> Title | None:
        if r is None:
            return None
        return Title(r["id"], r["isbn"], r["title"], r["author"], r["publisher"], r["pub_year"])

    def get(self, id: int) -> Title | None:
        return self._map(self._row("SELECT * FROM title WHERE id = ?", (id,)))

    def find_by_isbn(self, isbn: str) -> Title | None:
        return self._map(self._row("SELECT * FROM title WHERE isbn = ?", (isbn,)))

    def add(self, title: Title) -> Title:
        title.id = self._exec(
            "INSERT INTO title (isbn, title, author, publisher, pub_year) VALUES (?, ?, ?, ?, ?)",
            (title.isbn, title.title, title.author, title.publisher, title.pub_year),
        ).lastrowid
        return title

    def search(self, text: str) -> list[TitleSummary]:
        # shortcut: SQLite LIKE ignores case only for ASCII letters; enough for English titles, use ICU for others
        pattern = f"%{text.strip()}%"
        rows = self._rows(
            "SELECT t.id, t.isbn, t.title, t.author, t.pub_year, "
            "       COALESCE(SUM(c.status = 'available'), 0) AS available, "
            "       COUNT(c.id) AS total "
            "FROM title t LEFT JOIN copy c ON c.title_id = t.id AND c.status NOT IN ('withdrawn', 'lost') "
            "WHERE t.title LIKE ? OR t.author LIKE ? OR t.isbn LIKE ? "
            "GROUP BY t.id ORDER BY t.title COLLATE NOCASE",
            (pattern, pattern, pattern),
        )
        return [TitleSummary(**dict(r)) for r in rows]


class CopyRepository(_Repository):
    @staticmethod
    def _map(r) -> Copy | None:
        return None if r is None else Copy(r["id"], r["title_id"], r["code"], CopyStatus(r["status"]))

    def get(self, id: int) -> Copy | None:
        return self._map(self._row("SELECT * FROM copy WHERE id = ?", (id,)))

    def find_by_code(self, code: str) -> Copy | None:
        return self._map(self._row("SELECT * FROM copy WHERE code = ?", (code.strip(),)))

    def add(self, copy: Copy) -> Copy:
        copy.id = self._exec(
            "INSERT INTO copy (title_id, code, status) VALUES (?, ?, ?)", (copy.title_id, copy.code, str(copy.status))
        ).lastrowid
        return copy

    def set_status(self, id: int, status: CopyStatus) -> None:
        self._exec("UPDATE copy SET status = ? WHERE id = ?", (str(status), id))

    def count_available(self, title_id: int) -> int:
        return self._row("SELECT COUNT(*) FROM copy WHERE title_id = ? AND status = 'available'", (title_id,))[0]

    def of_title(self, title_id: int) -> list[Copy]:
        return [self._map(r) for r in self._rows("SELECT * FROM copy WHERE title_id = ? ORDER BY code", (title_id,))]


class LoanRepository(_Repository):
    @staticmethod
    def _map(r) -> Loan | None:
        if r is None:
            return None
        return Loan(r["id"], r["copy_id"], r["member_id"], _d(r["checkout_date"]), _d(r["due_date"]),
                    _d(r["return_date"]), r["renewal_count"], r["fine_qepik"])

    def get(self, id: int) -> Loan | None:
        return self._map(self._row("SELECT * FROM loan WHERE id = ?", (id,)))

    def open_loan_for_copy(self, copy_id: int) -> Loan | None:
        return self._map(self._row("SELECT * FROM loan WHERE copy_id = ? AND return_date IS NULL", (copy_id,)))

    def open_loans_of(self, member_id: int) -> list[Loan]:
        return [self._map(r) for r in self._rows(
            "SELECT * FROM loan WHERE member_id = ? AND return_date IS NULL ORDER BY due_date, id", (member_id,))]

    def overdue(self, today: date) -> list[Loan]:
        return [self._map(r) for r in self._rows(
            "SELECT * FROM loan WHERE return_date IS NULL AND due_date < ? ORDER BY due_date, id", (_iso(today),))]

    def add(self, loan: Loan) -> Loan:
        loan.id = self._exec(
            "INSERT INTO loan (copy_id, member_id, checkout_date, due_date, return_date, renewal_count, fine_qepik) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (loan.copy_id, loan.member_id, _iso(loan.checkout_date), _iso(loan.due_date), _iso(loan.return_date),
             loan.renewal_count, loan.fine_qepik),
        ).lastrowid
        return loan

    def update(self, loan: Loan) -> None:
        self._exec(
            "UPDATE loan SET due_date = ?, return_date = ?, renewal_count = ?, fine_qepik = ? WHERE id = ?",
            (_iso(loan.due_date), _iso(loan.return_date), loan.renewal_count, loan.fine_qepik, loan.id),
        )

    def total_fines(self, member_id: int) -> int:
        return self._row("SELECT COALESCE(SUM(fine_qepik), 0) FROM loan WHERE member_id = ?", (member_id,))[0]

    def member_has_title_on_loan(self, member_id: int, title_id: int) -> bool:
        return self._row(
            "SELECT COUNT(*) FROM loan l JOIN copy c ON c.id = l.copy_id "
            "WHERE l.member_id = ? AND c.title_id = ? AND l.return_date IS NULL", (member_id, title_id))[0] > 0

    def history_of(self, member_id: int) -> list[Loan]:
        return [self._map(r) for r in self._rows(
            "SELECT * FROM loan WHERE member_id = ? ORDER BY checkout_date DESC, id DESC", (member_id,))]


class ReservationRepository(_Repository):
    @staticmethod
    def _map(r) -> Reservation | None:
        if r is None:
            return None
        return Reservation(r["id"], r["title_id"], r["member_id"], datetime.fromisoformat(r["placed_at"]),
                           ReservationStatus(r["status"]), r["held_copy_id"], _d(r["pickup_deadline"]))

    def get(self, id: int) -> Reservation | None:
        return self._map(self._row("SELECT * FROM reservation WHERE id = ?", (id,)))

    def waiting_queue(self, title_id: int) -> list[Reservation]:
        return [self._map(r) for r in self._rows(
            "SELECT * FROM reservation WHERE title_id = ? AND status = 'waiting' ORDER BY placed_at, id",
            (title_id,))]

    def active_of(self, member_id: int) -> list[Reservation]:
        return [self._map(r) for r in self._rows(
            "SELECT * FROM reservation WHERE member_id = ? AND status IN ('waiting', 'ready') ORDER BY placed_at, id",
            (member_id,))]

    def expired_holds(self, today: date) -> list[Reservation]:
        return [self._map(r) for r in self._rows(
            "SELECT * FROM reservation WHERE status = 'ready' AND pickup_deadline < ? ORDER BY pickup_deadline, id",
            (_iso(today),))]

    def ready_for_copy(self, copy_id: int) -> Reservation | None:
        return self._map(self._row(
            "SELECT * FROM reservation WHERE held_copy_id = ? AND status = 'ready'", (copy_id,)))

    def add(self, r: Reservation) -> Reservation:
        r.id = self._exec(
            "INSERT INTO reservation (title_id, member_id, placed_at, status, held_copy_id, pickup_deadline) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (r.title_id, r.member_id, _iso(r.placed_at), str(r.status), r.held_copy_id, _iso(r.pickup_deadline)),
        ).lastrowid
        return r

    def update(self, r: Reservation) -> None:
        self._exec(
            "UPDATE reservation SET status = ?, held_copy_id = ?, pickup_deadline = ? WHERE id = ?",
            (str(r.status), r.held_copy_id, _iso(r.pickup_deadline), r.id),
        )


class PaymentRepository(_Repository):
    def add(self, p: Payment) -> Payment:
        p.id = self._exec(
            "INSERT INTO payment (member_id, librarian_id, amount_qepik, paid_at) VALUES (?, ?, ?, ?)",
            (p.member_id, p.librarian_id, p.amount_qepik, _iso(p.paid_at)),
        ).lastrowid
        return p

    def total_paid(self, member_id: int) -> int:
        return self._row("SELECT COALESCE(SUM(amount_qepik), 0) FROM payment WHERE member_id = ?", (member_id,))[0]
