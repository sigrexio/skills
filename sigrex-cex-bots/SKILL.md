---
name: sigrex-cex-bots
description: Connect centralized-exchange API keys to Sigrex and configure CEX Signal Bots for spot or USD-M futures on Binance, Bitget, MEXC, Gate.io, Kraken, Hyperliquid or Alpaca, including credential testing and rotation, bot fields, symbol formats, quote/base amount sizing, amount-from-signal, delay/frequency, folders, activation and troubleshooting. Use when setting up or debugging any CEX bot or exchange API key on Sigrex.
metadata:
  author: sigrex
  version: "2.0"
---

# Sigrex CEX Signal Bots

A CEX Signal Bot listens to one Bot Webhook and, for each matching signal,
places an order on a centralized exchange using one stored API-key
connection. Setup is: **exchange API key, then Bot Webhook, then bot**.

## Supported Exchanges

| Exchange | Spot `exchangeId` | Futures `exchangeId` | Constraints |
| --- | --- | --- | --- |
| Alpaca | `1` | - | Live accounts only; paper-trading keys rejected; `pair_base`/`pair_quote` not required |
| Binance | `2` | `3` | Futures: USD-M only |
| MEXC | `4` | `16` | Futures: USD-M only |
| Kraken | `6` | `7` | |
| Gate.io | `8` | `9` | Futures: USD-M only |
| Hyperliquid | `11` | `12` | USDC only |
| Bitget | `13` | `14` | Futures: USD-M only |

Confirm with `GET /api/v2/exchange/cex`. A catalog entry with `extra: true`
needs an additional credential value beyond key and secret (sent as the
`extra` string, e.g. an API passphrase); the docs do not list per-exchange
meanings, so use the label the dashboard shows for that exchange.

## Step 1: Exchange API Key

Create the key on the exchange first. Recommended exchange-side settings:
trading enabled, **withdrawals disabled**, and the correct product (spot vs
futures). Then connect it:

```json
POST /api/v2/api/exchange/test
{"exchangeId": 2, "publicKey": "<api-key>", "privateKey": "<api-secret>"}

POST /api/v2/api/exchange
{"exchangeId": 2, "name": "Binance spot main", "publicKey": "<api-key>", "privateKey": "<api-secret>"}
```

Fields: `exchangeId` (required, number), `publicKey` (required),
`privateKey` (required), `name` (optional, max 255), `extra` (optional
string). Sigrex validates the key with a live test request on creation;
invalid keys return `400`.

Rules:

- **One connection per product.** Spot and futures on the same exchange need
  two connections (e.g. `exchangeId` `2` and `3`).
- **Immutable.** Keys and exchange cannot be edited. To rotate: list linked
  bots (`GET /api/exchange/bot/signal/{id}?page=1&limit=50`), repoint or
  delete them, delete the connection (`409` while still linked), create a new
  one, reattach.
- Keys are encrypted server-side and decrypted only at execution time.
- `PUT /api/exchange/{id}/status {"status":"INACTIVE"}` disables a key.
- Collect secrets through a secure channel; never echo them back.

## Step 2: Bot Webhook

Create a Bot Webhook (prefer key protection) as described in
`sigrex-webhooks`. Note its `id`.

## Step 3: Create The Bot

```json
POST /api/v2/bot/signal/cex
{
  "name": "BTC spot - TV breakout",
  "webhook_id": 101,
  "api_id": 202,
  "symbol": "BTCUSDT",
  "pair_base": "BTC",
  "pair_quote": "USDT",
  "amount_from_signal": false,
  "amount": 25,
  "is_quote": true,
  "delay": 10
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `webhook_id` | yes | Bot Webhook the bot listens to |
| `api_id` | yes | Your stored exchange connection ID (not the catalog `exchangeId`) |
| `symbol` | yes | Exchange-specific symbol; incoming signals must use the same string |
| `amount_from_signal` | yes | `true`: use the signal's `size`; `false`: use `amount` |
| `amount` | when `amount_from_signal` is false | Fixed trade amount |
| `is_quote` | no | `true`: `amount` is in quote currency (USDT); `false`: base (BTC) |
| `pair_base`, `pair_quote` | no (auto-filled in the UI; not needed on Alpaca) | Base and quote assets of `symbol`; send them via the API |
| `delay` | no | Rate limit ("Frequency" in the UI). API text: "10 means 10 in 1 second". Extra signals inside the window are dropped |
| `name` | no | Defaults to the symbol |
| `folder_id` | no | Folder to place the bot in |

The update body (`PUT /bot/signal/cex/{id}`) has the same fields and the
same required set. New bots should stay `INACTIVE` until tested.

## Symbols

The bot's `symbol` must match the exchange's own format **and** the symbol
in every signal. Formats differ (`BTCUSDT` vs `BTC_USDT`); Hyperliquid
examples use `BTCUSDC`. Look up the exact market name on the exchange, use it
in the bot, in TradingView alerts, and in strategy signal symbols.

## Sizing

| Bot setting | Signal `size` | Result |
| --- | --- | --- |
| `amount_from_signal: false`, `amount: 25`, `is_quote: true` | ignored | Opens 25 USDT worth |
| `amount_from_signal: false`, `amount: 0.001`, `is_quote: false` | ignored | Opens 0.001 BTC |
| `amount_from_signal: false` + signal `forceSize: true` | `size: 50` | Signal size overrides the fixed amount |
| `amount_from_signal: true` | `size: 50` on an open | 50 in quote currency |
| `amount_from_signal: true` | `size: 0.002` on a close | 0.002 in base currency |
| `amount_from_signal: true` | omitted | Falls back to the bot's configured `amount` (set one as a fallback even in signal mode) |

Amounts must be at or above the exchange's minimum notional for the pair, or
the exchange rejects the order. Sigrex documents no leverage or margin-mode
setting for futures bots; check how the exchange account is configured
(leverage, margin mode, position mode) before going live.

## How Signals Map To Orders

- `BUY`: opens a long, or closes a short.
- `SELL`: closes a long, or opens a short. On **spot** it sells held base;
  spot accounts cannot short, so design spot strategies as `LONG`/`EXIT`.
- `dilution: true` stacks a same-direction entry; otherwise repeated entries
  don't stack.
- From strategies: `LONG` is sent as `BUY`, `SHORT` as `SELL`, and `EXIT` as
  the side that closes the current position. This is inferred from the
  payload semantics, so confirm it in the signal log during testing.
- Execution results reach `callback` URLs (see `sigrex-webhooks`) and the
  dashboard signal log.

## Lifecycle (prefix `/api/v2`)

```text
GET  /bot/signal/cex                 list           POST /bot/signal/cex             create
GET  /bot/signal/cex/{id}            get            PUT  /bot/signal/cex/{id}        update
DELETE /bot/signal/cex/{id}          delete         GET  /bot/signal/cex/total       count
PUT  /bot/signal/cex/{id}/status     {"status":"ACTIVE"|"INACTIVE"}   (402 = bot limit)
POST /bot/signal/cex/duplicate       {"id":"<bot-id>"}
GET|POST /bot/signal/cex/folder, GET /bot/signal/cex/folder/root, GET|PUT|DELETE /bot/signal/cex/folder/{id}
```

To run the same setup on another symbol: duplicate, then update `symbol`,
`pair_base`, `pair_quote` (and `amount` if needed).

## Test And Activate

1. `POST /api/exchange/test` passes, then create the connection.
2. Bot Webhook `ACTIVE`, bot `INACTIVE`.
3. Send `{"symbol":"<bot symbol>","side":"BUY","flag":"TEST"}` (plus `key`);
   check the signal log.
4. After explicit approval: activate the bot, send one minimum-size live
   entry, then the matching exit; confirm both on the exchange.
5. Only then connect or activate the upstream strategy.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Nothing in the signal log | Hook inactive, wrong hook URL, missing/wrong `key`, invalid JSON |
| Logged but no order | Bot inactive; `symbol` mismatch; `TEST` flag present; `delay` window dropped it |
| Exchange rejected order | Below minimum notional; insufficient balance; wrong product (spot key on futures bot); leverage/margin settings |
| Close order wrong size | Close `size` is base currency, not quote |
| `409` deleting a key | Bots still linked; list them and detach first |
| `402` on create/activate | Plan bot limit reached |

## Canonical Docs

- https://docs.sigrex.io/cex-signal-bot/exchange-api-key.md
- https://docs.sigrex.io/cex-signal-bot/creating-a-cex-signal-bot.md
- https://docs.sigrex.io/api-reference/reference/api-keys/exchange-api-keys.md
- https://docs.sigrex.io/api-reference/reference/signal-bots/cex-bot.md
- https://docs.sigrex.io/api-reference/reference/exchanges.md
