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


STAFF_ROUTES = [
    ("GET", "/api/registrations?year=2026&series=MAIN"), ("GET", "/api/protests?status=Pending"),
    ("GET", "/api/editions/2026/persons"), ("GET", "/api/editions/2026/heaviest-carried"),
    ("GET", "/api/reports/medals"), ("GET", "/api/reports/registrations-by-country?year=2026"),
    ("GET", "/api/entries/unregistered"), ("GET", "/api/officials"), ("GET", "/api/prizes?series=MAIN"),
    ("DELETE", "/api/registrations/1"), ("DELETE", "/api/entries/1"),
    ("POST", "/api/results"), ("PATCH", "/api/results/1/Single"), ("POST", "/api/penalties"),
    ("POST", "/api/protests"), ("POST", "/api/protests/1/decide"), ("POST", "/api/awards"),
    ("DELETE", "/api/booths/8/2027"),
]


@pytest.mark.parametrize("method,url", STAFF_ROUTES)
def test_staff_route_needs_login(anon, method, url):
    r = anon.open(url, method=method, json={})
    assert r.status_code == 401 and r.get_json()["error"] == "Staff login required"


PUBLIC_ROUTES = ["/api/editions", "/api/results?year=2026&series=MAIN", "/api/records", "/api/champions",
                 "/api/grand-prix", "/api/entries?year=2027&series=MAIN", "/api/teams",
                 "/api/search/persons?q=ta", "/api/vendors", "/api/editions/2027/booths"]


@pytest.mark.parametrize("url", PUBLIC_ROUTES)
def test_public_reads_need_no_login(anon, url):
    assert anon.get(url).status_code == 200


def test_manage_my_registration_needs_no_login(wanon, fresh_db):
    rid = scalar(fresh_db, "SELECT Registration_ID FROM REGISTRATION WHERE Edition_Year=2027 AND Bib_No=20")
    assert wanon.get(f"/api/registrations/{rid}").status_code == 200
    assert wanon.post(f"/api/registrations/{rid}/cancel").status_code == 200


def test_result_official_comes_from_session(wclient, fresh_db):
    matti = scalar(fresh_db, "SELECT Person_ID FROM STAFF_ACCOUNT WHERE Username='matti'")
    rid = scalar(fresh_db, "SELECT Registration_ID FROM REGISTRATION WHERE Edition_Year=2026 AND Bib_No=49")
    r = wclient.patch(f"/api/results/{rid}/Single", json={"raw_time_s": 60.0, "official_id": matti + 1})
    assert r.status_code == 200, r.get_json()
    assert scalar(fresh_db, "SELECT Recorded_By_Official_ID FROM RESULT WHERE Registration_ID=%s AND Stage='Single'",
                  (rid,)) == matti
