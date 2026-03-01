from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


@dataclass
class MonitorState:
    iterations: int = 0
    last_check_iso: str | None = None
    last_new_items: int = 0
    max_price_eur: float | None = None
    operation_mode: str = "real"
    last_cart_attempts: int = 0
    last_cart_successes: int = 0


class TelegramNotifier:
    def __init__(
        self,
        token: str,
        chat_id: str,
        initial_max_price_eur: float | None = None,
        initial_operation_mode: str = "real",
    ) -> None:
        self.token = token
        self.chat_id = chat_id
        mode = initial_operation_mode if initial_operation_mode in {"real", "test"} else "real"
        self.state = MonitorState(max_price_eur=initial_max_price_eur, operation_mode=mode)
        self.app = Application.builder().token(token).build()
        self.app.bot_data["state"] = self.state
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.app.add_handler(CommandHandler("start", self._start))
        self.app.add_handler(CommandHandler("help", self._help))
        self.app.add_handler(CommandHandler("status", self._status))
        self.app.add_handler(CommandHandler("max", self._max_price))
        self.app.add_handler(CommandHandler("mode", self._mode))

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "✅ Bot activo. Monitorizando TicketSwap para Bad Bunny Madrid."
        )

    async def _help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "Comandos disponibles:\n"
            "/start\n"
            "/status\n"
            "/max <precio_en_eur> (ej: /max 180)\n"
            "/max off (desactivar compra automática)\n"
            "/mode test | /mode real\n"
            "/help"
        )

    async def _status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        state: MonitorState = context.application.bot_data["state"]
        max_price = f"{state.max_price_eur:.2f}€" if state.max_price_eur is not None else "OFF"
        await update.effective_message.reply_text(
            f"Iteraciones: {state.iterations}\n"
            f"Último chequeo: {state.last_check_iso or 'N/A'}\n"
            f"Nuevos elementos último chequeo: {state.last_new_items}\n"
            f"Modo: {state.operation_mode.upper()}\n"
            f"Precio máximo auto-compra: {max_price}\n"
            f"Intentos de carrito (último ciclo): {state.last_cart_attempts}\n"
            f"Compras al carrito exitosas (último ciclo): {state.last_cart_successes}"
        )

    async def _max_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            current = self.get_max_price_eur()
            shown = f"{current:.2f}€" if current is not None else "OFF"
            await update.effective_message.reply_text(f"Precio máximo actual: {shown}")
            return

        raw = context.args[0].strip().lower()
        if raw in {"off", "disable", "none"}:
            self.set_max_price_eur(None)
            await update.effective_message.reply_text("Auto-compra desactivada.")
            return

        try:
            value = float(raw.replace(",", "."))
            if value <= 0:
                raise ValueError
        except ValueError:
            await update.effective_message.reply_text("Valor inválido. Usa por ejemplo: /max 175")
            return

        self.set_max_price_eur(value)
        await update.effective_message.reply_text(f"✅ Precio máximo actualizado a {value:.2f}€")

    async def _mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.effective_message.reply_text(f"Modo actual: {self.get_operation_mode().upper()}")
            return
        requested = context.args[0].strip().lower()
        if requested not in {"real", "test"}:
            await update.effective_message.reply_text("Modo inválido. Usa /mode test o /mode real")
            return
        self.set_operation_mode(requested)
        await update.effective_message.reply_text(f"✅ Modo actualizado a {requested.upper()}")

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

    def mark_iteration(self, new_items: int, cart_attempts: int = 0, cart_successes: int = 0) -> None:
        self.state.iterations += 1
        self.state.last_new_items = new_items
        self.state.last_cart_attempts = cart_attempts
        self.state.last_cart_successes = cart_successes
        self.state.last_check_iso = datetime.now(timezone.utc).isoformat()

    def set_max_price_eur(self, value: float | None) -> None:
        self.state.max_price_eur = value

    def get_max_price_eur(self) -> float | None:
        return self.state.max_price_eur

    def set_operation_mode(self, value: str) -> None:
        self.state.operation_mode = value if value in {"real", "test"} else "real"

    def get_operation_mode(self) -> str:
        return self.state.operation_mode
