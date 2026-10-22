"""GET /api/health: reports backend, database and Ollama status."""

from collections.abc import Awaitable, Callable
from typing import Annotated, Literal

import httpx
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from delegationlab.db.session import check_db
from delegationlab.settings import Settings, get_settings

router = APIRouter(tags=["system"])


class DbStatus(BaseModel):
    ok: bool
    journal_mode: str | None = None
    error: str | None = None


class OllamaStatus(BaseModel):
    reachable: bool
    url: str
    version: str | None = None
    error: str | None = None


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    db: DbStatus
    ollama: OllamaStatus


OllamaProbe = Callable[[Settings], Awaitable[OllamaStatus]]


async def probe_ollama(settings: Settings) -> OllamaStatus:
    url = settings.ollama_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_probe_timeout_s) as client:
            resp = await client.get(f"{url}/api/version")
            resp.raise_for_status()
            return OllamaStatus(reachable=True, url=url, version=resp.json().get("version"))
    except (httpx.HTTPError, ValueError) as exc:
        return OllamaStatus(reachable=False, url=url, error=f"{type(exc).__name__}: {exc}")


def get_ollama_probe() -> OllamaProbe:
    return probe_ollama


@router.get("/health", response_model=Health)
async def health(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    probe: Annotated[OllamaProbe, Depends(get_ollama_probe)],
) -> Health:
    ok, journal_mode, error = check_db(request.app.state.engine)
    ollama = await probe(settings)
    return Health(
        status="ok" if ok and ollama.reachable else "degraded",
        version=settings.app_version,
        db=DbStatus(ok=ok, journal_mode=journal_mode, error=error),
        ollama=ollama,
    )
