from typing import Any, Protocol

from delegationlab.llm.types import LLMOptions, Message, ModelInfo, ProviderResponse


class Provider(Protocol):
    name: str

    async def chat(
        self,
        model: str,
        messages: list[Message],
        json_schema: dict[str, Any],
        options: LLMOptions,
        timeout_s: float,
    ) -> ProviderResponse: ...

    async def list_models(self) -> list[ModelInfo]: ...

    async def model_digest(self, model: str) -> str | None: ...
