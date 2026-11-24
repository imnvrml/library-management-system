"""Database connection and transactions (design class diagram 5.2, NFR-04)."""
import sqlite3
import threading
from contextlib import contextmanager
from importlib import resources


class Database:
    def __init__(self, path: str):
        self.path = path
        self._local = threading.local()
        # ":memory:" exists only inside one connection, so it is shared; files get one connection per thread
        self._shared = self._open() if path == ":memory:" else None

    def _open(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def connection(self) -> sqlite3.Connection:
        if self._shared is not None:
            return self._shared
        con = getattr(self._local, "con", None)
        if con is None:
            con = self._local.con = self._open()
        return con

    @contextmanager
    def transaction(self):
        """All-or-nothing block. Nested blocks join the outer one, which commits or rolls back once."""
        con = self.connection()
        if con.in_transaction:
            yield con
            return
        con.execute("BEGIN IMMEDIATE")
        try:
            yield con
        except BaseException:
            con.execute("ROLLBACK")
            raise
        con.execute("COMMIT")

    def init_schema(self) -> None:
        sql = resources.files("library").joinpath("schema.sql").read_text(encoding="utf-8")
        self.connection().executescript(sql)

    def close(self) -> None:
        if self._shared is not None:
            self._shared.close()
        con = getattr(self._local, "con", None)
        if con is not None:
            con.close()
            self._local.con = None
