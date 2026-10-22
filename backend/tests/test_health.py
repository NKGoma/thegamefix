from fastapi.testclient import TestClient

from delegationlab.api.health import OllamaStatus, get_ollama_probe
from delegationlab.settings import Settings


def test_health_db_is_ok_and_uses_wal(client: TestClient, settings: Settings) -> None:
    body = client.get("/api/health").json()
    assert body["db"] == {"ok": True, "journal_mode": "wal", "error": None}
    assert body["version"] == settings.app_version
    assert settings.db_path.exists()


def test_health_reports_unreachable_ollama(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["ollama"]["reachable"] is False
    assert body["ollama"]["url"] == "http://127.0.0.1:9"
    assert body["ollama"]["error"]


def test_health_reports_reachable_ollama(client: TestClient) -> None:
    async def fake_probe(s: Settings) -> OllamaStatus:
        return OllamaStatus(reachable=True, url=s.ollama_url, version="0.12.0")

    client.app.dependency_overrides[get_ollama_probe] = lambda: fake_probe  # type: ignore[attr-defined]
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["ollama"]["reachable"] is True
    assert body["ollama"]["version"] == "0.12.0"


def test_foreign_keys_enabled(client: TestClient) -> None:
    from sqlalchemy import text

    with client.app.state.engine.connect() as conn:  # type: ignore[attr-defined]
        assert conn.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
