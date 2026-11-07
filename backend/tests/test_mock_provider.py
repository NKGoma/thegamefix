import json
from typing import Literal

from pydantic import BaseModel, Field

from delegationlab.llm.providers.mock import MockProvider
from delegationlab.llm.schema import json_schema_for
from delegationlab.llm.types import LLMOptions, Message


class Inner(BaseModel):
    level: Literal["low", "moderate", "high"]
    weight: float = Field(ge=0, le=1)


class Outer(BaseModel):
    name: str
    count: int = Field(ge=1, le=5)
    flag: bool
    inner: Inner
    items: list[Inner] = Field(min_length=2)
    note: str | None = None


MESSAGES = [Message(role="user", content="hello")]


async def _call(seed: int, model: str = "m") -> str:
    resp = await MockProvider().chat(
        model, MESSAGES, json_schema_for(Outer), LLMOptions(seed=seed), 10
    )
    return resp.text


def test_schema_is_flat() -> None:
    assert "$defs" not in json.dumps(json_schema_for(Outer))
    assert "$ref" not in json.dumps(json_schema_for(Outer))


async def test_output_is_schema_valid_for_many_seeds() -> None:
    for seed in range(50):
        Outer.model_validate_json(await _call(seed))


async def test_output_is_deterministic_per_seed() -> None:
    assert await _call(7) == await _call(7)
    assert await _call(7) != await _call(8)


async def test_invalid_first_n() -> None:
    provider = MockProvider(invalid_first_n=1)
    schema = json_schema_for(Outer)
    first = await provider.chat("m", MESSAGES, schema, LLMOptions(), 10)
    second = await provider.chat("m", MESSAGES, schema, LLMOptions(), 10)
    assert not first.text.endswith("}")
    Outer.model_validate_json(second.text)
