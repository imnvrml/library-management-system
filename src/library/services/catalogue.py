"""Catalogue: ISBN rules (BR-11) and CatalogueService (FR-03 to FR-06)."""
from library.clock import Clock
from library.db import Database
from library.domain import Copy, CopyStatus, Title
from library.errors import BusinessRuleError
from library.repositories import CopyRepository, TitleRepository, TitleSummary
from library.rules import Rules


def normalize_isbn(isbn: str) -> str:
    return isbn.replace("-", "").replace(" ", "").strip()


def is_valid_isbn(isbn: str) -> bool:
    """BR-11: 13 digits after removing hyphens/spaces, weights 1 and 3, weighted sum divisible by 10."""
    digits = normalize_isbn(isbn)
    if len(digits) != 13 or not digits.isdigit():
        return False
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits))
    return total % 10 == 0


class CatalogueService:
    def __init__(self, db: Database, titles: TitleRepository, copies: CopyRepository, clock: Clock, rules: Rules,
                 queue=None):
        self.db, self.titles, self.copies, self.clock, self.rules = db, titles, copies, clock, rules
        self.queue = queue  # ReservationService; set after construction because the two depend on each other

    is_valid_isbn = staticmethod(is_valid_isbn)

    def add_title(self, isbn: str, title: str, author: str, publisher: str | None, year) -> Title:
        """FR-03."""
        isbn = normalize_isbn(isbn or "")
        title, author = (title or "").strip(), (author or "").strip()
        if not is_valid_isbn(isbn):
            raise BusinessRuleError("Invalid ISBN")
        if not title:
            raise BusinessRuleError("Title is required")
        if not author:
            raise BusinessRuleError("Author is required")
        current = self.clock.today().year
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None
        if year is None or not self.rules.min_year <= year <= current:
            raise BusinessRuleError(f"Publication year must be between {self.rules.min_year} and {current}")
        with self.db.transaction():
            if self.titles.find_by_isbn(isbn):
                raise BusinessRuleError("ISBN already exists")
            return self.titles.add(Title(None, isbn, title, author, (publisher or "").strip() or None, year))

    def add_copy(self, title_id: int, code: str) -> Copy:
        """FR-04: a new copy is Available, or goes to the reservation queue (AC3)."""
        code = (code or "").strip()
        if not code:
            raise BusinessRuleError("Copy code is required")
        with self.db.transaction():
            if self.titles.get(title_id) is None:
                raise BusinessRuleError("Title not found")
            if self.copies.find_by_code(code):
                raise BusinessRuleError("Copy code already exists")
            copy = self.copies.add(Copy(None, title_id, code, CopyStatus.AVAILABLE))
            if self.queue is not None:
                self.queue.serve_queue(copy)
            return self.copies.get(copy.id)

    def withdraw_copy(self, copy_id: int) -> Copy:
        """FR-05: only a copy on the shelf can be withdrawn."""
        with self.db.transaction():
            copy = self.copies.get(copy_id)
            if copy is None:
                raise BusinessRuleError("Copy not found")
            if copy.status != CopyStatus.AVAILABLE:
                raise BusinessRuleError("Copy is not on the shelf")
            self.copies.set_status(copy.id, CopyStatus.WITHDRAWN)
            return self.copies.get(copy.id)

    def search(self, text: str) -> list[TitleSummary]:
        """FR-06: by part of title, author or ISBN; empty text lists everything alphabetically."""
        return self.titles.search(text or "")
