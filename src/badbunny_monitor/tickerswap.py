from __future__ import annotations

import asyncio
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
    price_eur: float | None = None


@dataclass(frozen=True)
class CartResult:
    success: bool
    status_code: int
    endpoint: str
    message: str


class TicketSwapClient:
    """Cliente de lectura para encontrar eventos/listados de TicketSwap."""

    BASE_URL = "https://www.ticketswap.com"

    def __init__(self, timeout_seconds: int = 12, buyer_cookie: str = "") -> None:
        self.timeout_seconds = timeout_seconds
        self.buyer_cookie = buyer_cookie

    async def search(self, query: str) -> list[Listing]:
        return await asyncio.to_thread(self._search_sync, query)

    def _search_sync(self, query: str) -> list[Listing]:
        from_api = self._search_json_api(query)
        if from_api:
            return self._filter_bad_bunny_madrid(from_api)
        from_html = self._search_html(query)
        return self._filter_bad_bunny_madrid(from_html)

    async def add_to_cart(self, listing: Listing) -> CartResult:
        return await asyncio.to_thread(self._add_to_cart_sync, listing)

    def _add_to_cart_sync(self, listing: Listing) -> CartResult:
        if not self.buyer_cookie:
            return CartResult(False, 0, "", "Falta TICKETSWAP_BUYER_COOKIE para operar carrito")

        payload = {"listing_id": listing.listing_id, "quantity": 1}
        candidate_endpoints = [
            f"{self.BASE_URL}/api/cart/v1/items",
            f"{self.BASE_URL}/api/checkout/v1/cart/items",
            f"{self.BASE_URL}/api/buyer/cart/items",
        ]
        for endpoint in candidate_endpoints:
            try:
                status, body = self._http_post_json(endpoint, payload)
                if 200 <= status < 300:
                    return CartResult(True, status, endpoint, "Entrada añadida al carrito")
                if status in {401, 403}:
                    return CartResult(False, status, endpoint, "Sesión inválida/no autorizada")
                if status in {404, 405}:
                    continue
                return CartResult(False, status, endpoint, body[:180])
            except Exception as exc:
                last_error = str(exc)
                continue
        return CartResult(False, 0, "", f"No se pudo añadir al carrito. Último error: {locals().get('last_error', 'N/A')}")

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

    def _http_post_json(self, url: str, payload: dict[str, object]) -> tuple[int, str]:
        req = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "User-Agent": "Mozilla/5.0 (BadBunnyMonitor)",
                "Accept": "application/json, text/plain;q=0.9,*/*;q=0.8",
                "Content-Type": "application/json",
                "Cookie": self.buyer_cookie,
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
            price_text = str(item.get("price") or item.get("lowest_price") or "").strip() or None
            price_eur = self._extract_price(price_text or "")
            listings.append(
                Listing(
                    listing_id=item_id,
                    title=name,
                    city=city,
                    url=url or self.BASE_URL,
                    price_text=price_text,
                    price_eur=price_eur,
                )
            )
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
            price_eur = self._extract_price(text)
            price_text = f"€{price_eur:.2f}" if price_eur is not None else None
            results.append(
                Listing(
                    listing_id=absolute,
                    title=text,
                    city=city,
                    url=absolute,
                    price_text=price_text,
                    price_eur=price_eur,
                )
            )

        dedup: dict[str, Listing] = {item.listing_id: item for item in results}
        return list(dedup.values())

    def _filter_bad_bunny_madrid(self, listings: list[Listing]) -> list[Listing]:
        filtered: list[Listing] = []
        for item in listings:
            haystack = f"{item.title} {item.city} {item.url}".lower()
            if "bad bunny" in haystack and "madrid" in haystack:
                filtered.append(item)
        return filtered

    @staticmethod
    def _extract_price(value: str) -> float | None:
        if not value:
            return None
        match = re.search(r"(\d+[\.,]?\d*)", value.replace(" ", ""))
        if not match:
            return None
        return float(match.group(1).replace(",", "."))
