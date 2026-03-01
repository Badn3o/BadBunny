from badbunny_monitor.tickerswap import TicketSwapClient


EVENT_URL = "https://www.ticketswap.es/concert-tickets/bad-bunny-madrid-estadio-riyadh-air-metropolitano-2026-06-15-WEMPrvGmoQbQ9uQf93LDSU"


def test_extract_slug_from_url() -> None:
    slug = TicketSwapClient._extract_slug_from_url(EVENT_URL)
    assert slug.endswith("WEMPrvGmoQbQ9uQf93LDSU")


def test_build_query_candidates_includes_slug_words() -> None:
    candidates = TicketSwapClient._build_query_candidates("bad bunny madrid", EVENT_URL)
    joined = " | ".join(candidates).lower()
    assert "bad bunny madrid" in joined
    assert "estadio" in joined
    assert "metropolitano" in joined
