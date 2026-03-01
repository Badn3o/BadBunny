from badbunny_monitor.tickerswap import TicketSwapClient


def test_extract_ticket_count_patterns() -> None:
    assert TicketSwapClient._extract_ticket_count("Pack de 3 entradas") == 3
    assert TicketSwapClient._extract_ticket_count("2 tickets juntos") == 2
    assert TicketSwapClient._extract_ticket_count("x4 entradas") == 4
    assert TicketSwapClient._extract_ticket_count("entrada suelta") == 1
