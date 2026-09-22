from fastapi.testclient import TestClient
from fastapi import FastAPI

import api


client = TestClient(api.app, raise_server_exceptions=False)
IMMUTABLE_CACHE = "public, max-age=31536000, immutable"


def test_page_prefetch_txt_is_served_for_exported_route(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: True)

    response = client.get("/news/__next.news.__PAGE__.txt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/x-component")


def test_page_prefetch_txt_is_served_for_scanner_route(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: True)

    response = client.get("/scanner/__next.scanner.__PAGE__.txt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/x-component")


def test_next_static_assets_use_immutable_cache_headers(tmp_path):
    asset_path = tmp_path / "static" / "chunks" / "app-test.js"
    asset_path.parent.mkdir(parents=True)
    asset_path.write_text("window.__asset_test = true;", encoding="utf-8")

    test_app = FastAPI()
    test_app.mount("/_next", api.ImmutableStaticFiles(directory=str(tmp_path)), name="next-static")
    local_client = TestClient(test_app)

    response = local_client.get("/_next/static/chunks/app-test.js")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == IMMUTABLE_CACHE

    conditional = local_client.get(
        "/_next/static/chunks/app-test.js",
        headers={"If-None-Match": response.headers["ETag"]},
    )

    assert conditional.status_code == 304
    assert conditional.headers["Cache-Control"] == IMMUTABLE_CACHE


def test_unknown_legacy_api_routes_return_json_404(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: True)

    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["detail"] == "API route not found"


def test_plain_http_websocket_path_does_not_return_frontend_shell(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: True)

    response = client.get("/ws")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["detail"] == "WebSocket route requires a WebSocket upgrade"
