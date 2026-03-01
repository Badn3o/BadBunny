from __future__ import annotations

import asyncio
import logging

from .config import load_settings
from .monitor import BadBunnyMonitor
from .tickerswap import TicketSwapClient
from .telegram_bot import TelegramNotifier


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> None:
    configure_logging()
    settings = load_settings()
    notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    client = TicketSwapClient(timeout_seconds=settings.request_timeout_seconds)
    monitor = BadBunnyMonitor(settings=settings, notifier=notifier, client=client)
    asyncio.run(monitor.run())


if __name__ == "__main__":
    main()
