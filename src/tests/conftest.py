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
        cursorclass=pymysql.cursors.DictCursor, autocommit=False,
    )


@pytest.fixture(scope="session")
def db_conn():
    load_scripts()
    conn = connect()
    yield conn
    conn.close()


@pytest.fixture
def fresh_db():
    """Reload both scripts so a test may write freely; yields a connection."""
    load_scripts()
    conn = connect()
    yield conn
    conn.close()
    load_scripts()
