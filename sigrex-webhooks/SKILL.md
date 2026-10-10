---
name: sigrex-webhooks
description: Create, secure, test and send to Sigrex Bot Webhooks and Data Webhooks, and build valid signal payloads (symbol, side, size, dilution, forceSize, flag TEST/DEBUG/REVERSE, key, callback). Use when generating a TradingView or script payload, sending or testing a trading signal, choosing between a bot hook and a data hook, protecting a hook with a key, handling execution callbacks, or managing webhook status, sharing and deletion.
compatibility: Bundled scripts require Python 3.8+ (standard library only).
metadata:
  author: sigrex
  version: "2.0"
---

# Sigrex Webhooks

Sigrex has two webhook types. Pick by what should happen to the request.

| | **Bot Webhook** | **Data Webhook** |
| --- | --- | --- |
| Purpose | Deliver a trading signal to Signal Bots | Deliver arbitrary JSON to Reactions |
| URL | `https://hook.sigrex.io/bot/<hash>` | `https://hook.sigrex.io/data/<hash>` |
| Email | `<hash>@sigrex.io` also accepts signals | No |
| Body | The signal payload below | Any JSON object (no schema enforced) |
| Key protection | `"key": "<secret>"` **inside the JSON body** | `X-Key: <secret>` **HTTP header** |
| Consumers | Every Signal Bot attached to it | Every Code/LLM Reaction attached to it |
| Trades? | Yes, through its bots | Never by itself |
| Delete blocked (`409`) while | Bots or strategies use it | Reactions use it |

The `<hash>` is a UUID generated at creation. The URL, hash and key are
credentials: anyone holding them can trade through the attached bots.

## Bot Signal Payload (CEX and DEX bots)

```ts
{
  id?: string,                   // custom label for the signal / alert
  key?: string,                  // required when the webhook is key-protected
  symbol: string,                // REQUIRED, must equal the bot's symbol, e.g. "BTCUSDT"
  side: "BUY" | "SELL",          // REQUIRED, lowercase "buy"/"sell" also accepted
  size?: number,                 // open: quote currency, close: base currency
  forceSize?: boolean,           // let `size` override bots with a fixed amount
  dilution?: boolean,            // true: stack onto a same-direction position
  flag?: FlagType | FlagType[],  // "TEST" | "DEBUG" | "REVERSE"
  debug?: any,                   // free-form, ignored by bots, kept for logs
  callback?: string              // URL that receives the execution result (POST)
}
```

Field semantics:

- **`side`**: `BUY` opens a long or closes a short; `SELL` closes a long or
  opens a short. On spot markets there are no shorts, so `SELL` sells the base
  asset you hold.
- **`size`**: overrides the bot's configured amount only when the bot has
  `amount_from_signal: true`, or when `forceSize: true` is sent. Opening size
  is in quote currency (e.g. USDT), closing size in base currency (e.g. BTC).
  Without `size`, the bot uses its configured amount. Must respect the venue's
  minimum notional.
- **`dilution`**: `true` adds to an existing same-direction position. With
  `false`/omitted, a repeated same-direction signal does not stack (the
  prediction docs describe it as preventing consecutive entries).
- **`flag`**: `TEST` = test only, no real trade; `DEBUG` = debugging;
  `REVERSE` = interpret as a reverse trade (no further detail is published,
  so do not rely on `REVERSE` without testing). One string or an array.
- **`callback`**: Sigrex POSTs the result to this URL after processing.
- **`id`**: a label for dashboards and logs. It is not a documented
  deduplication key; do not rely on it to block duplicates.

Minimal, test, and full examples:

```json
{"symbol": "BTCUSDT", "side": "BUY"}
```

```json
{"key": "<webhook-key>", "symbol": "BTCUSDT", "side": "BUY", "flag": "TEST", "id": "smoke-test-1"}
```

```json
{
  "id": "breakout-long",
  "key": "<webhook-key>",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "size": 100,
  "dilution": false,
  "callback": "https://your-app.example/sigrex/result"
}
```

Prediction bots use a **different** payload (`slug`, `outcome`, no `symbol`,
no `flag`); see `sigrex-prediction-bots`.

Validate any payload before sending:

```bash
python3 scripts/validate_signal.py '{"symbol":"BTCUSDT","side":"BUY","flag":"TEST"}'
python3 scripts/validate_signal.py --file payload.json --expect-key
python3 scripts/validate_signal.py --prediction '{"slug":"market-slug","outcome":"Yes","side":"BUY"}'
```

## Execution Callback

When `callback` is set, Sigrex POSTs a JSON document like this:

```json
{
  "signal":   {"symbol": "BTCUSDC", "key": "<echoed>", "side": "BUY", "callback": "https://..."},
  "executor": {
    "type": "cex-signal-bot",
    "api": {"id": 86, "exchange": "hyperliquid", "service": "futures"},
    "bot": {"id": 193}
  },
  "result": {
    "status": "ok",
    "response": {"type": "order", "data": {"statuses": [{"filled": {"totalSz": "0.00025", "avgPx": "79550.0", "oid": 538410463312}}]}}
  }
}
```

- `signal` echoes the original payload **including `key`**: only point
  callbacks at endpoints you control, over HTTPS.
- `result.response` is the raw venue response; its shape differs per exchange.
- One webhook can feed several bots. Be ready for one callback per executing
  bot and key them by `executor.bot.id`.
- A Sigrex Data Webhook can serve as the callback target, so a Code Reaction
  can record fills (see `sigrex-strategy-flows`).

## Sending A Signal

HTTP (TradingView, scripts, servers):

```bash
curl -X POST "https://hook.sigrex.io/bot/<hash>" \
  -H "Content-Type: application/json" \
  -d '{"key":"<webhook-key>","symbol":"BTCUSDT","side":"BUY","flag":"TEST"}'
```

Other senders:

- **Email:** send the JSON payload to `<hash>@sigrex.io`. Sigrex detects
  valid signal payloads and triggers the bots; other emails (e.g.
  verification mails) are forwarded to the account's registered address.
- **MCP:** `send_bot_hook_order_message` with the hook `hash`, optional `key`
  and the payload; in this tool `flag` is an array (`["TEST"]`). It cannot
  send prediction payloads.
- **Strategies/Reactions:** `$.Strategy.action(...)` or the LLM tools send
  signals to the configured `webhook_id`; you do not build the payload.
- **Browser extension / dashboard Manual Signal:** see `sigrex-integrations`.
- **From code to another hook:** `$.Http.post(hookUrl, payload)` inside a Code
  Strategy (used to reach prediction bots).

## Data Webhook Request

```http
POST https://hook.sigrex.io/data/<hash>
Content-Type: application/json
X-Key: <data-webhook-key>

{"event": "price_alert", "symbol": "BTCUSDT", "price": 67250, "source": "my-scanner"}
```

JSON only (plain-text support is announced as "coming soon"). Requests
without the correct `X-Key` are rejected when protection is on. The body is
passed to Reactions as-is: `$.Request.data` (string) in Code Reactions,
`{{data}}` in LLM Reactions. Design details: `sigrex-reactions`.

## Create And Manage (REST, prefix `/api/v2`)

Create/update body for both hook types:

```json
{"name": "btc-alerts", "description": "TradingView BTCUSDT 1h alerts", "is_safe": true, "hash_key": "<long-random-secret>"}
```

- `name` (optional, max 255; auto-generated like `silent-rain-9283` if empty)
- `description` (optional, max 255): say which symbols and cadence it carries,
  especially before sharing.
- `is_safe: true` enables key protection; `hash_key` is the key value. (The
  field is `hash_key`, not `has_key`.)

```text
GET    /webhook/bot                       list            POST /webhook/bot           create
GET    /webhook/bot/{id}                  get             PUT  /webhook/bot/{id}      update
DELETE /webhook/bot/{id}                  delete (409 while bots/strategies use it)
PUT    /webhook/bot/{id}/status           {"status":"ACTIVE"|"INACTIVE"}
GET    /webhook/bot/bot/signal/{id}/cex?page=1&limit=50         bots attached (also /dex, /prediction)
GET    /webhook/bot/{id}/shares           POST /webhook/bot/share/{id} {"userId":"..."}
DELETE /webhook/bot/share/{id}            {"userId":"..."}
GET    /webhook/bot/shared | /shared/with/{userId} | /shared/by/{userId}

GET    /webhook/data                      POST /webhook/data
GET    /webhook/data/{id}                 PUT  /webhook/data/{id}
DELETE /webhook/data/{id}                 (409 while reactions use it)
PUT    /webhook/data/{id}/status
GET    /webhook/data/{id}/code-reactions?page=1&limit=50   GET /webhook/data/{id}/llm-reactions?page=1&limit=50
GET    /webhook/data/{id}/shares          POST/DELETE /webhook/data/share/{id} {"userId":"..."}
GET    /webhook/data/shared | /shared/with/{userId} | /shared/by/{userId}
```

Limits: `402` "Webhook limit reached" on create or activate. Setting the
status a hook already has returns `400`. The response schema is not
published: read the hash and key from the actual object returned by the
API/MCP (the official plugin refers to the key field as `secret`). If the
hash is not in the response, ask the user to copy the URL from the dashboard.

## Routing Rules That Matter

- One Bot Webhook can feed many bots (CEX, DEX and prediction). Each bot acts
  only on signals whose `symbol` matches its own, so a single hook can carry
  several symbols to several bots. Prove the mapping with a `TEST` signal.
- Multiple strategies may point at one Bot Webhook; keep their symbols
  distinct or they will drive the same bots.
- A shared Bot Webhook hides its URL/hash from the recipient; they only see
  name and description and can attach their own bots (copy-trading). See
  `sigrex-social`.
- A shared Data Webhook lets other users POST data; every attached Reaction
  processes it regardless of sender.

## Testing Sequence

1. Create the hook (and bots) `INACTIVE`; validate the payload with the script.
2. Activate the hook, keep bots inactive, send a `TEST` payload, and check the
   signal log in the dashboard (or the callback).
3. Activate one bot with the smallest valid size, send one `TEST` signal,
   then, after explicit user approval, a single small live signal.
4. Report the exact payload (key redacted), target hook name, attached bots
   and observed result.

## Gotchas

- Wrong place for the key: bot hooks want `key` in the body, data hooks want
  the `X-Key` header.
- `size` as a string, `dilution` as `"true"`, trailing spaces in `symbol`, or
  JSON with trailing commas (the docs' own "Simple" example has one) all
  break parsing or matching.
- TradingView's `{{strategy.order.contracts}}` is a base-currency quantity;
  Sigrex opening `size` is quote currency. See `sigrex-integrations`.

## Available Scripts

Run them from this skill's directory. Each prints JSON on stdout (add
`--format text` for a readable version), sends diagnostics to stderr, and
documents its options and exit codes in `--help`.

- **`scripts/validate_signal.py`**: checks a bot signal (or a prediction
  payload with `--prediction`) against the published schema and redacts
  `key`. Exit `0` valid, `1` invalid, `2` usage error.

## Canonical Docs

- https://docs.sigrex.io/getting-started/webhook.md
- https://docs.sigrex.io/getting-started/signal-payload-format.md
- https://docs.sigrex.io/reaction/data-webhook.md
- https://docs.sigrex.io/api-reference/reference/hooks/bot-hooks.md
- https://docs.sigrex.io/api-reference/reference/hooks/data-hooks.md
