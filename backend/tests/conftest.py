from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from delegationlab.main import create_app
from delegationlab.settings import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    # Port 9 (discard) is closed on test machines, so Ollama is unreachable by default.
    return Settings(data_dir=tmp_path / "data", ollama_url="http://127.0.0.1:9")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as c:
        yield c
