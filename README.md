# BadBunny Monitor (aplicación única modular)

Aplicación única con arquitectura modular para monitorizar TicketSwap, comunicar por Telegram, trazar ejecución y controlar todo desde UI.

## Arquitectura modular

1. **Módulo de comunicación** (`communication.py` + `config.py`)
   - Gestiona: token bot, chat id, URL objetivo, concepto búsqueda, precio máximo y número objetivo de entradas.
2. **Módulo scraping/captura** (`scraper.py` + `tickerswap.py`)
   - Estrategias iterativas de búsqueda y captura de venta (GraphQL + fallback REST).
3. **Módulo de trazas** (`tracing.py`)
   - Registro continuo de ejecución y estado (`monitor.log`, `runtime_status.json`).
4. **Módulo de visualización/UI** (`gui.py`)
   - Editor `.env`, controles de proceso, reinicio total y semáforos de salud.

Todo se ejecuta encapsulado como una sola app desde el panel web.

---

## Arranque (Windows / Linux / macOS)

- PowerShell: `./scripts/run_all.ps1`
- CMD: `scripts\\run_all.cmd`
- Linux/macOS: `./scripts/run_all.sh`

> Los scripts no sobreescriben `.env`. Debes tener `.env` real ya configurado.

---

## Variables de comunicación (.env)

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TICKETSWAP_EVENT_URL`
- `TICKETSWAP_QUERY`
- `MAX_PRICE_EUR`
- `TARGET_QUANTITY` (número de entradas objetivo)
- `OPERATION_MODE` (`test`/`real`)
- `TICKETSWAP_BUYER_COOKIE`
- `RUNTIME_STATUS_PATH` (estado de semáforos)

---

## Panel UI (`http://localhost:8080`)

- Semáforos:
  - Bot Telegram: verde/rojo
  - Scraping: verde/ámbar
- Estado proceso monitor
- Botones: iniciar, reiniciar, **reiniciar TODO**, detener
- Editor `.env`
- Traza completa en vivo (`monitor.log`)

---

## Comportamiento en modo TEST

Si no hay resultados nuevos pero sí listings del evento, se intenta captura con uno existente para verificar flujo completo.

---

## Testing

```bash
pytest -q
```
