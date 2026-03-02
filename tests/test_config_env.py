from pathlib import Path

from badbunny_monitor.config import load_settings


def test_load_settings_handles_utf8_bom_in_env(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\ufeffTELEGRAM_BOT_TOKEN=token123\nTELEGRAM_CHAT_ID=chat123\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    settings = load_settings()

    assert settings.telegram_bot_token == "token123"
    assert settings.telegram_chat_id == "chat123"


def test_load_settings_uses_existing_env_file_without_autogenerate(tmp_path, monkeypatch) -> None:
    Path(tmp_path / ".env").write_text(
        "TELEGRAM_BOT_TOKEN=abc\nTELEGRAM_CHAT_ID=999\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    settings = load_settings()

    assert settings.telegram_bot_token == "abc"
    assert settings.telegram_chat_id == "999"
