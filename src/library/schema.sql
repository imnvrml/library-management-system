-- Logical ERD (docs/models/06-erd-logical.puml), 3NF. Dates are ISO-8601 text, money is integer qəpik.

CREATE TABLE IF NOT EXISTS user (
    id            INTEGER PRIMARY KEY,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    full_name     TEXT    NOT NULL,
    phone         TEXT,
    role          TEXT    NOT NULL CHECK (role IN ('librarian', 'member')),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS title (
    id        INTEGER PRIMARY KEY,
    isbn      TEXT    NOT NULL UNIQUE CHECK (length(isbn) = 13),
    title     TEXT    NOT NULL,
    author    TEXT    NOT NULL,
    publisher TEXT,
    -- upper bound (current year) is checked in CatalogueService because it changes every year
    pub_year  INTEGER NOT NULL CHECK (pub_year >= 1800)
);

CREATE TABLE IF NOT EXISTS copy (
    id       INTEGER PRIMARY KEY,
    title_id INTEGER NOT NULL REFERENCES title (id),
    code     TEXT    NOT NULL UNIQUE,
    status   TEXT    NOT NULL CHECK (status IN ('available', 'on_loan', 'on_hold', 'withdrawn', 'lost'))
);

CREATE TABLE IF NOT EXISTS loan (
    id            INTEGER PRIMARY KEY,
    copy_id       INTEGER NOT NULL REFERENCES copy (id),
    member_id     INTEGER NOT NULL REFERENCES user (id),
    checkout_date TEXT    NOT NULL,
    due_date      TEXT    NOT NULL,
    return_date   TEXT,
    renewal_count INTEGER NOT NULL DEFAULT 0 CHECK (renewal_count BETWEEN 0 AND 2),
    fine_qepik    INTEGER NOT NULL DEFAULT 0 CHECK (fine_qepik >= 0)
);
-- at most one open loan per copy
CREATE UNIQUE INDEX IF NOT EXISTS one_open_loan_per_copy ON loan (copy_id) WHERE return_date IS NULL;

CREATE TABLE IF NOT EXISTS reservation (
    id              INTEGER PRIMARY KEY,
    title_id        INTEGER NOT NULL REFERENCES title (id),
    member_id       INTEGER NOT NULL REFERENCES user (id),
    placed_at       TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK (status IN ('waiting', 'ready', 'fulfilled', 'expired', 'cancelled')),
    held_copy_id    INTEGER REFERENCES copy (id),
    pickup_deadline TEXT
);

CREATE TABLE IF NOT EXISTS payment (
    id           INTEGER PRIMARY KEY,
    member_id    INTEGER NOT NULL REFERENCES user (id),
    librarian_id INTEGER NOT NULL REFERENCES user (id),
    amount_qepik INTEGER NOT NULL CHECK (amount_qepik > 0),
    paid_at      TEXT    NOT NULL
);
