from badbunny_monitor.monitor import BadBunnyMonitor
from badbunny_monitor.tickerswap import Listing, TicketSwapClient


def test_extract_price_supports_comma_and_dot() -> None:
    assert TicketSwapClient._extract_price("€123.45") == 123.45
    assert TicketSwapClient._extract_price("EUR 99,90") == 99.9
    assert TicketSwapClient._extract_price("sin precio") is None


def test_should_try_buy_requires_limit_and_price() -> None:
    item_ok = Listing("1", "Bad Bunny Madrid", "Madrid", "https://x", price_eur=120)
    item_expensive = Listing("2", "Bad Bunny Madrid", "Madrid", "https://x", price_eur=250)
    item_no_price = Listing("3", "Bad Bunny Madrid", "Madrid", "https://x", price_eur=None)

    assert BadBunnyMonitor._should_try_buy(item_ok, 150) is True
    assert BadBunnyMonitor._should_try_buy(item_expensive, 150) is False
    assert BadBunnyMonitor._should_try_buy(item_no_price, 150) is False
    assert BadBunnyMonitor._should_try_buy(item_ok, None) is False
