"""Shared pytest fixtures: a freshly loaded `eukonkanto_test` database."""
import os
import subprocess
from pathlib import Path

import pymysql
import pytest

SRC = Path(__file__).resolve().parent.parent
TEST_DB = "eukonkanto_test"

os.environ["DB_NAME"] = TEST_DB
os.environ.setdefault("DB_USER", "phase4")
os.environ.setdefault("DB_PASS", "phase4")


def load_scripts(db_name: str = TEST_DB) -> None:
    """Pipe schema.sql then populate.sql (if present) into the mariadb client,
    with the production database name swapped for `db_name`."""
    sql = ""
    for name in ("schema.sql", "populate.sql"):
        path = SRC / name
        if path.exists():
            sql += path.read_text(encoding="utf8").replace("eukonkanto_db", db_name) + "\n"
    subprocess.run(
        ["mariadb", f"-u{os.environ['DB_USER']}", f"-p{os.environ['DB_PASS']}",
         "--default-character-set=utf8mb4"],
        input=sql.encode("utf8"), check=True, capture_output=True,
    )


def connect():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"), user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"], database=TEST_DB, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, autocommit=True,   # always see the app's commits
    )


_state = {"dirty": True}


@pytest.fixture
def db_conn():
    """Read-only tests: a connection to the loaded test DB (reloaded only if a
    previous test wrote to it)."""
    if _state["dirty"]:
        load_scripts()
        _state["dirty"] = False
    conn = connect()
    yield conn
    conn.close()


@pytest.fixture
def fresh_db():
    """Reload both scripts so a test may write freely; yields a connection."""
    load_scripts()
    _state["dirty"] = True
    conn = connect()
    yield conn
    conn.close()


def q(conn, sql, params=()):
    """Run a query on `conn` and return all rows (dicts)."""
    with conn.cursor() as cur:
        cur.execute(sql, params or None)   # None: no %-interpolation (literal % in LIKE)
        return cur.fetchall()


def scalar(conn, sql, params=()):
    rows = q(conn, sql, params)
    return next(iter(rows[0].values())) if rows else None


@pytest.fixture
def client(db_conn):
    """Flask test client on the loaded (read-only) test database."""
    from app import create_app
    app = create_app()
    app.testing = True
    return app.test_client()


@pytest.fixture
def wclient(fresh_db):
    """Flask test client for tests that write (database reloaded first)."""
    from app import create_app
    app = create_app()
    app.testing = True
    return app.test_client()
