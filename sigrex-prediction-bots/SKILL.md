---
name: sigrex-prediction-bots
description: Configure Sigrex Polymarket Prediction Signal Bots, prediction wallet credentials, fixed or signal-derived market slugs, and prediction webhook payloads. Use when working with Polymarket automation, outcomes, prediction keys, or prediction bot execution.
metadata:
  author: sigrex
  version: "1.0"
---

# Sigrex Prediction Signal Bots

This integration is documented as beta and currently supports Polymarket. It
uses a dedicated wallet signing key and can execute real trades. Use a
dedicated low-balance wallet, test with explicit small sizes, and require
confirmation before funding or activation.

## Wallet Setup

Connect the Polymarket account by providing its profile/funder address and a
wallet private key. USDC is sent to the profile/funder address. The docs state
the key cannot withdraw funds, but it can sign trading operations; do not reuse
a primary wallet.

Prediction key endpoints under `/api/v2`:

```text
GET/POST /api/prediction
POST /api/prediction/test
GET /api/prediction/bot/signal/{id}?page=&limit=
PUT /api/prediction/{id}/status
DELETE /api/prediction/{id}
```

Create fields are `exchangeId`, `funderAddress`, `walletPrivateKey`, and
optional `name`. The documented exchange ID is `15`. Treat `funderAddress` as
an address string; one test schema incorrectly labels it as a number.

## Bot Configuration

Create under `/api/v2/bot/signal/prediction`:

```json
{
  "name": "BTC prediction bot",
  "webhook_id": 123,
  "api_id": 456,
  "slug_from_signal": true,
  "amount_from_signal": true,
  "amount": 10,
  "delay": 10
}
```

Use either a fixed market URL/slug or `slug_from_signal`. Use either a fixed
USDC `amount` or `amount_from_signal`. The bot API also supports `folder_id`.

```text
GET/POST /bot/signal/prediction
GET/PUT/DELETE /bot/signal/prediction/{id}
GET /bot/signal/prediction/market/{slug}
GET /bot/signal/prediction/total
PUT /bot/signal/prediction/{id}/status
POST /bot/signal/prediction/duplicate
```

Fixed-slug mode requires an exact match. Signal-slug mode validates the
incoming slug before each order and may be slower. Preflight a market with
`GET /bot/signal/prediction/market/{slug}` before activation.

## Prediction Payload

Prediction payloads do not use the generic `symbol` field:

```json
{
  "key": "secret-if-protected",
  "slug": "market-slug",
  "outcome": "Yes",
  "side": "BUY",
  "size": 5,
  "dilution": false,
  "id": "test-001",
  "debug": {"source": "manual-test"}
}
```

Use `BUY` or `SELL`; verify outcome matching because case sensitivity is not
fully specified. `size` is the USDC amount when configured from the signal.
Do not assume `id` guarantees idempotency or deduplication.

## Safe Test Sequence

1. Create/test the prediction credential.
2. Confirm the profile/funder address and wallet chain.
3. Preflight the exact market slug and outcome.
4. Create an inactive bot with a fixed small USDC amount.
5. Send a protected test payload and inspect logs.
6. Confirm the market, outcome, side, and size with the user.
7. Activate only after explicit approval.

## Canonical Docs

- https://docs.sigrex.io/prediction-signal-bot-beta/connect-wallet.md
- https://docs.sigrex.io/prediction-signal-bot-beta/create-prediction-signal-bot.md
- https://docs.sigrex.io/prediction-signal-bot-beta/payload-format.md
- https://docs.sigrex.io/api-reference/reference/signal-bots/prediction-bot.md
- https://docs.sigrex.io/api-reference/reference/api-keys/prediction-api-keys.md
