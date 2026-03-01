# BadBunny Monitor

Bot de Telegram + monitor de TicketSwap para detectar entradas de **Bad Bunny en Madrid** y gestionar auto-carrito en modo test o real.

## Interfaz gráfica (paso a paso)

Arranca la interfaz web local:

```bash
badbunny-monitor-ui
```

Abre `http://localhost:8080`.

La UI incluye guía para:

1. Dar de alta y crear el bot de Telegram (`@BotFather`, token, chat id).
2. Especificar precio máximo.
3. Activar modo **TEST** (intenta carrito siempre y notifica "entra a finalizar compra").
4. Activar modo **REAL** (mismo proceso, pero solo si precio unitario <= máximo).

La UI guarda estos valores en `runtime_state.json` y el monitor los aplica en cada ciclo.

## Lógica de packs de entradas

Si TicketSwap detecta un pack (ej. 3 entradas), el monitor calcula:

`precio unitario = precio total del pack / número de entradas`

En modo real, la comparación contra el máximo usa ese precio unitario.

## Variables de entorno

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TICKETSWAP_QUERY` (default: `bad bunny madrid`)
- `POLL_INTERVAL_SECONDS` (default: `30`)
- `MAX_PRICE_EUR` (valor inicial)
- `OPERATION_MODE` (`test` o `real`, valor inicial)
- `RUNTIME_STATE_PATH` (default: `runtime_state.json`)
- `TICKETSWAP_BUYER_COOKIE`

## Comandos del bot

- `/start`
- `/status`
- `/help`
- `/max <precio>` o `/max off`
- `/mode test` o `/mode real`

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Ejecución monitor

```bash
badbunny-monitor
```

## Testing

```bash
pytest -q
```
