from fastapi.testclient import TestClient

from delegationlab.settings import Settings


def test_benchmark_with_mock_provider_stores_result(client: TestClient, settings: Settings) -> None:
    resp = client.post("/api/models/mock-model/benchmark", params={"provider": "mock"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["model"] == "mock-model"
    assert body["n_calls"] == 10
    assert body["json_validity_rate"] == 1.0
    assert body["digest"].startswith("mock-")
    log = settings.data_dir / "benchmarks" / body["id"] / "calls.jsonl"
    assert len(log.read_text().splitlines()) == 10


def test_model_names_with_slashes_and_colons(client: TestClient) -> None:
    resp = client.post("/api/models/library/gemma3:12b/benchmark", params={"provider": "mock"})
    assert resp.status_code == 200
    assert resp.json()["model"] == "library/gemma3:12b"


def test_list_models_attaches_latest_benchmark(client: TestClient) -> None:
    client.post("/api/models/mock/benchmark", params={"provider": "mock"})
    body = client.get("/api/models", params={"provider": "mock"}).json()
    [model] = body["models"]
    assert model["name"] == "mock"
    assert model["benchmark"]["n_calls"] == 10


def test_list_models_degrades_when_ollama_unreachable(client: TestClient) -> None:
    resp = client.get("/api/models")
    assert resp.status_code == 200
    body = resp.json()
    assert body["models"] == [] and body["error"]
    assert body["default_model"] == "gemma3:12b"


def test_benchmark_returns_502_when_ollama_unreachable(client: TestClient) -> None:
    assert client.post("/api/models/gemma3:12b/benchmark").status_code == 502
