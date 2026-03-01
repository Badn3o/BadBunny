from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Protocol

from .config import Settings
from .runtime_state import RuntimeStateStore
from .tickerswap import Listing, TicketSwapClient


logger = logging.getLogger(__name__)


class Notifier(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def send_message(self, text: str) -> None: ...
    def mark_iteration(self, new_items: int, cart_attempts: int = 0, cart_successes: int = 0) -> None: ...
    def get_max_price_eur(self) -> float | None: ...
    def set_max_price_eur(self, value: float | None) -> None: ...
    def get_operation_mode(self) -> str: ...
    def set_operation_mode(self, value: str) -> None: ...


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
    def __init__(self, settings: Settings, notifier: Notifier, client: TicketSwapClient) -> None:
        self.settings = settings
        self.notifier = notifier
        self.client = client
        self.seen = SeenListings()
        self.state_store = RuntimeStateStore(settings.runtime_state_path)

    async def run(self) -> None:
        self._apply_runtime_state()
        await self.notifier.start()
        try:
            while True:
                self._apply_runtime_state()
                await self._tick()
                if self.settings.run_once:
                    break
                await asyncio.sleep(self.settings.poll_interval_seconds)
        finally:
            await self.notifier.stop()

    def _apply_runtime_state(self) -> None:
        state = self.state_store.load()
        self.notifier.set_max_price_eur(state.max_price_eur)
        self.notifier.set_operation_mode(state.operation_mode)

    async def _tick(self) -> None:
        search = await self.client.search(
            self.settings.ticketswap_query,
            event_url=self.settings.ticketswap_event_url,
        )
        listings = search.listings
        new_items = self.seen.find_new(listings)

        cart_attempts = 0
        cart_successes = 0
        operation_mode = self.notifier.get_operation_mode()
        max_price = self.notifier.get_max_price_eur()

        logger.info(
            "Monitor tick: listings=%s new=%s mode=%s max_price=%s",
            len(listings),
            len(new_items),
            operation_mode,
            max_price,
        )

        if self.settings.progress_to_telegram:
            await self.notifier.send_message(self._format_progress(search.trace, len(listings), len(new_items)))

        for item in new_items:
            await self.notifier.send_message(self._format_alert(item))
            if self._should_try_buy(item, max_price_eur=max_price, operation_mode=operation_mode):
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
    def _should_try_buy(item: Listing, max_price_eur: float | None, operation_mode: str) -> bool:
        if operation_mode == "test":
            return True
        if max_price_eur is None:
            return False
        if item.unit_price_eur is None:
            return False
        return item.unit_price_eur <= max_price_eur

    @staticmethod
    def _format_progress(trace: list[str], listing_count: int, new_count: int) -> str:
        tail = trace[-8:] if len(trace) > 8 else trace
        trace_text = "\n".join(f"- {line}" for line in tail)
        return (
            "🔎 Progreso TicketSwap\n"
            f"Resultados totales filtrados: {listing_count}\n"
            f"Resultados nuevos: {new_count}\n"
            "Detalle últimas búsquedas:\n"
            f"{trace_text}"
        )

    @staticmethod
    def _format_alert(item: Listing) -> str:
        unit_price = item.unit_price_eur
        if unit_price is not None:
            price_line = (
                f"\nPrecio total: {item.total_price_eur:.2f}€"
                f"\nNº entradas en pack: {item.ticket_count}"
                f"\nPrecio unitario: {unit_price:.2f}€"
            )
        else:
            price_line = f"\nPrecio: {item.price_text or 'N/D'}"
        return (
            "🎟️ Nueva entrada detectada en TicketSwap\n"
            f"Evento: {item.title}\n"
            f"Ciudad: {item.city or 'Madrid'}{price_line}\n"
            f"Link: {item.url}"
        )

    @staticmethod
    def _format_cart_result(item: Listing, success: bool, message: str) -> str:
        icon = "🛒✅" if success else "🛒❌"
        unit = item.unit_price_eur
        unit_text = f"{unit:.2f}€" if unit is not None else "N/D"
        return (
            f"{icon} Resultado carrito\n"
            f"Evento: {item.title}\n"
            f"Precio unitario detectado: {unit_text}\n"
            f"Detalle: {message}"
        )
