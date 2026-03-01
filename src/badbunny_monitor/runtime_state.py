from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass
class RuntimeState:
    max_price_eur: float | None = None
    operation_mode: str = "real"


class RuntimeStateStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def load(self) -> RuntimeState:
        if not self.path.exists():
            return RuntimeState()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return RuntimeState()

        max_price = payload.get("max_price_eur") if isinstance(payload, dict) else None
        mode = payload.get("operation_mode") if isinstance(payload, dict) else "real"
        if mode not in {"real", "test"}:
            mode = "real"

        price_value: float | None
        try:
            price_value = float(max_price) if max_price is not None else None
        except (TypeError, ValueError):
            price_value = None

        return RuntimeState(max_price_eur=price_value, operation_mode=mode)

    def save(self, state: RuntimeState) -> None:
        self.path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")
