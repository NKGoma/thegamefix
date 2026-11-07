"""LLM response cache in SQLite. It is the reproducibility guarantee for reruns (PRD §16)."""

import hashlib
import json
from typing import Any

from sqlalchemy import func
from sqlalchemy.engine import Engine
from sqlmodel import Session, delete, select

from delegationlab.db.models import LLMCache
from delegationlab.llm.types import LLMOptions, Message, ProviderResponse


def cache_key(
    provider: str,
    model: str,
    model_digest: str | None,
    messages: list[Message],
    options: LLMOptions,
    json_schema: dict[str, Any],
) -> str:
    payload = {
        "provider": provider,
        "model": model,
        "model_digest": model_digest,
        "messages": [m.model_dump() for m in messages],
        "options": options.model_dump(),
        "schema": json_schema,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


class LLMCacheStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get(self, key: str) -> LLMCache | None:
        with Session(self.engine) as s:
            return s.get(LLMCache, key)

    def put(self, key: str, resp: ProviderResponse) -> None:
        with Session(self.engine) as s:
            s.merge(
                LLMCache(
                    key=key,
                    response_text=resp.text,
                    prompt_tokens=resp.prompt_tokens,
                    completion_tokens=resp.completion_tokens,
                )
            )
            s.commit()

    def size(self) -> tuple[int, int]:
        """(entries, bytes of stored response text)."""
        with Session(self.engine) as s:
            n, size = s.exec(
                select(
                    func.count(), func.coalesce(func.sum(func.length(LLMCache.response_text)), 0)
                )
            ).one()
            return int(n), int(size)

    def clear(self) -> int:
        with Session(self.engine) as s:
            n = s.exec(select(func.count()).select_from(LLMCache)).one()
            s.exec(delete(LLMCache))
            s.commit()
            return int(n)
