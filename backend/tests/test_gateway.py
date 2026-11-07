import asyncio
import json
from pathlib import Path
from typing import Literal

import pytest
from pydantic import BaseModel
from sqlmodel import Session, col, select

from delegationlab.db.models import Call
from delegationlab.db.session import init_db, make_engine
from delegationlab.llm.cache import cache_key
from delegationlab.llm.gateway import LLMGateway
from delegationlab.llm.providers.mock import MockProvider
from delegationlab.llm.templates import TemplateStore
from delegationlab.llm.types import (
    LLMConfig,
    LLMOptions,
    LLMValidationError,
    Message,
    PersonaViewError,
)
from delegationlab.settings import Settings

PERSONA = {"narrative": "a careful nurse"}


class Answer(BaseModel):
    execution_authority: Literal["act_silently", "ask_first"]
    rationale: str


def make_gateway(settings: Settings, prompts_dir: Path, mock: MockProvider, **cfg) -> LLMGateway:  # type: ignore[no-untyped-def]
    engine = make_engine(settings)
    init_db(engine)
    return LLMGateway(
        engine=engine,
        data_dir=settings.data_dir,
        templates=TemplateStore(prompts_dir),
        providers={"mock": mock},
        config=LLMConfig(provider="mock", **cfg),
    )


async def ask(gw: LLMGateway, task_id: str = "t1", view: str = "traits_only", **bind) -> Answer:  # type: ignore[no-untyped-def]
    llm = gw.bind(
        run_id="r1", task_id=task_id, run_seed=42, log_dir=gw.data_dir / "runs" / "r1", **bind
    )
    return await llm.complete_json(
        template="test/item.j2",
        variables={"persona": PERSONA, "question": f"q-{task_id}"},
        output_schema=Answer,
        persona_view=view,
        model="mock-model",
    )


def calls(gw: LLMGateway) -> list[Call]:
    with Session(gw.logger.engine) as s:
        return list(s.exec(select(Call).order_by(col(Call.created_at), col(Call.retry_index))))


async def test_returns_validated_object_and_logs_one_call(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    gw = make_gateway(settings, prompts_dir, MockProvider())
    answer = await ask(gw)
    assert isinstance(answer, Answer)
    [call] = calls(gw)
    assert call.valid_json and call.retry_index == 0 and not call.cache_hit
    assert call.persona_view == "traits_only"
    assert call.template_hash == gw.templates.hash("test/item.j2")
    assert call.model_digest and call.model_digest.startswith("mock-")


async def test_jsonl_record_holds_full_call(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    gw = make_gateway(settings, prompts_dir, MockProvider())
    await ask(gw, "t1")
    await ask(gw, "t2")
    second = calls(gw)[1]
    record = gw.logger.read(second)
    assert record["id"] == second.id
    assert record["task_id"] == "t2"
    assert record["exposed_persona_fields"] == PERSONA
    assert record["messages"][0] == {"role": "system", "content": "You are a careful nurse."}
    assert record["parsed"]["execution_authority"] in {"act_silently", "ask_first"}
    assert second.log_path == "runs/r1/calls.jsonl"


async def test_invalid_then_valid_retries_with_error_in_prompt(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    gw = make_gateway(settings, prompts_dir, MockProvider(invalid_first_n=1))
    await ask(gw)
    first, second = calls(gw)
    assert (first.retry_index, first.valid_json) == (0, False)
    assert (second.retry_index, second.valid_json) == (1, True)
    assert first.seed != second.seed
    retry_prompt = gw.logger.read(second)["messages"][-1]["content"]
    assert "Your previous answer was invalid because:" in retry_prompt
    assert "Return only valid JSON matching the schema." in retry_prompt
    assert gw.logger.read(first)["validation_error"]


async def test_exhausted_retries_raise_and_log_every_attempt(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    gw = make_gateway(settings, prompts_dir, MockProvider(invalid_first_n=99), json_retries=2)
    with pytest.raises(LLMValidationError):
        await ask(gw)
    assert [c.retry_index for c in calls(gw)] == [0, 1, 2]
    assert not any(c.valid_json for c in calls(gw))


async def test_identical_call_is_a_cache_hit(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    mock = MockProvider()
    gw = make_gateway(settings, prompts_dir, mock)
    a = await ask(gw)
    b = await ask(gw)
    assert a == b
    assert mock.calls == 1
    assert [c.cache_hit for c in calls(gw)] == [False, True]


async def test_cache_can_be_disabled(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    mock = MockProvider()
    gw = make_gateway(settings, prompts_dir, mock, cache=False)
    await ask(gw)
    await ask(gw)
    assert mock.calls == 2


def test_cache_key_is_stable_and_tracks_digest() -> None:
    args = (
        "ollama",
        "gemma3:12b",
        "d1",
        [Message(role="user", content="x")],
        LLMOptions(seed=1),
        {"type": "object"},
    )
    assert cache_key(*args) == cache_key(*args)
    assert cache_key("ollama", "gemma3:12b", "d2", *args[3:]) != cache_key(*args)


async def test_ground_truth_view_is_refused(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    mock = MockProvider()
    gw = make_gateway(settings, prompts_dir, mock)
    with pytest.raises(PersonaViewError):
        await ask(gw, view="ground_truth_code")
    assert mock.calls == 0 and calls(gw) == []


async def test_semaphore_caps_concurrency(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    mock = MockProvider(delay_s=0.05)
    gw = make_gateway(settings, prompts_dir, mock, max_concurrency=2)
    await asyncio.gather(*(ask(gw, f"t{i}") for i in range(6)))
    assert mock.max_in_flight == 2
    assert len(calls(gw)) == 6


async def test_rerun_is_identical_with_warm_cache(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    gw = make_gateway(settings, prompts_dir, MockProvider())
    first = [await ask(gw, f"t{i}") for i in range(3)]
    second = [await ask(gw, f"t{i}") for i in range(3)]
    assert first == second


async def test_digest_capture_and_change_detection(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    gw = make_gateway(settings, prompts_dir, MockProvider())
    snap = await gw.capture_digests(["a", "b"])
    assert await gw.digests_changed(snap) == []
    snap["a"] = "stale"
    assert await gw.digests_changed(snap) == ["a"]


def test_jsonl_lines_are_valid_json(settings, prompts_dir) -> None:  # type: ignore[no-untyped-def]
    gw = make_gateway(settings, prompts_dir, MockProvider(invalid_first_n=1))
    asyncio.run(ask(gw))
    lines = (settings.data_dir / "runs" / "r1" / "calls.jsonl").read_text().splitlines()
    assert len(lines) == 2 and all(json.loads(line)["id"] for line in lines)
