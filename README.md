# BadBunny Monitor

Bot de Telegram + monitor de TicketSwap para detectar entradas de **Bad Bunny en Madrid** y gestionar auto-carrito en modo test o real.

## Arranque único (instala + ejecuta todo)

Usa un único script para dejar todo listo y arrancar panel + monitor:

```bash
./scripts/run_all.sh
```

Este script:
- crea `.venv` si no existe,
- instala dependencias,
- crea `.env` inicial con token/chat (si falta),
- lanza el panel web en `http://localhost:8080`.

## Panel web único (UI + control de proceso)

Desde la página puedes:

1. Editar completo el fichero `.env`.
2. Guardar cambios.
3. Guardar y relanzar todo el proceso.
4. Iniciar/reiniciar/detener el monitor.
5. Ver traza en vivo de `monitor.log` en la parte inferior.

## Seguimiento de progreso (consultas TicketSwap)

El monitor informa en logs y Telegram:
- queries iterativas que está probando,
- estado de llamadas API/HTML,
- número de resultados filtrados y nuevos.

Además, con `TICKETSWAP_EVENT_URL` hace análisis directo de la página del evento (incluyendo señales de `__NEXT_DATA__`, `alert` y `listing`).

## Comportamiento especial en modo TEST

Si en modo `test` no hay resultados nuevos pero la búsqueda sí devuelve entradas del evento, el sistema intenta carrito con una de ellas para validar flujo de extremo a extremo.

## Lógica de packs de entradas

Si TicketSwap detecta un pack (ej. 3 entradas), el monitor calcula:

`precio unitario = precio total del pack / número de entradas`

En modo real, la comparación contra el máximo usa ese precio unitario.

## Variables de entorno

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TICKETSWAP_QUERY` (default: `bad bunny madrid`)
- `TICKETSWAP_EVENT_URL` (URL de evento a inspeccionar)
- `POLL_INTERVAL_SECONDS` (default: `30`)
- `MAX_PRICE_EUR` (valor inicial)
- `OPERATION_MODE` (`test` o `real`, valor inicial)
- `PROGRESS_TO_TELEGRAM` (`true/false` para enviar trazas)
- `RUNTIME_STATE_PATH` (default: `runtime_state.json`)
- `TICKETSWAP_BUYER_COOKIE`

## Ejecución manual alternativa

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m badbunny_monitor.gui
```

## Testing

```bash
pytest -q
```
