from pathlib import Path

from badbunny_monitor.communication import build_communication_profile
from badbunny_monitor.config import Settings
from badbunny_monitor.tracing import TraceManager


def test_build_communication_profile() -> None:
    settings = Settings(
        telegram_bot_token="t",
        telegram_chat_id="c",
        ticketswap_query="bad bunny",
        ticketswap_event_url="https://x",
        max_price_eur=123.0,
        target_quantity=2,
    )
    profile = build_communication_profile(settings)
    assert profile.bot_token == "t"
    assert profile.chat_id == "c"
    assert profile.target_url == "https://x"
    assert profile.target_quantity == 2


def test_trace_manager_status_roundtrip(tmp_path) -> None:
    log = tmp_path / "m.log"
    status = tmp_path / "s.json"
    tracer = TraceManager(log_path=str(log), status_path=str(status))
    tracer.record("INFO", "hello", a=1)
    tracer.update_status(bot_connected=True, scraper_progress="running", last_result="ok")
    data = tracer.read_status()
    assert data["bot_connected"] is True
    assert data["scraper_progress"] == "running"
    assert data["last_result"] == "ok"
    assert Path(log).exists()
