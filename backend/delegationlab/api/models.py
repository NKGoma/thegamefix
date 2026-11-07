"""Model endpoints: list installed models and benchmark one (PRD §15, §20)."""

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from sqlmodel import Session, col, select

from delegationlab.db.models import ModelBenchmark
from delegationlab.llm.benchmark import run_benchmark
from delegationlab.llm.gateway import LLMGateway
from delegationlab.llm.types import ModelInfo, ProviderError

router = APIRouter(tags=["models"])

ProviderName = Literal["ollama", "mock"]


class ModelEntry(ModelInfo):
    benchmark: ModelBenchmark | None = None


class ModelList(BaseModel):
    provider: str
    default_model: str
    models: list[ModelEntry]
    error: str | None = None


def _gateway(request: Request) -> LLMGateway:
    return request.app.state.gateway  # type: ignore[no-any-return]


def _latest_benchmarks(gateway: LLMGateway, provider: str) -> dict[str, ModelBenchmark]:
    with Session(gateway.logger.engine) as s:
        rows = s.exec(
            select(ModelBenchmark)
            .where(ModelBenchmark.provider == provider)
            .order_by(col(ModelBenchmark.created_at))
        ).all()
    return {r.model: r for r in rows}  # later rows overwrite earlier ones


@router.get("/models", response_model=ModelList)
async def list_models(
    request: Request, provider: Annotated[ProviderName, Query()] = "ollama"
) -> ModelList:
    gateway = _gateway(request)
    default_model = request.app.state.settings.default_model
    try:
        models = await gateway.provider(provider).list_models()
    except ProviderError as exc:
        return ModelList(provider=provider, default_model=default_model, models=[], error=str(exc))
    benchmarks = _latest_benchmarks(gateway, provider)
    return ModelList(
        provider=provider,
        default_model=default_model,
        models=[ModelEntry(**m.model_dump(), benchmark=benchmarks.get(m.name)) for m in models],
    )


@router.post("/models/{name:path}/benchmark", response_model=ModelBenchmark)
async def benchmark_model(
    name: str, request: Request, provider: Annotated[ProviderName, Query()] = "ollama"
) -> ModelBenchmark:
    try:
        return await run_benchmark(_gateway(request), name, provider)
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
