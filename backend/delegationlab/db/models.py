"""SQLModel tables. Timestamps are UTC ISO-8601 strings; IDs are ULIDs."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel
from ulid import ULID


def new_id() -> str:
    return str(ULID())


def utcnow_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


class Call(SQLModel, table=True):
    """Index row for one LLM request/response. The full record lives in the JSONL log."""

    id: str = Field(default_factory=new_id, primary_key=True)
    # Plain strings, not foreign keys: benchmark calls have no run or task.
    run_id: str | None = Field(default=None, index=True)
    task_id: str | None = Field(default=None, index=True)
    provider: str
    model: str
    model_digest: str | None = None
    template: str
    template_hash: str
    persona_view: str | None = None
    request_hash: str = Field(index=True)
    seed: int
    cache_hit: bool = False
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    valid_json: bool
    retry_index: int = 0
    created_at: str = Field(default_factory=utcnow_iso)
    log_path: str
    jsonl_offset: int


class LLMCache(SQLModel, table=True):
    key: str = Field(primary_key=True)
    response_text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    created_at: str = Field(default_factory=utcnow_iso)


class ModelBenchmark(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    provider: str
    model: str = Field(index=True)
    digest: str | None = None
    n_calls: int
    mean_latency_ms: float
    p95_latency_ms: float
    tokens_per_s: float | None = None
    json_validity_rate: float
    created_at: str = Field(default_factory=utcnow_iso)
