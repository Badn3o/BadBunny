from __future__ import annotations

from dataclasses import dataclass
import os

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv() -> None:
        return None


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    ticketswap_query: str = "bad bunny madrid"
    poll_interval_seconds: int = 30
    run_once: bool = False
    request_timeout_seconds: int = 12


TRUE_VALUES = {"1", "true", "yes", "on"}


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in TRUE_VALUES


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN es obligatorio")
    if not chat_id:
        raise ValueError("TELEGRAM_CHAT_ID es obligatorio")

    return Settings(
        telegram_bot_token=token,
        telegram_chat_id=chat_id,
        ticketswap_query=os.getenv("TICKETSWAP_QUERY", "bad bunny madrid").strip(),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "30")),
        run_once=_to_bool(os.getenv("RUN_ONCE"), default=False),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "12")),
    )
