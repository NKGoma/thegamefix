"""Deterministic mock provider: returns schema-valid JSON derived from the schema and the seed.

Used by all tests and by "dry run" mode, so runs can be exercised without a model.
"""

import asyncio
import hashlib
import json
import random
from typing import Any

from delegationlab.engine.rng import derive_seed
from delegationlab.llm.types import LLMOptions, Message, ModelInfo, ProviderResponse


def generate(schema: dict[str, Any], rng: random.Random) -> Any:
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return rng.choice(schema["enum"])
    for key in ("anyOf", "oneOf"):
        if key in schema:
            branches = [b for b in schema[key] if b.get("type") != "null"] or schema[key]
            return generate(branches[0], rng)
    if "allOf" in schema:
        return generate({k: v for s in schema["allOf"] for k, v in s.items()}, rng)
    match schema.get("type"):
        case "object":
            props = schema.get("properties", {})
            return {k: generate(v, rng) for k, v in props.items()}
        case "array":
            lo = schema.get("minItems", 1)
            hi = max(lo, schema.get("maxItems", lo + 2))
            return [generate(schema.get("items", {}), rng) for _ in range(rng.randint(lo, hi))]
        case "integer":
            lo = int(schema.get("minimum", schema.get("exclusiveMinimum", -1) + 1))
            hi = int(schema.get("maximum", schema.get("exclusiveMaximum", lo + 101) - 1))
            return rng.randint(lo, hi)
        case "number":
            lo = float(schema.get("minimum", 0.0))
            hi = float(schema.get("maximum", lo + 1.0))
            return round(rng.uniform(lo, hi), 4)
        case "boolean":
            return rng.random() < 0.5
        case "null":
            return None
        case _:
            n = schema.get("minLength", 0)
            text = f"mock-{rng.randint(0, 10**6):06d}"
            return text.ljust(n, "x")


class MockProvider:
    name = "mock"

    def __init__(self, *, invalid_first_n: int = 0, delay_s: float = 0.0) -> None:
        self.invalid_first_n = invalid_first_n
        self.delay_s = delay_s
        self.calls = 0
        self.in_flight = 0
        self.max_in_flight = 0

    async def chat(
        self,
        model: str,
        messages: list[Message],
        json_schema: dict[str, Any],
        options: LLMOptions,
        timeout_s: float,
    ) -> ProviderResponse:
        self.calls += 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            if self.delay_s:
                await asyncio.sleep(self.delay_s)
            if self.calls <= self.invalid_first_n:
                text = '{"not": "what you asked for"'
            else:
                msg_hash = hashlib.sha256(
                    json.dumps([m.model_dump() for m in messages]).encode()
                ).hexdigest()
                rng = random.Random(derive_seed(options.seed, model, msg_hash))
                text = json.dumps(generate(json_schema, rng))
            prompt_tokens = sum(len(m.content.split()) for m in messages)
            return ProviderResponse(
                text=text,
                prompt_tokens=prompt_tokens,
                completion_tokens=len(text) // 4,
                latency_ms=self.delay_s * 1000,
                eval_duration_ms=self.delay_s * 1000 or None,
            )
        finally:
            self.in_flight -= 1

    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(name="mock", digest=await self.model_digest("mock"), loaded=True)]

    async def model_digest(self, model: str) -> str | None:
        return "mock-" + hashlib.sha256(model.encode()).hexdigest()[:12]
