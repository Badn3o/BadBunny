from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from .config import Settings
from .tickerswap import Listing, TicketSwapClient
from .telegram_bot import TelegramNotifier


@dataclass
class SeenListings:
    ids: set[str] = field(default_factory=set)

    def find_new(self, listings: list[Listing]) -> list[Listing]:
        fresh: list[Listing] = []
        for item in listings:
            if item.listing_id not in self.ids:
                fresh.append(item)
        for item in listings:
            self.ids.add(item.listing_id)
        return fresh


class BadBunnyMonitor:
    def __init__(self, settings: Settings, notifier: TelegramNotifier, client: TicketSwapClient) -> None:
        self.settings = settings
        self.notifier = notifier
        self.client = client
        self.seen = SeenListings()

    async def run(self) -> None:
        await self.notifier.start()
        try:
            while True:
                await self._tick()
                if self.settings.run_once:
                    break
                await asyncio.sleep(self.settings.poll_interval_seconds)
        finally:
            await self.notifier.stop()

    async def _tick(self) -> None:
        listings = await self.client.search(self.settings.ticketswap_query)
        new_items = self.seen.find_new(listings)

        if new_items:
            for item in new_items:
                await self.notifier.send_message(self._format_alert(item))

        self.notifier.mark_iteration(new_items=len(new_items))

    @staticmethod
    def _format_alert(item: Listing) -> str:
        price = f"\nPrecio: {item.price_text}" if item.price_text else ""
        return (
            "🎟️ Nueva entrada detectada en TicketSwap\n"
            f"Evento: {item.title}\n"
            f"Ciudad: {item.city or 'Madrid'}{price}\n"
            f"Link: {item.url}"
        )
