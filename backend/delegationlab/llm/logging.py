"""Call logging: one JSONL line per LLM call, plus an index row in the `call` table."""

import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy.engine import Engine
from sqlmodel import Session

from delegationlab.db.models import Call


class CallLogger:
    def __init__(self, engine: Engine, data_dir: Path) -> None:
        self.engine = engine
        self.data_dir = data_dir
        self._locks: dict[Path, asyncio.Lock] = {}

    async def log(self, call: Call, record: dict[str, Any], log_dir: Path) -> Call:
        """Append `record` to <log_dir>/calls.jsonl, then store `call` pointing at that line."""
        path = log_dir / "calls.jsonl"
        lock = self._locks.setdefault(path, asyncio.Lock())
        line = json.dumps({"id": call.id, **record}, default=str, ensure_ascii=False) + "\n"
        async with lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("ab") as f:
                offset = f.tell()
                f.write(line.encode())
        call.log_path = str(path.relative_to(self.data_dir))
        call.jsonl_offset = offset
        with Session(self.engine) as s:
            s.add(call)
            s.commit()
            s.refresh(call)
        return call

    def read(self, call: Call) -> dict[str, Any]:
        with (self.data_dir / call.log_path).open("rb") as f:
            f.seek(call.jsonl_offset)
            return json.loads(f.readline())  # type: ignore[no-any-return]
