from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


class TraceManager:
    def __init__(self, log_path: str = "monitor.log", status_path: str = "runtime_status.json") -> None:
        self.log_path = Path(log_path)
        self.status_path = Path(status_path)

    def record(self, level: str, message: str, **data: Any) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {"ts": timestamp, "level": level, "message": message, "data": data}
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def update_status(self, **status: Any) -> None:
        current = self.read_status()
        current.update(status)
        current["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.status_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

    def read_status(self) -> dict[str, Any]:
        if not self.status_path.exists():
            return {
                "bot_connected": False,
                "scraper_progress": "idle",
                "last_result": "N/A",
            }
        try:
            return json.loads(self.status_path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "bot_connected": False,
                "scraper_progress": "unknown",
                "last_result": "status_parse_error",
            }
