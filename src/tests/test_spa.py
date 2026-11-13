"""Task 11: Flask serves the built React app with an SPA fallback."""
from app import create_app


def _client(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>Eukonkanto</title>", encoding="utf8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log(1)", encoding="utf8")
    app = create_app(frontend_dist=tmp_path)
    app.testing = True
    return app.test_client()


def test_spa_fallback(tmp_path):
    c = _client(tmp_path)
    r = c.get("/results")
    assert r.status_code == 200 and b"Eukonkanto" in r.data
    assert c.get("/").status_code == 200


def test_static_asset_served(tmp_path):
    assert _client(tmp_path).get("/assets/app.js").data == b"console.log(1)"


def test_api_404_stays_json(tmp_path):
    r = _client(tmp_path).get("/api/nope")
    assert r.status_code == 404 and r.get_json() == {"error": "Not found"}
