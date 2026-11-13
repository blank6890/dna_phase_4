"""Thin PyMySQL helpers. Every query in the app is a raw SQL string with %s parameters."""
import datetime as dt
from contextlib import contextmanager
from decimal import Decimal

import pymysql

from config import get_db_config


def get_connection() -> pymysql.connections.Connection:
    return pymysql.connect(**get_db_config(), cursorclass=pymysql.cursors.DictCursor, autocommit=False)


def _clean(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, dt.date):
        return value.isoformat()
    return value


def clean_rows(rows) -> list[dict]:
    return [{k: _clean(v) for k, v in row.items()} for row in rows]


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a read query and return JSON-ready rows."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or None)   # None: no %-formatting when there are no params
            return clean_rows(cur.fetchall())
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    """Run one write statement, commit, and return lastrowid."""
    with transaction() as cur:
        cur.execute(sql, params or None)
        return cur.lastrowid


@contextmanager
def transaction():
    """Yield a cursor; commit on success, roll back and re-raise on any error."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def like(term: str) -> str:
    """Wrap user text for LIKE, matching %, _ and backslash literally."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
