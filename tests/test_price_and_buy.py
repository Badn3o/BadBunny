from badbunny_monitor.monitor import BadBunnyMonitor
from badbunny_monitor.tickerswap import Listing, TicketSwapClient


def test_extract_price_supports_comma_and_dot() -> None:
    assert TicketSwapClient._extract_price("€123.45") == 123.45
    assert TicketSwapClient._extract_price("EUR 99,90") == 99.9
    assert TicketSwapClient._extract_price("sin precio") is None


def test_pack_unit_price_is_used_in_real_mode() -> None:
    pack = Listing("1", "Bad Bunny Madrid pack 3 entradas", "Madrid", "https://x", total_price_eur=300, ticket_count=3)
    assert pack.unit_price_eur == 100
    assert BadBunnyMonitor._should_try_buy(pack, 100, "real") is True
    assert BadBunnyMonitor._should_try_buy(pack, 99, "real") is False


def test_test_mode_always_attempts_cart() -> None:
    expensive = Listing("2", "Bad Bunny Madrid", "Madrid", "https://x", total_price_eur=500, ticket_count=1)
    assert BadBunnyMonitor._should_try_buy(expensive, 10, "test") is True
