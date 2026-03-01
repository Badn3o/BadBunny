from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
import re
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Listing:
    listing_id: str
    title: str
    city: str
    url: str
    price_text: str | None = None
    total_price_eur: float | None = None
    ticket_count: int = 1

    @property
    def unit_price_eur(self) -> float | None:
        if self.total_price_eur is None or self.ticket_count <= 0:
            return None
        return self.total_price_eur / self.ticket_count


@dataclass(frozen=True)
class CartResult:
    success: bool
    status_code: int
    endpoint: str
    message: str


@dataclass(frozen=True)
class SearchResult:
    listings: list[Listing]
    trace: list[str]


class TicketSwapClient:
    BASE_URL = "https://www.ticketswap.com"

    def __init__(self, timeout_seconds: int = 12, buyer_cookie: str = "") -> None:
        self.timeout_seconds = timeout_seconds
        self.buyer_cookie = buyer_cookie

    async def search(self, query: str, event_url: str = "") -> SearchResult:
        return await asyncio.to_thread(self._search_sync, query, event_url)

    def _search_sync(self, query: str, event_url: str = "") -> SearchResult:
        trace: list[str] = []
        queries = self._build_query_candidates(query=query, event_url=event_url)
        trace.append(f"queries={queries}")

        aggregated: list[Listing] = []
        seen: set[str] = set()

        for candidate in queries:
            trace.append(f"searching query='{candidate}'")
            from_api = self._search_json_api(candidate, trace)
            if from_api:
                trace.append(f"api_results[{candidate}]={len(from_api)}")
                self._append_new(aggregated, seen, from_api)
            else:
                trace.append(f"api_results[{candidate}]=0")

            from_html = self._search_html(candidate, trace)
            trace.append(f"html_results[{candidate}]={len(from_html)}")
            self._append_new(aggregated, seen, from_html)

        if event_url:
            direct = self._search_event_page(event_url, trace)
            trace.append(f"direct_event_results={len(direct)}")
            self._append_new(aggregated, seen, direct)

        filtered = self._filter_bad_bunny_madrid(aggregated)
        trace.append(f"filtered_bad_bunny_madrid={len(filtered)}")
        logger.info("TicketSwap trace: %s", " | ".join(trace))
        return SearchResult(listings=filtered, trace=trace)

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

        last_error = "N/A"
        for endpoint in candidate_endpoints:
            try:
                status, body = self._http_post_json(endpoint, payload)
                if 200 <= status < 300:
                    return CartResult(True, status, endpoint, "Entrada añadida al carrito. Entra a finalizar compra")
                if status in {401, 403}:
                    return CartResult(False, status, endpoint, "Sesión inválida/no autorizada")
                if status in {404, 405}:
                    continue
                return CartResult(False, status, endpoint, body[:200])
            except Exception as exc:
                last_error = str(exc)

        return CartResult(False, 0, "", f"No se pudo añadir al carrito. Último error: {last_error}")

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
        try:
            with urlopen(req, timeout=self.timeout_seconds) as response:  # nosec B310
                status = getattr(response, "status", 200)
                body = response.read().decode("utf-8", errors="ignore")
                return status, body
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            return exc.code, body

    def _search_json_api(self, query: str, trace: list[str]) -> list[Listing]:
        url = f"{self.BASE_URL}/api/search/v2/events"
        try:
            status, body = self._http_get(url, {"query": query})
            trace.append(f"GET {url} status={status}")
            if status != 200:
                return []
            data = json.loads(body)
            return self._parse_api_payload(data)
        except Exception as exc:
            trace.append(f"GET {url} error={exc}")
            return []

    def _search_event_page(self, event_url: str, trace: list[str]) -> list[Listing]:
        try:
            status, html = self._http_get(event_url, {})
            trace.append(f"GET event_url status={status}")
            if status != 200:
                return []
        except Exception as exc:
            trace.append(f"GET event_url error={exc}")
            return []

        next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
        if not next_data_match:
            trace.append("event_url next_data=missing")
            return []

        try:
            payload = json.loads(next_data_match.group(1))
        except Exception as exc:
            trace.append(f"event_url next_data parse error={exc}")
            return []

        serialized = json.dumps(payload, ensure_ascii=False)
        trace.append("event_url next_data found")
        trace.append(f"event_url has_alert_keyword={'alert' in serialized.lower()}")
        trace.append(f"event_url has_listing_keyword={'listing' in serialized.lower()}")

        parsed: list[Listing] = []
        for price in re.finditer(r'"price"\s*:\s*"?([0-9]+(?:[\.,][0-9]+)?)', serialized):
            amount = float(price.group(1).replace(",", "."))
            parsed.append(
                Listing(
                    listing_id=f"event-{len(parsed)+1}",
                    title="Bad Bunny Madrid (event page)",
                    city="Madrid",
                    url=event_url,
                    price_text=f"€{amount:.2f}",
                    total_price_eur=amount,
                    ticket_count=1,
                )
            )
            if len(parsed) >= 5:
                break
        return parsed

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
            total_price = self._extract_price(price_text or "")
            ticket_count = self._extract_ticket_count(
                f"{item.get('number_of_tickets', '')} {item.get('quantity', '')} {name}"
            )
            listings.append(
                Listing(
                    listing_id=item_id,
                    title=name,
                    city=city,
                    url=url or self.BASE_URL,
                    price_text=price_text,
                    total_price_eur=total_price,
                    ticket_count=ticket_count,
                )
            )
        return listings

    def _search_html(self, query: str, trace: list[str]) -> list[Listing]:
        search_url = f"{self.BASE_URL}/search"
        try:
            status, html = self._http_get(search_url, {"q": query})
            trace.append(f"GET {search_url}?q={query} status={status}")
            if status != 200:
                return []
        except Exception as exc:
            trace.append(f"GET {search_url}?q={query} error={exc}")
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
            total_price = self._extract_price(text)
            price_text = f"€{total_price:.2f}" if total_price is not None else None
            ticket_count = self._extract_ticket_count(text)
            results.append(
                Listing(
                    listing_id=absolute,
                    title=text,
                    city=city,
                    url=absolute,
                    price_text=price_text,
                    total_price_eur=total_price,
                    ticket_count=ticket_count,
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

    @staticmethod
    def _extract_ticket_count(value: str) -> int:
        text = value.lower()
        patterns = [
            r"(\d+)\s*(tickets?|entradas?)",
            r"pack\s*de\s*(\d+)",
            r"x\s*(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                count = int(match.group(1))
                return count if count > 0 else 1
        return 1

    @staticmethod
    def _append_new(target: list[Listing], seen: set[str], source: list[Listing]) -> None:
        for item in source:
            if item.listing_id in seen:
                continue
            seen.add(item.listing_id)
            target.append(item)

    @staticmethod
    def _build_query_candidates(query: str, event_url: str) -> list[str]:
        candidates: list[str] = []
        raw = (query or "bad bunny madrid").strip()
        if raw:
            candidates.append(raw)

        lowered = raw.lower()
        if "bad bunny" not in lowered:
            candidates.append(f"bad bunny {raw}".strip())
        if "madrid" not in lowered:
            candidates.append(f"{raw} madrid".strip())

        if event_url:
            slug = TicketSwapClient._extract_slug_from_url(event_url)
            slug_words = re.sub(r"[-_]", " ", slug).strip()
            if slug_words:
                candidates.append(slug_words)
                condensed = " ".join(slug_words.split()[:6]).strip()
                if condensed:
                    candidates.append(condensed)

        unique: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = candidate.lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique[:8]

    @staticmethod
    def _extract_slug_from_url(url: str) -> str:
        try:
            path = urlparse(url).path.strip("/")
        except Exception:
            return ""
        if not path:
            return ""
        return path.split("/")[-1]
