"""Staff login: Flask's signed session cookie holds the logged-in official's ID."""
from functools import wraps

from flask import Flask, session
from werkzeug.security import check_password_hash

from api import ApiError, as_str, body, done, respond
from repo import staff

WRONG_LOGIN = "Wrong username or password"
LOGIN_REQUIRED = "Staff login required"


def staff_required(view):
    """Refuse the request with 401 unless a staff member is logged in."""
    @wraps(view)
    def guarded(*args, **kwargs):
        if not isinstance(session.get("official_id"), int):
            raise ApiError(401, LOGIN_REQUIRED)
        return view(*args, **kwargs)
    return guarded


def current_official_id() -> int:
    """The logged-in official (only call inside a @staff_required view)."""
    return session["official_id"]


def _public(account: dict) -> dict:
    return {k: account[k] for k in ("Person_ID", "Username", "First_Name", "Last_Name", "Duty_Title")}


def register_auth_routes(app: Flask) -> None:
    @app.post("/api/auth/login")
    def api_login():
        data = body()
        username = data.get("username")
        if not isinstance(username, str):
            raise ApiError(400, "username is required")
        username = as_str(username, "username", max_len=40).lower()
        password = data.get("password")
        if not isinstance(password, str) or not 1 <= len(password) <= 200:
            raise ApiError(400, "password is required")
        account = staff.account(username)
        if account is None or not check_password_hash(account["Password_Hash"], password):
            raise ApiError(401, WRONG_LOGIN)
        session.clear()
        session["official_id"] = account["Person_ID"]
        return done("Logged in", staff.ACCOUNT_SQL, official=_public(account))

    @app.post("/api/auth/logout")
    def api_logout():
        session.clear()
        return done("Logged out")

    @app.get("/api/auth/me")
    @staff_required
    def api_me():
        official = staff.official(current_official_id())
        if official is None:                       # account removed since login
            session.clear()
            raise ApiError(401, LOGIN_REQUIRED)
        return respond([], staff.OFFICIAL_SQL, official=official)
