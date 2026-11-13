"""Request parsing, JSON responses and database-error mapping shared by every route."""
import datetime as dt
import re

import pymysql
from flask import jsonify, request


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def respond(rows, *sqls):
    return jsonify(rows=rows, sql="\n\n".join(sqls))


def done(message, *sqls, **extra):
    return jsonify(ok=True, message=message, sql="\n\n".join(sqls), **extra)


# ---------------------------------------------------------------- value validators
def as_int(value, name, required=True, minimum=None):
    if value is None or value == "":
        if required:
            raise ApiError(400, f"{name} is required")
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ApiError(400, f"{name} must be a whole number") from None
    if isinstance(value, bool) or (minimum is not None and number < minimum):
        raise ApiError(400, f"{name} must be a whole number of at least {minimum}")
    return number


def as_float(value, name, required=True):
    if value is None or value == "":
        if required:
            raise ApiError(400, f"{name} is required")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ApiError(400, f"{name} must be a number") from None
    if number < 0 or number != number:
        raise ApiError(400, f"{name} must be a positive number")
    return number


def as_str(value, name, required=True, max_len=100):
    if value is None or str(value).strip() == "":
        if required:
            raise ApiError(400, f"{name} is required")
        return None
    if not isinstance(value, (str, int, float)):
        raise ApiError(400, f"{name} must be text")
    text = str(value).strip()
    if len(text) > max_len:
        raise ApiError(400, f"{name} must be at most {max_len} characters")
    return text


def as_choice(value, name, allowed, required=True):
    if value is None or value == "":
        if required:
            raise ApiError(400, f"{name} is required")
        return None
    if value not in allowed:
        raise ApiError(400, f"{name} must be one of: {', '.join(sorted(allowed))}")
    return value


def as_date(value, name, required=True):
    text = as_str(value, name, required, max_len=10)
    if text is None:
        return None
    try:
        return dt.date.fromisoformat(text).isoformat()
    except ValueError:
        raise ApiError(400, f"{name} must be a date (YYYY-MM-DD)") from None


def as_datetime(value, name, required=True):
    text = as_str(value, name, required, max_len=19)
    if text is None:
        return None
    try:
        return dt.datetime.fromisoformat(text).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ApiError(400, f"{name} must be a date and time (YYYY-MM-DD HH:MM)") from None


# ---------------------------------------------------------------- request readers
def _raw(name):
    if name in request.args:
        return request.args.get(name)
    body = request.get_json(silent=True)
    return body.get(name) if isinstance(body, dict) else None


def body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "Request body must be a JSON object")
    return data


def parse_int(name, required=True, minimum=None):
    return as_int(_raw(name), name, required, minimum)


def parse_choice(name, allowed, required=True):
    return as_choice(_raw(name), name, allowed, required)


def parse_str(name, max_len=100, required=True):
    return as_str(_raw(name), name, required, max_len)


# ---------------------------------------------------------------- error mapping
def _db_error(err):
    code = err.args[0] if err.args else None
    msg = err.args[1] if len(err.args) > 1 else str(err)
    if code == 1644:                                   # SIGNAL from a trigger
        return 409, msg
    if code == 1062:
        if "uq_reg_bib" in msg:
            return 409, "Bib number already used in this edition"
        if "uq_person_email" in msg:
            return 409, "A person with this e-mail address already exists"
        if "uq_reg_entry_race" in msg:
            return 409, "This entry is already registered for this race"
        if "PRIMARY" in msg:
            return 409, "This record already exists"
        return 409, "Duplicate value"
    if code == 1451:
        return 409, "Cannot delete: other records still refer to this one"
    if code == 1452:
        return 409, "Referenced record does not exist"
    if code in (3819, 4025):
        m = re.search(r"CONSTRAINT `([^`]+)`", msg)
        return 409, f"Value violates rule: {m.group(1) if m else 'check constraint'}"
    if code == 1048:
        m = re.search(r"Column '([^']+)'", msg)
        return 400, f"{m.group(1) if m else 'A value'} is required"
    return 500, "Database error"


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def _api_error(e):
        return jsonify(error=e.message), e.status

    @app.errorhandler(pymysql.err.MySQLError)
    def _mysql_error(e):
        status, message = _db_error(e)
        if status == 500:
            app.logger.exception("database error")
        return jsonify(error=message), status

    @app.errorhandler(404)
    def _not_found(e):
        if request.path.startswith("/api/"):
            return jsonify(error="Not found"), 404
        return e
