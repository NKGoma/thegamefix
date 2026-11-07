"""LLM gateway: the only way any module calls an LLM (PRD §11).

Every attempt is rendered from a template, seeded deterministically, served from the cache when
possible, validated against a Pydantic schema, and logged to JSONL plus the `call` index.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.engine import Engine

from delegationlab.db.models import Call
from delegationlab.engine.rng import derive_seed
from delegationlab.llm.cache import LLMCacheStore, cache_key
from delegationlab.llm.logging import CallLogger
from delegationlab.llm.providers.base import Provider
from delegationlab.llm.schema import json_schema_for
from delegationlab.llm.templates import TemplateStore
from delegationlab.llm.types import (
    LLMConfig,
    LLMOptions,
    LLMValidationError,
    Message,
    PersonaViewError,
    ProviderResponse,
)

T = TypeVar("T", bound=BaseModel)

FORBIDDEN_VIEWS = frozenset({"ground_truth_code"})

RETRY_INSTRUCTION = (
    "\n\nYour previous answer was invalid because: {error}\n"
    "Return only valid JSON matching the schema."
)


def summarize_validation_error(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors()[:5]:
        loc = ".".join(str(p) for p in err["loc"]) or "<root>"
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


class LLMGateway:
    def __init__(
        self,
        *,
        engine: Engine,
        data_dir: Path,
        templates: TemplateStore,
        providers: dict[str, Provider],
        config: LLMConfig,
    ) -> None:
        self.templates = templates
        self.providers = providers
        self.config = config
        self.cache = LLMCacheStore(engine)
        self.logger = CallLogger(engine, data_dir)
        self.data_dir = data_dir
        self._semaphore = asyncio.Semaphore(config.max_concurrency)
        self._digests: dict[tuple[str, str], str | None] = {}

    def provider(self, name: str | None = None) -> Provider:
        name = name or self.config.provider
        if name not in self.providers:
            raise KeyError(f"Unknown LLM provider {name!r}; known: {sorted(self.providers)}")
        return self.providers[name]

    async def model_digest(
        self, model: str, *, provider: str | None = None, refresh: bool = False
    ) -> str | None:
        key = (provider or self.config.provider, model)
        if refresh or key not in self._digests:
            self._digests[key] = await self.provider(key[0]).model_digest(model)
        return self._digests[key]

    async def capture_digests(
        self, models: list[str], *, provider: str | None = None
    ) -> dict[str, str | None]:
        """Snapshot of model digests, stored on the run at start."""
        return {m: await self.model_digest(m, provider=provider, refresh=True) for m in models}

    async def digests_changed(
        self, snapshot: dict[str, str | None], *, provider: str | None = None
    ) -> list[str]:
        """Models whose digest differs from the snapshot (the orchestrator pauses the run)."""
        current = await self.capture_digests(list(snapshot), provider=provider)
        return [m for m, d in snapshot.items() if current[m] != d]

    def bind(
        self,
        *,
        run_id: str | None,
        task_id: str | None,
        run_seed: int,
        log_dir: Path,
        config: LLMConfig | None = None,
    ) -> "BoundGateway":
        return BoundGateway(self, run_id, task_id, run_seed, log_dir, config or self.config)


@dataclass
class _Attempt:
    response: ProviderResponse
    cache_hit: bool


@dataclass
class BoundGateway:
    """A gateway bound to one task: what modules receive as `ctx.llm`."""

    gateway: LLMGateway
    run_id: str | None
    task_id: str | None
    run_seed: int
    log_dir: Path
    config: LLMConfig

    async def complete_json(
        self,
        *,
        template: str,
        variables: dict[str, Any],
        output_schema: type[T],
        persona_view: str | None,
        model: str,
    ) -> T:
        if persona_view in FORBIDDEN_VIEWS:
            raise PersonaViewError(f"Persona view {persona_view!r} may never be sent to an LLM")

        gw = self.gateway
        provider = gw.provider(self.config.provider)
        schema = json_schema_for(output_schema)
        template_hash = gw.templates.hash(template)
        base_messages = gw.templates.render(template, variables)
        digest = await gw.model_digest(model, provider=provider.name)
        error: str | None = None

        for retry_index in range(self.config.json_retries + 1):
            messages = _with_retry_note(base_messages, error)
            options = LLMOptions(
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                num_ctx=self.config.num_ctx,
                seed=derive_seed(self.run_seed, self.task_id, retry_index),
            )
            key = cache_key(provider.name, model, digest, messages, options, schema)
            attempt = await self._attempt(provider, model, messages, schema, options, key)

            parsed: T | None = None
            error = None
            try:
                parsed = output_schema.model_validate_json(attempt.response.text)
            except ValidationError as exc:
                error = summarize_validation_error(exc)

            await gw.logger.log(
                Call(
                    run_id=self.run_id,
                    task_id=self.task_id,
                    provider=provider.name,
                    model=model,
                    model_digest=digest,
                    template=template,
                    template_hash=template_hash,
                    persona_view=persona_view,
                    request_hash=key,
                    seed=options.seed,
                    cache_hit=attempt.cache_hit,
                    latency_ms=attempt.response.latency_ms,
                    prompt_tokens=attempt.response.prompt_tokens,
                    completion_tokens=attempt.response.completion_tokens,
                    valid_json=parsed is not None,
                    retry_index=retry_index,
                    log_path="",
                    jsonl_offset=0,
                ),
                {
                    "run_id": self.run_id,
                    "task_id": self.task_id,
                    "provider": provider.name,
                    "model": model,
                    "model_digest": digest,
                    "template": template,
                    "template_hash": template_hash,
                    "persona_view": persona_view,
                    "exposed_persona_fields": variables.get("persona"),
                    "messages": [m.model_dump() for m in messages],
                    "options": options.model_dump(),
                    "output_schema": output_schema.__name__,
                    "raw_response": attempt.response.text,
                    "parsed": parsed.model_dump(mode="json") if parsed else None,
                    "validation_error": error,
                    "cache_hit": attempt.cache_hit,
                    "retry_index": retry_index,
                    "latency_ms": attempt.response.latency_ms,
                    "prompt_tokens": attempt.response.prompt_tokens,
                    "completion_tokens": attempt.response.completion_tokens,
                    "eval_duration_ms": attempt.response.eval_duration_ms,
                },
                self.log_dir,
            )
            if parsed is not None:
                return parsed

        raise LLMValidationError(
            f"{template} on {model}: no valid JSON after {self.config.json_retries + 1} "
            f"attempts; last error: {error}"
        )

    async def _attempt(
        self,
        provider: Provider,
        model: str,
        messages: list[Message],
        schema: dict[str, Any],
        options: LLMOptions,
        key: str,
    ) -> _Attempt:
        cache = self.gateway.cache
        if self.config.cache and (hit := cache.get(key)) is not None:
            return _Attempt(
                ProviderResponse(
                    text=hit.response_text,
                    prompt_tokens=hit.prompt_tokens,
                    completion_tokens=hit.completion_tokens,
                    latency_ms=0.0,
                ),
                cache_hit=True,
            )
        async with self.gateway._semaphore:
            resp = await provider.chat(model, messages, schema, options, self.config.timeout_s)
        if self.config.cache:
            cache.put(key, resp)
        return _Attempt(resp, cache_hit=False)


def _with_retry_note(messages: list[Message], error: str | None) -> list[Message]:
    if error is None:
        return messages
    out = [m.model_copy() for m in messages]
    last_user = max(i for i, m in enumerate(out) if m.role == "user")
    out[last_user] = Message(
        role="user", content=out[last_user].content + RETRY_INSTRUCTION.format(error=error)
    )
    return out
