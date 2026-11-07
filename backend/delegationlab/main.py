"""FastAPI application factory. Run with: uvicorn delegationlab.main:create_app --factory"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import Engine

from delegationlab.api import health, models
from delegationlab.db.session import init_db, make_engine
from delegationlab.llm.gateway import LLMGateway
from delegationlab.llm.providers.base import Provider
from delegationlab.llm.providers.mock import MockProvider
from delegationlab.llm.providers.ollama import OllamaProvider
from delegationlab.llm.providers.openai_compat import OpenAICompatProvider
from delegationlab.llm.templates import TemplateStore
from delegationlab.llm.types import LLMConfig
from delegationlab.settings import Settings, get_settings


def build_gateway(settings: Settings, engine: Engine) -> LLMGateway:
    providers: dict[str, Provider] = {
        "ollama": OllamaProvider(settings.ollama_url),
        "mock": MockProvider(),
        "openai_compat": OpenAICompatProvider(settings.openai_compat_base_url),
    }
    return LLMGateway(
        engine=engine,
        data_dir=settings.data_dir,
        templates=TemplateStore(settings.prompts_dir),
        providers=providers,
        config=LLMConfig(max_concurrency=settings.default_concurrency),
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(settings)
        init_db(engine)
        app.state.engine = engine
        app.state.settings = settings
        app.state.gateway = build_gateway(settings, engine)
        yield
        engine.dispose()

    app = FastAPI(title="DelegationLab", version=settings.app_version, lifespan=lifespan)
    app.dependency_overrides[get_settings] = lambda: settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(models.router, prefix="/api")
    return app
