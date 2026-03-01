from __future__ import annotations

import asyncio
import logging

from .communication import build_communication_profile
from .config import load_settings
from .monitor import BadBunnyMonitor
from .runtime_state import RuntimeState, RuntimeStateStore
from .scraper import AdaptiveScraper
from .tickerswap import TicketSwapClient
from .telegram_bot import TelegramNotifier
from .tracing import TraceManager


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> None:
    configure_logging()
    settings = load_settings()

    store = RuntimeStateStore(settings.runtime_state_path)
    if not store.path.exists():
        store.save(RuntimeState(max_price_eur=settings.max_price_eur, operation_mode=settings.operation_mode))

    tracer = TraceManager(log_path="monitor.log", status_path=settings.runtime_status_path)
    communication = build_communication_profile(settings)

    notifier = TelegramNotifier(
        communication.bot_token,
        communication.chat_id,
        initial_max_price_eur=communication.max_price_eur,
        initial_operation_mode=settings.operation_mode,
    )
    client = TicketSwapClient(
        timeout_seconds=settings.request_timeout_seconds,
        buyer_cookie=settings.ticketswap_buyer_cookie,
    )
    scraper = AdaptiveScraper(client, tracer)

    monitor = BadBunnyMonitor(
        settings=settings,
        notifier=notifier,
        scraper=scraper,
        communication=communication,
        tracer=tracer,
    )
    asyncio.run(monitor.run())


if __name__ == "__main__":
    main()
