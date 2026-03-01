from badbunny_monitor.tickerswap import Listing, TicketSwapClient


def test_extract_listing_numeric_id_from_url() -> None:
    url = "https://www.ticketswap.com/listing/bad-bunny/16119618/cac534feaf"
    assert TicketSwapClient._extract_listing_numeric_id(url) == "16119618"


def test_try_add_to_cart_graphql_returns_none_without_post_success() -> None:
    client = TicketSwapClient(timeout_seconds=1, buyer_cookie="cookie=ok")
    listing = Listing(
        listing_id="TGlzdGluZzoxNjExOTYxOA==",
        title="Bad Bunny",
        city="Madrid",
        url="https://www.ticketswap.com/listing/bad-bunny/16119618/cac534feaf",
    )

    def fake_post(url: str, payload: dict[str, object] | list[dict[str, object]]):
        return 500, '{"errors":[{"message":"fail"}]}'

    client._http_post_json = fake_post  # type: ignore[method-assign]
    result = client._try_add_to_cart_graphql(listing)
    assert result is not None
    assert result.success is False
