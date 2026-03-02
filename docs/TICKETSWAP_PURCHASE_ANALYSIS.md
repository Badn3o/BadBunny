# Análisis técnico de compra real en TicketSwap

Este documento resume el análisis práctico realizado sobre la página de evento y qué se ha replicado en el cliente.

## 1) URL objetivo analizada

- `https://www.ticketswap.es/concert-tickets/bad-bunny-madrid-estadio-riyadh-air-metropolitano-2026-06-15-WEMPrvGmoQbQ9uQf93LDSU`

## 2) Hallazgos de tráfico y datos

### 2.1 Carga de la página del evento

En la sesión de análisis con navegador automatizado se observaron peticiones a:

- `POST /api/exposure`
- `POST /api/graphql/public?version=4`

Esto confirma el uso de GraphQL público para parte de datos.

### 2.2 Datos embebidos en `__NEXT_DATA__`

Se localizaron en `initialApolloState`:

- `eventId` (formato global ID base64)
- entidades `Event:*`
- entidades `Listing:*`
- `availableTicketsCount`, `ticketAlertsCount`, `isBuyingBlocked`, etc.

Además se obtuvieron `uri` de listings con rutas tipo:

- `https://www.ticketswap.com/listing/<slug>/<numeric_listing_id>/<token>`

## 3) Estrategia implementada para compra real

Dado que TicketSwap combina flujo público y privado autenticado, se implementó una estrategia robusta por capas:

1. **Intento GraphQL prioritario**:
   - endpoint `POST /api/graphql/private?version=4`
   - fallback `POST /api/graphql/public?version=4`
   - payload en formato de array de operaciones (alineado con llamadas observadas)
   - prueba de varias mutaciones candidatas (`addListingToCart`, `addToCart`, `createCheckoutFromListing`) y variantes de `listingId`.

2. **Fallback REST**:
   - `/api/cart/v1/items`
   - `/api/checkout/v1/cart/items`
   - `/api/buyer/cart/items`

3. **Autenticación**:
   - se requiere `TICKETSWAP_BUYER_COOKIE` válido.

## 4) Limitaciones reales esperables

- Anti-bot / challenge dinámico en páginas de listing.
- Cambios frecuentes de mutaciones y campos GraphQL.
- Requisitos de sesión (cookie, CSRF, huella de navegador).

Por eso se mantiene traza detallada y múltiples intentos de endpoint/mutación.

## 5) Cómo verificar compra real paso a paso

1. Iniciar en modo `test`.
2. Confirmar trazas de búsqueda y de intento de carrito en `monitor.log` (visible también en UI).
3. Validar en Telegram mensaje de resultado `🛒✅` o `🛒❌`.
4. Si falla autenticación, renovar `TICKETSWAP_BUYER_COOKIE` desde sesión web activa.
5. Pasar a modo `real` cuando el flujo de test sea consistente.
