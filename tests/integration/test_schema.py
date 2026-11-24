"""Database schema tests (models 4.2, NFR-04, NFR-06)."""
import sqlite3

import pytest


def columns(db, table):
    return [row["name"] for row in db.connection().execute(f"PRAGMA table_info({table})")]


def test_schema_has_the_six_tables_of_the_logical_erd(db):
    rows = db.connection().execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    assert {r["name"] for r in rows} >= {"user", "title", "copy", "loan", "reservation", "payment"}


def test_TC_NFR_06_user_table_stores_only_lending_data(db):
    assert columns(db, "user") == [
        "id", "email", "password_hash", "full_name", "phone", "role", "is_active", "created_at",
    ]


def test_transaction_rolls_back_on_error(db):
    with pytest.raises(RuntimeError):
        with db.transaction():
            db.connection().execute(
                "INSERT INTO title (isbn, title, author, publisher, pub_year) "
                "VALUES ('9780441172719', 'Dune', 'Frank Herbert', NULL, 1990)"
            )
            raise RuntimeError("boom")
    assert db.connection().execute("SELECT COUNT(*) FROM title").fetchone()[0] == 0


def test_nested_transaction_commits_once_at_the_outer_level(db):
    with db.transaction():
        with db.transaction():
            db.connection().execute(
                "INSERT INTO title (isbn, title, author, publisher, pub_year) "
                "VALUES ('9780441172719', 'Dune', 'Frank Herbert', NULL, 1990)"
            )
        assert db.connection().in_transaction
    assert db.connection().execute("SELECT COUNT(*) FROM title").fetchone()[0] == 1


def test_one_open_loan_per_copy_is_enforced(db):
    con = db.connection()
    con.execute("INSERT INTO title (isbn, title, author, pub_year) VALUES ('9780441172719', 'Dune', 'F. Herbert', 1990)")
    con.execute("INSERT INTO copy (title_id, code, status) VALUES (1, 'C-001', 'on_loan')")
    con.execute(
        "INSERT INTO user (email, password_hash, full_name, role, is_active, created_at) "
        "VALUES ('ann@example.com', 'x', 'Ann', 'member', 1, '2026-12-01T10:00:00')"
    )
    insert_loan = (
        "INSERT INTO loan (copy_id, member_id, checkout_date, due_date, renewal_count, fine_qepik) "
        "VALUES (1, 1, '2026-12-01', '2026-12-15', 0, 0)"
    )
    con.execute(insert_loan)
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(insert_loan)
