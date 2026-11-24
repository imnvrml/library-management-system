"""Demo data for `flask --app library seed-demo` (not used by the tests' assertions)."""
from datetime import timedelta

from library.domain import Role
from library.services import Services

DEMO_PASSWORD = "library123"

TITLES = [
    ("9780441172719", "Dune", "Frank Herbert", "Ace", 1990, 3),
    ("9780441172696", "Dune Messiah", "Frank Herbert", "Ace", 1987, 1),
    ("9780132350884", "Clean Code", "Robert C. Martin", "Prentice Hall", 2008, 2),
    ("9780201633610", "Design Patterns", "Gamma; Helm; Johnson; Vlissides", "Addison-Wesley", 1994, 1),
    ("9780061120084", "To Kill a Mockingbird", "Harper Lee", "Harper Perennial", 2006, 2),
    ("9780141439518", "Pride and Prejudice", "Jane Austen", "Penguin Classics", 2002, 1),
]


def seed(s: Services) -> str:
    if s.users.find_by_email("librarian@library.local"):
        return "Demo data already present."
    s.members.register("Lale Librarian", "librarian@library.local", None, DEMO_PASSWORD, role=Role.LIBRARIAN)
    ann = s.members.register("Ann Aliyeva", "ann@library.local", "+994501111111", DEMO_PASSWORD)
    ben = s.members.register("Ben Babayev", "ben@library.local", "+994502222222", DEMO_PASSWORD)
    s.members.register("Cem Cavadov", "cem@library.local", None, DEMO_PASSWORD)
    titles = {}
    for isbn, title, author, publisher, year, copies in TITLES:
        t = s.catalogue.add_title(isbn, title, author, publisher, year)
        titles[title] = t
        for k in range(1, copies + 1):
            s.catalogue.add_copy(t.id, f"{title[:3].upper()}-{k:03d}")

    # a loan that is already overdue: borrowed 20 days ago (the clock is moved back temporarily)
    today = s.clock.today()
    original_today = s.clock.today
    s.clock.today = lambda: today - timedelta(days=20)
    try:
        s.circulation.checkout(ben.id, "DUN-001")
    finally:
        s.clock.today = original_today
    s.circulation.checkout(ann.id, "DES-001")
    s.queue.place(ben.id, titles["Design Patterns"].id)
    return ("Demo data created. Log in as librarian@library.local, ann@library.local, ben@library.local "
            f"or cem@library.local with password {DEMO_PASSWORD}.")
