---
name: sigrex-webhooks
description: Create, configure, secure, and test Sigrex bot and data webhooks and their JSON signal payloads. Use when working with Sigrex webhooks, TradingView alerts, bot hooks, data hooks, signal payloads, or webhook sharing.
metadata:
  author: sigrex
  version: "1.0"
---

# Sigrex Webhooks

Use this skill for webhook design and payload generation. Do not send a live
request or create a live trading connection without explicit user approval.

## Choose The Hook

- Use a **Bot Webhook** when an incoming signal should reach attached Signal
  Bots and potentially execute a trade.
- Use a **Data Webhook** when incoming JSON should be stored and passed to
  Code or LLM Reactions. A Data Webhook does not trade by itself.
- Use a **Bot Webhook** for CEX, DEX, or Prediction Signal Bots. The webhook
  URL can also receive signals by email at `<webhook-hash>@sigrex.io`.

## Bot Signal Payload

Build the smallest valid payload first:

```json
{
  "symbol": "BTCUSDT",
  "side": "BUY"
}
```

Supported fields are `id`, `key`, `symbol`, `side`, `size`, `forceSize`,
`dilution`, `flag`, and `debug`. `side` is `BUY` or `SELL`; `size` means quote
currency when opening and base currency when closing. Use `TEST` in `flag` for
non-live verification when appropriate.

Prediction Bot payloads are different. Use `slug`, `outcome`, `side`, and
optional `size`, `dilution`, `id`, `key`, and `debug`; do not substitute the
generic `symbol` field.

When key protection is enabled, include the exact configured `key` in the bot
payload. For a Data Webhook, send JSON with `Content-Type: application/json`
and use `X-Key: <secret>` when key protection is enabled.

## Workflow

1. Identify the hook type, target symbol, side, and whether the request is a
   test or live action.
2. Validate required fields and casing against the payload format.
3. Confirm the user intends to create, activate, share, or send to a live hook.
4. Prefer a `TEST` signal or an inactive hook for verification.
5. Report the exact request body and endpoint without exposing secrets.

## Management API Shape

The signed API uses `https://api.sigrex.io/api/v2`:

```text
GET/POST   /webhook/bot
GET/PUT/DELETE /webhook/bot/{id}
PUT        /webhook/bot/{id}/status       {"status":"ACTIVE|INACTIVE"}
GET        /webhook/bot/{id}/shares
POST       /webhook/bot/share/{id}        {"userId":"..."}
DELETE     /webhook/bot/share/{id}

GET/POST   /webhook/data
GET/PUT/DELETE /webhook/data/{id}
PUT        /webhook/data/{id}/status      {"status":"ACTIVE|INACTIVE"}
GET        /webhook/data/{id}/shares
GET        /webhook/data/{id}/llm-reactions?page=&limit=
GET        /webhook/data/{id}/code-reactions?page=&limit=
POST       /webhook/data/share/{id}       {"userId":"..."}
DELETE     /webhook/data/share/{id}
```

Create/update hook fields are `name`, `description`, `is_safe`, and `has_key`.
Sharing requires friendship. A delete may return `409` while dependencies
still exist; inspect attached bots, strategies, and reactions first. Plan or
webhook quotas may return `402`.

## Security And Gotchas

- Treat webhook URLs, hashes, and keys as credentials. Never commit or echo
  them in logs.
- A shared webhook keeps its actual URL/hash private from the recipient.
- Deletion can fail with `409` when the hook is still used by bots, strategies,
  or reactions; inspect dependencies before retrying.
- Sigrex documents both uppercase and lowercase side values in prose, but use
  uppercase `BUY`/`SELL` in generated examples for consistency.

## Canonical Docs

- https://docs.sigrex.io/getting-started/webhook.md
- https://docs.sigrex.io/getting-started/signal-payload-format.md
- https://docs.sigrex.io/reaction/data-webhook.md
- https://docs.sigrex.io/api-reference/reference/hooks/bot-hooks.md
- https://docs.sigrex.io/api-reference/reference/hooks/data-hooks.md
- https://docs.sigrex.io/api-reference/reference/signal-bots/prediction-bot.md
