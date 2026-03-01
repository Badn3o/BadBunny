from __future__ import annotations

from .tickerswap import CartResult, Listing, SearchResult, TicketSwapClient
from .tracing import TraceManager


class AdaptiveScraper:
    """Capa especializada en búsqueda web con estrategias iterativas."""

    def __init__(self, client: TicketSwapClient, tracer: TraceManager) -> None:
        self.client = client
        self.tracer = tracer

    async def find(self, query: str, event_url: str = "") -> SearchResult:
        self.tracer.update_status(scraper_progress="running")
        result = await self.client.search(query, event_url=event_url)
        self.tracer.record("INFO", "search_completed", traces=result.trace, found=len(result.listings))
        self.tracer.update_status(scraper_progress="completed", last_result=f"found={len(result.listings)}")
        return result

    async def capture_sale(self, listing: Listing) -> CartResult:
        self.tracer.record("INFO", "capture_attempt", listing_id=listing.listing_id, url=listing.url)
        result = await self.client.add_to_cart(listing)
        self.tracer.record(
            "INFO" if result.success else "ERROR",
            "capture_result",
            success=result.success,
            status=result.status_code,
            endpoint=result.endpoint,
            message=result.message,
        )
        return result
