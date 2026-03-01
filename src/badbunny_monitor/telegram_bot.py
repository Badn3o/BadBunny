from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except Exception:  # pragma: no cover
    Update = object
    Application = None
    CommandHandler = None
    ContextTypes = None


@dataclass
class MonitorState:
    iterations: int = 0
    last_check_iso: str | None = None
    last_new_items: int = 0


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        if Application is None:
            raise RuntimeError(
                "Falta dependencia python-telegram-bot. Instala requirements para ejecutar el bot."
            )
        self.token = token
        self.chat_id = chat_id
        self.state = MonitorState()
        self.app = Application.builder().token(token).build()
        self.app.bot_data["state"] = self.state
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.app.add_handler(CommandHandler("start", self._start))
        self.app.add_handler(CommandHandler("help", self._help))
        self.app.add_handler(CommandHandler("status", self._status))

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "✅ Bot activo. Monitorizando TicketSwap para Bad Bunny Madrid."
        )

    async def _help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "Comandos disponibles:\n/start\n/status\n/help"
        )

    async def _status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        state: MonitorState = context.application.bot_data["state"]
        await update.effective_message.reply_text(
            f"Iteraciones: {state.iterations}\n"
            f"Último chequeo: {state.last_check_iso or 'N/A'}\n"
            f"Nuevos elementos último chequeo: {state.last_new_items}"
        )

    async def start(self) -> None:
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)

    async def stop(self) -> None:
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()

    async def send_message(self, text: str) -> None:
        await self.app.bot.send_message(chat_id=self.chat_id, text=text, disable_web_page_preview=False)

    def mark_iteration(self, new_items: int) -> None:
        self.state.iterations += 1
        self.state.last_new_items = new_items
        self.state.last_check_iso = datetime.now(timezone.utc).isoformat()
