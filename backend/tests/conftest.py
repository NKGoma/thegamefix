from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from delegationlab.llm.providers.ollama import OllamaProvider
from delegationlab.main import create_app
from delegationlab.settings import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    # Port 9 (discard) is closed on test machines, so Ollama is unreachable by default.
    return Settings(data_dir=tmp_path / "data", ollama_url="http://127.0.0.1:9")


async def _no_sleep(_seconds: float) -> None:
    return None


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as c:
        # Skip the real 1s/4s/10s backoff when the (unreachable) Ollama is retried.
        c.app.state.gateway.providers["ollama"] = OllamaProvider(  # type: ignore[attr-defined]
            settings.ollama_url, sleep=_no_sleep
        )
        yield c


TEST_TEMPLATE = """{# ---
persona_view: traits_only
output_schema: Answer
--- #}
{% block system %}You are {{ persona.narrative }}.{% endblock %}
{% block user %}Question: {{ question }}{% endblock %}
"""


@pytest.fixture
def prompts_dir(tmp_path: Path) -> Path:
    d = tmp_path / "prompts"
    (d / "test").mkdir(parents=True)
    (d / "test" / "item.j2").write_text(TEST_TEMPLATE)
    return d
