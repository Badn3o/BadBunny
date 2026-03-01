# BadBunny Monitor

Bot de Telegram + monitor de TicketSwap para detectar nuevas entradas de **Bad Bunny en Madrid** y, si cumplen precio máximo, intentar enviarlas al carrito lo más rápido posible.

## Qué hace

- Consulta TicketSwap cada `POLL_INTERVAL_SECONDS`.
- Filtra resultados por `bad bunny` + `madrid`.
- Detecta nuevas entradas (deduplicación en memoria).
- Notifica por Telegram cada entrada nueva.
- Si el precio detectado es `<= max` configurado, intenta **add to cart** inmediatamente.

> Nota importante: TicketSwap puede cambiar APIs/endpoints y mecanismos anti-bot; puede requerir ajustes periódicos.

## Requisitos

- Python 3.10+
- Token de bot de Telegram (BotFather)
- Chat ID destino
- Cookie de sesión de comprador de TicketSwap para operaciones de carrito

## Configuración

1. Copia `.env.example` a `.env`.
2. Rellena variables.

```bash
cp .env.example .env
```

Variables principales:

- `TELEGRAM_BOT_TOKEN`: token del bot.
- `TELEGRAM_CHAT_ID`: chat donde mandar alertas.
- `TICKETSWAP_QUERY`: por defecto `bad bunny madrid`.
- `POLL_INTERVAL_SECONDS`: intervalo de sondeo, por defecto `30`.
- `MAX_PRICE_EUR`: máximo de auto-compra inicial (se puede cambiar por Telegram).
- `TICKETSWAP_BUYER_COOKIE`: cookie de sesión para intentar carrito.

## Comandos del bot

- `/start`
- `/status`
- `/help`
- `/max <precio>` (ej. `/max 175`) para activar/actualizar auto-compra.
- `/max off` para desactivar auto-compra.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Ejecución

```bash
badbunny-monitor
```

## Testing

```bash
pytest -q
```
