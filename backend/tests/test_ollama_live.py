"""Runs against the real local Ollama. Not part of `make test`; run with `make test-ollama`."""

import os

import pytest

from delegationlab.db.session import init_db, make_engine
from delegationlab.llm.benchmark import PERSONA, SCENARIOS, TEMPLATE, BenchmarkAnswer
from delegationlab.llm.types import ProviderError
from delegationlab.main import build_gateway
from delegationlab.settings import Settings

pytestmark = pytest.mark.ollama

MODEL = os.environ.get("DELEGATIONLAB_TEST_MODEL", Settings().default_model)


async def test_one_real_structured_call(tmp_path) -> None:  # type: ignore[no-untyped-def]
    settings = Settings(data_dir=tmp_path)
    engine = make_engine(settings)
    init_db(engine)
    gateway = build_gateway(settings, engine)
    try:
        digest = await gateway.model_digest(MODEL)
    except ProviderError:
        pytest.skip(f"Ollama unreachable at {settings.ollama_url}; run `ollama serve`")
    if digest is None:
        pytest.skip(f"{MODEL} is not pulled; run `ollama pull {MODEL}`")
    llm = gateway.bind(run_id=None, task_id="live", run_seed=1, log_dir=tmp_path / "live")
    answer = await llm.complete_json(
        template=TEMPLATE,
        variables={"persona": PERSONA, "scenario": SCENARIOS[0]},
        output_schema=BenchmarkAnswer,
        persona_view="traits_only",
        model=MODEL,
    )
    assert answer.rationale
