"""SQLite engine with WAL mode and foreign keys enforced on every connection."""

from typing import Any

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine

from delegationlab.settings import Settings


def _set_sqlite_pragmas(dbapi_connection: Any, _record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_engine(settings: Settings) -> Engine:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{settings.db_path}",
        connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", _set_sqlite_pragmas)
    return engine


def init_db(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)


def check_db(engine: Engine) -> tuple[bool, str | None, str | None]:
    """Return (ok, journal_mode, error)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            mode = conn.execute(text("PRAGMA journal_mode")).scalar_one()
        return True, str(mode), None
    except Exception as exc:
        return False, None, str(exc)
