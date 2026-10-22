"""Application settings, read from environment variables and an optional `.env` file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DELEGATIONLAB_",
        env_file=(REPO_ROOT / ".env", ".env"),
        extra="ignore",
    )

    app_version: str = "0.1.0"
    data_dir: Path = REPO_ROOT / "data"
    db_filename: str = "delegationlab.sqlite"
    ollama_url: str = "http://localhost:11434"
    ollama_probe_timeout_s: float = 2.0
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_filename


@lru_cache
def get_settings() -> Settings:
    return Settings()
