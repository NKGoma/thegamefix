import json

import httpx
import pytest

from delegationlab.llm.providers.ollama import OllamaProvider
from delegationlab.llm.types import LLMOptions, Message, ProviderError

SCHEMA = {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
CHAT_OK = {
    "message": {"role": "assistant", "content": '{"a": "hi"}'},
    "prompt_eval_count": 12,
    "eval_count": 5,
    "eval_duration": 250_000_000,
}


async def no_sleep(_s: float) -> None:
    return None


def provider(handler) -> OllamaProvider:  # type: ignore[no-untyped-def]
    return OllamaProvider("http://ollama", transport=httpx.MockTransport(handler), sleep=no_sleep)


async def test_chat_sends_schema_and_seed_and_parses_tokens() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(200, json=CHAT_OK)

    resp = await provider(handler).chat(
        "gemma3:12b",
        [Message(role="system", content="s"), Message(role="user", content="u")],
        SCHEMA,
        LLMOptions(seed=99, temperature=0.3),
        30,
    )
    assert seen["format"] == SCHEMA
    assert seen["stream"] is False
    assert seen["options"]["seed"] == 99
    assert seen["options"]["temperature"] == 0.3
    assert seen["messages"][0] == {"role": "system", "content": "s"}
    assert resp.text == '{"a": "hi"}'
    assert (resp.prompt_tokens, resp.completion_tokens) == (12, 5)
    assert resp.eval_duration_ms == 250


async def test_chat_retries_5xx_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503) if calls["n"] == 1 else httpx.Response(200, json=CHAT_OK)

    resp = await provider(handler).chat(
        "m", [Message(role="user", content="u")], SCHEMA, LLMOptions(), 30
    )
    assert calls["n"] == 2
    assert resp.text == '{"a": "hi"}'


async def test_chat_gives_up_after_three_retries() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ConnectError("refused")

    with pytest.raises(ProviderError):
        await provider(handler).chat(
            "m", [Message(role="user", content="u")], SCHEMA, LLMOptions(), 30
        )
    assert calls["n"] == 4  # first try + 3 retries


async def test_list_models_merges_tags_and_ps() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "name": "gemma3:12b",
                            "size": 8_000_000_000,
                            "digest": "abc",
                            "details": {"parameter_size": "12.2B", "quantization_level": "Q4_K_M"},
                        },
                        {
                            "name": "gemma3:4b",
                            "size": 3_000_000_000,
                            "digest": "def",
                            "details": {},
                        },
                    ]
                },
            )
        return httpx.Response(200, json={"models": [{"name": "gemma3:12b"}]})

    p = provider(handler)
    models = {m.name: m for m in await p.list_models()}
    assert models["gemma3:12b"].loaded and not models["gemma3:4b"].loaded
    assert models["gemma3:12b"].quantization == "Q4_K_M"
    assert await p.model_digest("gemma3:4b") == "def"
    assert await p.model_digest("missing") is None


async def test_list_models_does_not_retry() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ConnectError("refused")

    with pytest.raises(ProviderError):
        await provider(handler).list_models()
    assert calls["n"] == 1
