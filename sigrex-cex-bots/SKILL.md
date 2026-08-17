---
name: sigrex-cex-bots
description: Configure Sigrex CEX exchange credentials and CEX Signal Bots for spot or futures trading. Use when working with Binance, Bitget, MEXC, Gate.io, Kraken, Hyperliquid, Alpaca, exchange API keys, amount sizing, or CEX bot activation.
metadata:
  author: sigrex
  version: "1.0"
---

# Sigrex CEX Signal Bots

Use this skill for centralized-exchange credentials and bots. Keep exchange
private keys server-side, disable withdrawals on exchange credentials, and
require confirmation before activation or a live signal.

## Supported Exchange Catalog

Use the live exchange catalog instead of hardcoding IDs, but these IDs are
documented:

| Exchange | Services | Catalog IDs | Constraint |
| --- | --- | --- | --- |
| Alpaca | spot | `1` | No paper trading |
| Binance | spot, USD-M futures | `2`, `3` | USD-M futures only |
| Bitget | spot, USD-M futures | `13`, `14` | USD-M futures only |
| MEXC | spot, USD-M futures | `4`, `16` | USD-M futures only |
| Gate.io | spot, USD-M futures | `8`, `9` | USD-M futures only |
| Kraken | spot, futures | `6`, `7` | Verify current catalog |
| Hyperliquid | spot, futures | `11`, `12` | USDC only |

Discover with the signed API:

```text
GET /exchange
GET /exchange/cex
```

Useful catalog fields are `id`, `type`, `name`, `service`, `enabled`,
`hasExchangeRate`, and `extra`.

## Exchange Credential Workflow

Create and test an exchange connection before creating a bot:

```json
{
  "exchangeId": 2,
  "name": "Binance spot",
  "publicKey": "exchange-public-key",
  "privateKey": "exchange-secret",
  "extra": "optional-passphrase"
}
```

Endpoints under `/api/v2`:

```text
GET  /api/exchange
POST /api/exchange
POST /api/exchange/test
PUT  /api/exchange/{id}/status
GET  /api/exchange/bot/signal/{id}?page=1&limit=50
DELETE /api/exchange/{id}
```

Spot and futures need separate connections. Credentials cannot be edited. To
rotate them, detach all linked bots, delete the connection, and create a new
one. `extra` is an exchange-specific string when required. A linked key can
return `409` on deletion.

## CEX Bot Configuration

Create under `/api/v2/bot/signal/cex`:

```json
{
  "name": "BTC spot bot",
  "webhook_id": 123,
  "api_id": 456,
  "symbol": "BTCUSDT",
  "pair_base": "BTC",
  "pair_quote": "USDT",
  "amount_from_signal": false,
  "amount": 100,
  "is_quote": true,
  "delay": 10
}
```

Required fields are `webhook_id`, the user exchange connection `api_id`,
`symbol`, and `amount_from_signal`. Optional fields include `name`,
`folder_id`, `pair_base`, `pair_quote`, `amount`, `is_quote`, and `delay`.

Do not confuse `api_id` with the catalog `exchangeId`: `api_id` identifies the
user's stored credential.

## Amount Rules

- `amount_from_signal: true` uses the incoming payload `size`.
- `amount_from_signal: false` uses configured `amount`.
- `is_quote: true` makes configured amount quote currency; false makes it base
  currency.
- Opening `size` is quote currency; closing `size` is base currency.
- The amount must satisfy the exchange pair's minimum notional.
- Symbols are exchange-specific; verify whether the venue expects `BTCUSDT`,
  `BTC/USDT`, or another format.

## Bot Lifecycle

```text
GET/POST /bot/signal/cex
GET/PUT/DELETE /bot/signal/cex/{id}
GET /bot/signal/cex/total
PUT /bot/signal/cex/{id}/status       {"status":"ACTIVE|INACTIVE"}
POST /bot/signal/cex/duplicate       {"id":"bot-id"}
```

Create the Bot Webhook first, connect the tested exchange credential, create
the bot, keep it inactive while testing, send a `TEST` payload, and activate
only after the symbol and sizing behavior are confirmed. Package or bot
limits may return `402`.

## Canonical Docs

- https://docs.sigrex.io/cex-signal-bot/exchange-api-key.md
- https://docs.sigrex.io/cex-signal-bot/creating-a-cex-signal-bot.md
- https://docs.sigrex.io/api-reference/reference/exchanges.md
- https://docs.sigrex.io/api-reference/reference/api-keys/exchange-api-keys.md
- https://docs.sigrex.io/api-reference/reference/signal-bots/cex-bot.md
