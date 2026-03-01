from badbunny_monitor.tickerswap import Listing, TicketSwapClient


def test_filters_bad_bunny_madrid() -> None:
    client = TicketSwapClient()
    items = [
        Listing("1", "Bad Bunny - Madrid", "Madrid", "https://example/1"),
        Listing("2", "Bad Bunny - Barcelona", "Barcelona", "https://example/2"),
        Listing("3", "Another Artist - Madrid", "Madrid", "https://example/3"),
    ]

    filtered = client._filter_bad_bunny_madrid(items)

    assert [x.listing_id for x in filtered] == ["1"]
