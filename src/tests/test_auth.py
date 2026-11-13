"""Staff login: accounts, session cookie and the guard on Staff Desk routes."""
import pytest

from conftest import STAFF, scalar

LOGIN = {"username": STAFF[0], "password": STAFF[1]}


def test_login_ok_and_me(anon):
    r = anon.post("/api/auth/login", json=LOGIN)
    assert r.status_code == 200 and r.get_json()["official"]["First_Name"] == "Matti"
    assert anon.get("/api/auth/me").get_json()["official"]["Username"] == "matti"


def test_login_wrong_password_and_unknown_user_same_message(anon):
    a = anon.post("/api/auth/login", json={"username": "matti", "password": "nope"})
    b = anon.post("/api/auth/login", json={"username": "nobody", "password": "staff2027"})
    assert a.status_code == b.status_code == 401
    assert a.get_json()["error"] == b.get_json()["error"] == "Wrong username or password"
    assert anon.get("/api/auth/me").status_code == 401


def test_login_username_case_and_spaces(anon):
    assert anon.post("/api/auth/login", json={"username": " Matti ", "password": "staff2027"}).status_code == 200


def test_login_password_not_trimmed(anon):
    assert anon.post("/api/auth/login", json={"username": "matti", "password": " staff2027 "}).status_code == 401


def test_login_bad_payload_400(anon):
    for payload in ({}, {"username": 5, "password": "x"}, {"username": "matti", "password": 5}, [1, 2]):
        assert anon.post("/api/auth/login", json=payload).status_code == 400, payload


def test_logout_ends_session(client):
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_cookie_flags(anon):
    cookie = anon.post("/api/auth/login", json=LOGIN).headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie


def test_cookie_from_other_secret_is_401(anon):
    anon.post("/api/auth/login", json=LOGIN)
    from app import create_app
    other = create_app()                                  # new random secret, like a server restart
    other.testing = True
    c2 = other.test_client()
    c2.set_cookie("session", anon.get_cookie("session").value)
    assert c2.get("/api/auth/me").status_code == 401
