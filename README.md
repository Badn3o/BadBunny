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

## Seguimiento de progreso (consultas TicketSwap)

Ahora el monitor informa en logs y en Telegram el progreso de cada ciclo:

- queries que está probando (iterativas),
- estado de llamadas API/HTML,
- número de resultados filtrados y nuevos.

Además, puedes fijar una URL concreta del evento (como la que enviaste) con `TICKETSWAP_EVENT_URL` para que el monitor haga análisis directo de esa página y trate de detectar estructura relacionada con alertas/listings.

## Lógica de packs de entradas

Si TicketSwap detecta un pack (ej. 3 entradas), el monitor calcula:

`precio unitario = precio total del pack / número de entradas`

En modo real, la comparación contra el máximo usa ese precio unitario.

## Variables de entorno

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TICKETSWAP_QUERY` (default: `bad bunny madrid`)
- `TICKETSWAP_EVENT_URL` (URL de evento a inspeccionar de forma directa)
- `POLL_INTERVAL_SECONDS` (default: `30`)
- `MAX_PRICE_EUR` (valor inicial)
- `OPERATION_MODE` (`test` o `real`, valor inicial)
- `PROGRESS_TO_TELEGRAM` (`true/false` para enviar trazas)
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
