"""Shared types for the LLM layer."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMOptions(BaseModel):
    temperature: float = 0.7
    top_p: float = 0.9
    num_ctx: int = 8192
    seed: int = 0


class LLMConfig(BaseModel):
    """The `llm:` block of an experiment config (PRD §9)."""

    provider: str = "ollama"
    temperature: float = 0.7
    top_p: float = 0.9
    num_ctx: int = 8192
    max_concurrency: int = Field(default=2, ge=1)
    json_retries: int = Field(default=2, ge=0)
    timeout_s: float = 180
    cache: bool = True


class ProviderResponse(BaseModel):
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float
    eval_duration_ms: float | None = None  # generation time only, for tokens/s
    raw: dict[str, Any] = Field(default_factory=dict)


class ModelInfo(BaseModel):
    name: str
    size_bytes: int | None = None
    parameter_size: str | None = None
    quantization: str | None = None
    digest: str | None = None
    loaded: bool = False


class ProviderError(RuntimeError):
    """The provider could not produce a response (unreachable, repeated 5xx, ...)."""


class LLMValidationError(RuntimeError):
    """The model kept returning output that does not match the schema."""


class PersonaViewError(RuntimeError):
    """A prompt asked for a persona view the LLM may not see."""
