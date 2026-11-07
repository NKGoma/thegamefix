"""OpenAI-compatible provider: a stub in v1, for later cross-model robustness checks."""

from typing import Any

from delegationlab.llm.types import LLMOptions, Message, ModelInfo, ProviderError, ProviderResponse


class OpenAICompatProvider:
    name = "openai_compat"

    def __init__(self, base_url: str | None) -> None:
        self.base_url = base_url

    async def chat(
        self,
        model: str,
        messages: list[Message],
        json_schema: dict[str, Any],
        options: LLMOptions,
        timeout_s: float,
    ) -> ProviderResponse:
        raise ProviderError("The openai_compat provider is not implemented in v1")

    async def list_models(self) -> list[ModelInfo]:
        return []

    async def model_digest(self, model: str) -> str | None:
        return None
