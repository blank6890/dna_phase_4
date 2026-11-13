"""Task 5: db helpers, error mapping and the app skeleton."""
import pytest

import db
from api import ApiError, parse_int, parse_choice, parse_str


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["rows"] == [{"db": "eukonkanto_test"}]
    assert body["sql"] == "SELECT DATABASE() AS db"


def test_like_escapes():
    assert db.like("50%_x") == "%50\\%\\_x%"
    assert db.like("a\\b") == "%a\\\\b%"


def test_query_converts_types(db_conn):
    row = db.query("SELECT Fee_Paid_EUR, Registered_At, Edition_Year FROM REGISTRATION "
                   "WHERE Edition_Year=%s AND Bib_No=%s", (2026, 62))[0]
    assert row["Fee_Paid_EUR"] == 55.0 and isinstance(row["Fee_Paid_EUR"], float)
    assert isinstance(row["Registered_At"], str) and row["Registered_At"].startswith("2026-")


def test_query_literal_percent_without_params(db_conn):
    assert db.query("SELECT 'F%hr' AS x") == [{"x": "F%hr"}]


def test_parse_int_rejects_text():
    from app import create_app
    with create_app().test_request_context("/?year=abc"):
        with pytest.raises(ApiError) as e:
            parse_int("year")
        assert e.value.status == 400 and "year" in e.value.message


def test_parse_choice_and_str():
    from app import create_app
    with create_app().test_request_context("/?series=XX&q=" + "a" * 200):
        with pytest.raises(ApiError):
            parse_choice("series", {"MAIN", "SPR"})
        with pytest.raises(ApiError):
            parse_str("q", max_len=100)
    with create_app().test_request_context("/?series=MAIN"):
        assert parse_choice("series", {"MAIN"}) == "MAIN"
        assert parse_int("year", required=False) is None


def _app_with_route(sql):
    from app import create_app
    app = create_app()
    app.testing = True

    @app.route("/api/_test")
    def _t():
        db.execute(sql)
        return {"ok": True}
    return app.test_client()


def test_trigger_maps_to_409(fresh_db):
    c = _app_with_route("INSERT INTO EXHIBITS_AT VALUES (2, 2025, '4x4', 90, FALSE, TRUE)")
    r = c.get("/api/_test")
    assert r.status_code == 409
    assert "70 EUR" in r.get_json()["error"]


def test_duplicate_bib_maps_to_message(fresh_db):
    c = _app_with_route("UPDATE REGISTRATION SET Bib_No=62 WHERE Edition_Year=2026 AND Bib_No=49")
    r = c.get("/api/_test")
    assert r.status_code == 409
    assert r.get_json()["error"] == "Bib number already used in this edition"


def test_fk_restrict_maps_to_message(fresh_db):
    c = _app_with_route("DELETE FROM SERIES WHERE Series_Code='MAIN'")
    r = c.get("/api/_test")
    assert r.status_code == 409
    assert "other records still refer" in r.get_json()["error"]


def test_unknown_api_route_is_json_404(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and "error" in r.get_json()
