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

        cart_attempts = 0
        cart_successes = 0

        if new_items:
            for item in new_items:
                await self.notifier.send_message(self._format_alert(item))
                should_buy = self._should_try_buy(item, self.notifier.get_max_price_eur())
                if should_buy:
                    cart_attempts += 1
                    result = await self.client.add_to_cart(item)
                    if result.success:
                        cart_successes += 1
                    await self.notifier.send_message(self._format_cart_result(item, result.success, result.message))

        self.notifier.mark_iteration(
            new_items=len(new_items),
            cart_attempts=cart_attempts,
            cart_successes=cart_successes,
        )

    @staticmethod
    def _should_try_buy(item: Listing, max_price_eur: float | None) -> bool:
        if max_price_eur is None:
            return False
        if item.price_eur is None:
            return False
        return item.price_eur <= max_price_eur

    @staticmethod
    def _format_alert(item: Listing) -> str:
        if item.price_eur is not None:
            price_line = f"\nPrecio: {item.price_eur:.2f}€"
        else:
            price_line = f"\nPrecio: {item.price_text}" if item.price_text else "\nPrecio: N/D"
        return (
            "🎟️ Nueva entrada detectada en TicketSwap\n"
            f"Evento: {item.title}\n"
            f"Ciudad: {item.city or 'Madrid'}{price_line}\n"
            f"Link: {item.url}"
        )

    @staticmethod
    def _format_cart_result(item: Listing, success: bool, message: str) -> str:
        icon = "🛒✅" if success else "🛒❌"
        return (
            f"{icon} Resultado carrito\n"
            f"Evento: {item.title}\n"
            f"Precio detectado: {item.price_eur if item.price_eur is not None else 'N/D'}\n"
            f"Detalle: {message}"
        )
