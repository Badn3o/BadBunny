from __future__ import annotations

from dataclasses import dataclass
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Listing:
    listing_id: str
    title: str
    city: str
    url: str
    price_text: str | None = None


class TicketSwapClient:
    """Cliente de lectura para encontrar eventos/listados de TicketSwap."""

    BASE_URL = "https://www.ticketswap.com"

    def __init__(self, timeout_seconds: int = 12) -> None:
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str) -> list[Listing]:
        from_api = self._search_json_api(query)
        if from_api:
            return self._filter_bad_bunny_madrid(from_api)
        from_html = self._search_html(query)
        return self._filter_bad_bunny_madrid(from_html)

    def _http_get(self, url: str, params: dict[str, str]) -> tuple[int, str]:
        full_url = f"{url}?{urlencode(params)}" if params else url
        req = Request(
            full_url,
            headers={
                "User-Agent": "Mozilla/5.0 (BadBunnyMonitor)",
                "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(req, timeout=self.timeout_seconds) as response:  # nosec B310
            status = getattr(response, "status", 200)
            body = response.read().decode("utf-8", errors="ignore")
            return status, body

    def _search_json_api(self, query: str) -> list[Listing]:
        url = f"{self.BASE_URL}/api/search/v2/events"
        try:
            status, body = self._http_get(url, {"query": query})
            if status != 200:
                return []
            data = json.loads(body)
            return self._parse_api_payload(data)
        except Exception:
            return []

    def _parse_api_payload(self, payload: object) -> list[Listing]:
        items = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return []

        listings: list[Listing] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or item.get("slug") or "")
            name = str(item.get("name") or "").strip()
            city = str(item.get("city") or item.get("location") or "").strip()
            url = str(item.get("url") or "").strip()
            if url.startswith("/"):
                url = f"{self.BASE_URL}{url}"
            if not item_id:
                item_id = url or name
            if not name:
                continue
            listings.append(Listing(listing_id=item_id, title=name, city=city, url=url or self.BASE_URL))
        return listings

    def _search_html(self, query: str) -> list[Listing]:
        search_url = f"{self.BASE_URL}/search"
        try:
            status, html = self._http_get(search_url, {"q": query})
            if status != 200:
                return []
        except Exception:
            return []

        links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, flags=re.I | re.S)
        results: list[Listing] = []

        for href, inner in links:
            text = re.sub(r"<[^>]+>", " ", inner)
            text = re.sub(r"\s+", " ", text).strip()
            if not href or not text:
                continue
            if "bad bunny" not in text.lower() and "bad bunny" not in href.lower():
                continue
            absolute = href if href.startswith("http") else f"{self.BASE_URL}{href}"
            city = "Madrid" if "madrid" in text.lower() or "madrid" in href.lower() else ""
            results.append(Listing(listing_id=absolute, title=text, city=city, url=absolute))

        dedup: dict[str, Listing] = {item.listing_id: item for item in results}
        return list(dedup.values())

    def _filter_bad_bunny_madrid(self, listings: list[Listing]) -> list[Listing]:
        filtered: list[Listing] = []
        for item in listings:
            haystack = f"{item.title} {item.city} {item.url}".lower()
            if "bad bunny" in haystack and "madrid" in haystack:
                filtered.append(item)
        return filtered
