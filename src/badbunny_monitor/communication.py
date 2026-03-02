from __future__ import annotations

from dataclasses import dataclass

from .config import Settings


@dataclass(frozen=True)
class CommunicationProfile:
    bot_token: str
    chat_id: str
    target_url: str
    search_term: str
    max_price_eur: float | None
    target_quantity: int


def build_communication_profile(settings: Settings) -> CommunicationProfile:
    return CommunicationProfile(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
        target_url=settings.ticketswap_event_url,
        search_term=settings.ticketswap_query,
        max_price_eur=settings.max_price_eur,
        target_quantity=settings.target_quantity,
    )
