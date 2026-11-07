"""Ollama provider: POST /api/chat with `format` set to the JSON schema (structured outputs)."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from delegationlab.llm.types import LLMOptions, Message, ModelInfo, ProviderError, ProviderResponse

BACKOFF_S = (1.0, 4.0, 10.0)


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        base_url: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._transport = transport
        self._sleep = sleep

    def _client(self, timeout_s: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url, timeout=timeout_s, transport=self._transport
        )

    async def _request(
        self, method: str, path: str, timeout_s: float, *, retry: bool = True, **kw: Any
    ) -> Any:
        """Send a request; with `retry`, back off on connection errors, timeouts and 5xx."""
        last: Exception | None = None
        for attempt in range(len(BACKOFF_S) + 1 if retry else 1):
            if attempt:
                await self._sleep(BACKOFF_S[attempt - 1])
            try:
                async with self._client(timeout_s) as client:
                    resp = await client.request(method, path, **kw)
                if resp.status_code >= 500:
                    last = ProviderError(f"Ollama {path} returned {resp.status_code}: {resp.text}")
                    continue
                if resp.status_code >= 400:
                    raise ProviderError(f"Ollama {path} returned {resp.status_code}: {resp.text}")
                return resp.json()
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last = exc
        detail = f"after {len(BACKOFF_S)} retries" if retry else "(no retry)"
        raise ProviderError(f"Ollama {path} failed {detail}: {last}")

    async def chat(
        self,
        model: str,
        messages: list[Message],
        json_schema: dict[str, Any],
        options: LLMOptions,
        timeout_s: float,
    ) -> ProviderResponse:
        body = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "format": json_schema,
            "stream": False,
            "options": options.model_dump(),
        }
        start = time.perf_counter()
        data = await self._request("POST", "/api/chat", timeout_s, json=body)
        latency_ms = (time.perf_counter() - start) * 1000
        eval_ns = data.get("eval_duration")
        return ProviderResponse(
            text=data.get("message", {}).get("content", ""),
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
            latency_ms=latency_ms,
            eval_duration_ms=eval_ns / 1e6 if eval_ns else None,
            raw={k: v for k, v in data.items() if k != "message"},
        )

    async def list_models(self) -> list[ModelInfo]:
        # Listing fails fast so the dashboard can show "unreachable" at once; only chat retries.
        tags = await self._request("GET", "/api/tags", 10, retry=False)
        try:
            ps = await self._request("GET", "/api/ps", 10, retry=False)
            loaded = {m["name"] for m in ps.get("models", [])}
        except ProviderError:
            loaded = set()
        out = []
        for m in tags.get("models", []):
            details = m.get("details") or {}
            out.append(
                ModelInfo(
                    name=m["name"],
                    size_bytes=m.get("size"),
                    parameter_size=details.get("parameter_size"),
                    quantization=details.get("quantization_level"),
                    digest=m.get("digest"),
                    loaded=m["name"] in loaded,
                )
            )
        return out

    async def model_digest(self, model: str) -> str | None:
        for m in await self.list_models():
            if m.name == model or m.name == f"{model}:latest":
                return m.digest
        return None
