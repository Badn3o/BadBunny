from badbunny_monitor.monitor import SeenListings
from badbunny_monitor.tickerswap import Listing


def test_seen_listings_detects_only_new() -> None:
    seen = SeenListings()
    batch = [
        Listing("a", "Bad Bunny Madrid", "Madrid", "https://example/a"),
        Listing("b", "Bad Bunny Madrid", "Madrid", "https://example/b"),
    ]

    first = seen.find_new(batch)
    second = seen.find_new(batch)

    assert len(first) == 2
    assert len(second) == 0
