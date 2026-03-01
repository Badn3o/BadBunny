# BadBunny Monitor (Windows + Linux/macOS)

Bot de Telegram + monitor de TicketSwap para detectar entradas de **Bad Bunny en Madrid** y gestionar auto-carrito en modo `test` o `real`.

---

## 1) Ejecución rápida en **Windows** (recomendado)

### Opción A: PowerShell (recomendada)

1. Abre **PowerShell** en la carpeta del proyecto.
2. Ejecuta:

```powershell
.\scripts\run_all.ps1
```

### Opción B: CMD

1. Abre **Símbolo del sistema (cmd)** en la carpeta del proyecto.
2. Ejecuta:

```cmd
scripts\run_all.cmd
```

Ambas opciones:
- crean `.venv` si no existe,
- instalan dependencias,
- **usan el `.env` real existente** (no autogeneran valores),
- arrancan el panel único en `http://localhost:8080`.

---

## 2) Ejecución rápida en Linux/macOS

```bash
./scripts/run_all.sh
```

---

## 3) Panel único web (`http://localhost:8080`)

### Nota importante en Windows (error ModuleNotFoundError)

Si antes veías el error:

`Error while finding module specification for 'badbunny_monitor.main' (ModuleNotFoundError)`

ya está corregido: el panel ahora relanza el monitor usando el **mismo intérprete Python activo** (venv) y fuerza `PYTHONPATH=src` como fallback.


Desde la página puedes:
1. Editar completo el archivo `.env`.
2. Guardar cambios sin que la UI altere formato/valores.
3. Guardar y relanzar monitor.
4. Iniciar/Reiniciar/Detener monitor.
5. Ver traza en vivo (`monitor.log`) al final de la página.

Se corrigieron errores de relanzado en Windows y carga de `.env` con BOM UTF-8 (común en PowerShell).

---

## 4) Configuración de `.env` (paso a paso)

> Importante: debes tener un `.env` válido antes de arrancar. Los scripts ya no lo sobrescriben ni generan uno de ejemplo automáticamente.

Variables principales:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TICKETSWAP_QUERY`
- `TICKETSWAP_EVENT_URL`
- `POLL_INTERVAL_SECONDS`
- `MAX_PRICE_EUR`
- `OPERATION_MODE` (`test` o `real`)
- `PROGRESS_TO_TELEGRAM`
- `RUNTIME_STATE_PATH`
- `TICKETSWAP_BUYER_COOKIE`

> Recomendación inicial: usar `OPERATION_MODE=test` hasta validar trazas y carrito.

---

## 5) Flujo de compra: cómo está implementado

El motor de carrito trabaja por capas para maximizar compatibilidad:

1. **GraphQL prioritario** (formato observado en la web):
   - `POST /api/graphql/private?version=4`
   - fallback `POST /api/graphql/public?version=4`
   - pruebas de mutaciones candidatas (`addListingToCart`, `addToCart`, `createCheckoutFromListing`).
2. **Fallback REST**:
   - `/api/cart/v1/items`
   - `/api/checkout/v1/cart/items`
   - `/api/buyer/cart/items`

En todos los casos es imprescindible `TICKETSWAP_BUYER_COOKIE` válido.

### Importante sobre modo TEST

En `test`, si no aparecen resultados nuevos pero sí hay entradas detectadas del evento, el sistema intenta carrito con una entrada existente para validar extremo a extremo.

---

## 6) Lógica de packs de entradas

Si TicketSwap muestra un pack (ej. 3 entradas):

`precio_unitario = precio_total / número_de_entradas`

En modo `real`, la comparación contra el máximo usa siempre el **precio unitario**.

---

## 7) Análisis detallado de compra real

Consulta el documento técnico:

- `docs/TICKETSWAP_PURCHASE_ANALYSIS.md`

Incluye hallazgos de la página objetivo, endpoints observados y estrategia de hardening del flujo de carrito.

---

## 8) Ejecución manual alternativa

```bash
python -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
pip install -e .[dev]
python -m badbunny_monitor.gui
```

---

## 9) Testing

```bash
pytest -q
```
