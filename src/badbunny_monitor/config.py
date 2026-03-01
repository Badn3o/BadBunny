from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    ticketswap_query: str = "bad bunny madrid"
    poll_interval_seconds: int = 30
    run_once: bool = False
    request_timeout_seconds: int = 12
    max_price_eur: float | None = None
    ticketswap_buyer_cookie: str = ""
    operation_mode: str = "real"
    runtime_state_path: str = "runtime_state.json"
    ticketswap_event_url: str = ""
    progress_to_telegram: bool = True


TRUE_VALUES = {"1", "true", "yes", "on"}


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in TRUE_VALUES


def _to_optional_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value.strip().replace(",", "."))


def _load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_settings() -> Settings:
    _load_dotenv_file(Path(".env"))

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN es obligatorio")
    if not chat_id:
        raise ValueError("TELEGRAM_CHAT_ID es obligatorio")

    mode = os.getenv("OPERATION_MODE", "real").strip().lower()
    if mode not in {"real", "test"}:
        mode = "real"

    return Settings(
        telegram_bot_token=token,
        telegram_chat_id=chat_id,
        ticketswap_query=os.getenv("TICKETSWAP_QUERY", "bad bunny madrid").strip(),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "30")),
        run_once=_to_bool(os.getenv("RUN_ONCE"), default=False),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "12")),
        max_price_eur=_to_optional_float(os.getenv("MAX_PRICE_EUR")),
        ticketswap_buyer_cookie=os.getenv("TICKETSWAP_BUYER_COOKIE", "").strip(),
        operation_mode=mode,
        runtime_state_path=os.getenv("RUNTIME_STATE_PATH", "runtime_state.json").strip() or "runtime_state.json",
        ticketswap_event_url=os.getenv("TICKETSWAP_EVENT_URL", "").strip(),
        progress_to_telegram=_to_bool(os.getenv("PROGRESS_TO_TELEGRAM"), default=True),
    )
