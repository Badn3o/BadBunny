# BadBunny Monitor

Bot de Telegram + monitor de TicketSwap para detectar en tiempo real (por sondeo) nuevas entradas de **Bad Bunny en Madrid** y avisarlas por Telegram.

## Qué hace

- Consulta TicketSwap cada `POLL_INTERVAL_SECONDS`.
- Filtra resultados por:
  - evento relacionado con Bad Bunny
  - ciudad Madrid
- Detecta nuevas entradas comparando contra histórico en memoria.
- Envía alertas al chat de Telegram configurado.

> Nota: TicketSwap puede cambiar su estructura/API; este proyecto usa un conector HTTP robusto con fallback HTML y puede requerir ajustes futuros.

## Requisitos

- Python 3.10+
- Token de bot de Telegram (BotFather)
- Chat ID destino (usuario o grupo)

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
- `RUN_ONCE`: `true` para ejecutar una sola iteración (útil en pruebas).

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

## Comandos del bot

- `/start`: confirma que el bot está vivo.
- `/status`: devuelve estado del monitor (última ejecución, elementos nuevos, etc.).
- `/help`: ayuda rápida.

## Testing

```bash
pytest -q
```
