---
name: sigrex-prediction-bots
description: Configure Sigrex Prediction Signal Bots (beta) for Polymarket and Outcome.xyz, including wallet connection with session keys, fixed-market vs slug-from-signal mode, USDC sizing, the prediction payload (slug, outcome, side, size; no symbol, no TEST flag), market preflight, and triggering prediction bots from Code Strategies via HTTP. Use for any Sigrex prediction-market, Polymarket or Outcome.xyz automation question.
compatibility: Bundled scripts require Python 3.8+ (standard library only).
metadata:
  author: sigrex
  version: "2.0"
---

# Sigrex Prediction Signal Bots (beta)

A Prediction Signal Bot listens to a Bot Webhook and places orders on a
prediction market outcome with the user's connected account. It is beta and
early-stage: it can **only be triggered by signals arriving at its Bot
Webhook**. Code Strategies, LLM Sessions and Reactions cannot drive it
natively through `$.Strategy.action` or the LLM trading tools. A Code Strategy
can still reach it by POSTing a prediction payload to the bot's webhook URL
with `$.Http.post` (pattern below).

## Markets

| Market | Type | `exchangeId` | Connection credential |
| --- | --- | --- | --- |
| Polymarket | PREDICTION | `15` | Profile (funder) address + wallet private key, used once to create a session key |
| Outcome.xyz | PREDICTION | `17` | A **Hyperliquid API wallet** private key (API wallets can trade, not withdraw) |

List with `GET /api/v2/exchange/prediction`.

## Connecting The Account

How Polymarket connections work:

- The user provides the **Profile Address** (`0x...`, the address funds are
  sent to; shown in their Polymarket account) and the **private key of the
  wallet that owns the account**.
- Sigrex uses the private key **once** to authorize a **session key**. The
  private key is **never stored**; only the encrypted session key is kept.
- The session key can place trades and manage positions but **cannot
  withdraw**. It is valid for **180 days**. After expiry, trading stops until
  the user reconnects.
- Only Polymarket **Deposit Wallets** are supported (all accounts created on
  or after 4 May 2026). Older Safe or Proxy wallet accounts are not supported
  yet.
- Funding: send USDC to the Profile Address and wait for confirmation.
- Recommend a dedicated wallet for automation.

API (prefix `/api/v2`):

```text
POST /api/prediction/test     {"exchangeId":15,"funderAddress":"0x...","walletPrivateKey":"<redacted>"}
POST /api/prediction          {"exchangeId":15,"name":"Polymarket main","funderAddress":"0x...","walletPrivateKey":"<redacted>"}
GET  /api/prediction          GET /api/prediction/bot/signal/{id}?page=1&limit=50
PUT  /api/prediction/{id}/status {"status":"ACTIVE"|"INACTIVE"}
DELETE /api/prediction/{id}   (409 while bots use it)
```

Send `funderAddress` as a string even though the published test schema
types it as a number. Never log, echo or store the private key; collect it
only through the dashboard or a secure channel, and prefer the user doing
this step in the dashboard themselves.

## Bot Configuration

```json
POST /api/v2/bot/signal/prediction
{
  "name": "BTC 100K - yes",
  "webhook_id": 101,
  "api_id": 303,
  "slug_from_signal": false,
  "url": "https://polymarket.com/event/<event-slug>/<market-slug>",
  "amount_from_signal": false,
  "amount": 5,
  "delay": 1
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `webhook_id` | yes | Bot Webhook that triggers the bot |
| `api_id` | yes | Your prediction connection ID |
| `slug_from_signal` | yes | `false`: trade only the market in `url`; `true`: take the market from each signal's `slug` (wildcard mode) |
| `url` | if `slug_from_signal` is false | Full market URL; Sigrex extracts the market slug (last path segment) |
| `amount_from_signal` | yes | `true`: use signal `size`; `false`: use `amount` |
| `amount` | if `amount_from_signal` is false | USDC per order; also the fallback when a signal has no `size` |
| `delay` | no | Frequency limit ("1 in every 1 second" in the UI); extra signals inside the window are dropped, which helps against duplicates |
| `name`, `folder_id` | no | Name defaults from the webhook |

Fixed mode (recommended for a single market) requires the signal `slug` to
equal the bot's slug **exactly**, or the signal is ignored. Wildcard mode
verifies the slug before every order and is slightly slower.

Lifecycle:

```text
GET/POST /bot/signal/prediction            GET/PUT/DELETE /bot/signal/prediction/{id}
GET  /bot/signal/prediction/total          PUT /bot/signal/prediction/{id}/status
POST /bot/signal/prediction/duplicate {"id":"<bot-id>"}
GET  /bot/signal/prediction/market/{exchange}/{slug}    market preflight
GET|POST /bot/signal/prediction/folder, /folder/root, GET|PUT|DELETE /folder/{id}
```

Preflight every market with `/market/{exchange}/{slug}` and check the
outcome names before activation. The docs do not say whether `{exchange}` is
the numeric ID (`15`) or a name; try the ID and read the error if it fails.

## Prediction Payload

```ts
{
  id?: string,          // tracking label
  key?: string,         // required if the webhook is key-protected
  slug: string,         // REQUIRED market slug, e.g. "elon-musk-of-tweets-april-2026-840-879"
  outcome: string,      // REQUIRED, must match a market outcome exactly, e.g. "Yes" / "No"
  side: "BUY" | "SELL", // BUY opens/increases, SELL closes/reduces
  size?: number,        // USDC, overrides the bot amount (when allowed)
  forceSize?: boolean,  // bypass a strict fixed amount
  dilution?: boolean,   // true: allow consecutive BUYs (stacking); false: one entry until a SELL
  debug?: any,          // metadata, not used for execution
  callback?: string     // receives the execution result (POST)
}
```

Differences from CEX/DEX payloads:

- **No `symbol`**: the market is the `slug` and the side of the bet is the
  `outcome`.
- **No `flag` field**, so **no documented `TEST` mode**. Testing means a
  real order: use the minimum size, a fixed `amount`, and explicit user
  approval.
- `outcome` matching may be case-sensitive depending on the market; copy the
  exact outcome label.
- The slug is the last segment of the market URL. For
  `https://polymarket.com/event/elon-musk-of-tweets-april-2026/elon-musk-of-tweets-april-2026-840-879`
  it is `elon-musk-of-tweets-april-2026-840-879`.

```bash
python3 scripts/validate_signal.py --prediction \
  '{"slug":"elon-musk-of-tweets-april-2026-840-879","outcome":"Yes","side":"BUY","size":5}'
```

## Driving A Prediction Bot From A Code Strategy

The bot cannot receive `$.Strategy.action`, so POST to its webhook. Keep the
hook URL and key in `$.Env`:

```js
const S = (await $.Storage.get()) || { sent: 0 };
const yesOdds = Number(S.modelProbability || 0);

if (yesOdds >= 0.7 && !S.entered) {
  const res = await $.Http.post($.Env.PRED_HOOK_URL, {
    key: $.Env.PRED_HOOK_KEY,
    slug: $.Env.PRED_SLUG,
    outcome: "Yes",
    side: "BUY",
    size: 5,
    id: "relay-" + Date.now()
  });
  S.entered = res.status >= 200 && res.status < 300;
  S.lastStatus = res.status;
  S.sent += 1;
}

await $.Storage.set(S);
```

This strategy does not need `send_signal`; create it without a `webhook_id`.
Track entered/exited state in storage because `lastTrigger` is not updated by
raw HTTP posts.

## Safe Test Sequence

1. User connects the account in the dashboard; confirm the connection
   tests successfully and note the session-key expiry date (180 days).
2. Preflight the market slug and outcome names.
3. Create the bot `INACTIVE` with fixed `url` and a small fixed `amount`.
4. With approval: activate, send one minimum-size BUY, verify on the
   market, then the matching SELL.
5. Monitor logs; reconnect before the session key expires.

## Available Scripts

Run them from this skill's directory. Each prints JSON on stdout (add
`--format text` for a readable version), sends diagnostics to stderr, and
documents its options and exit codes in `--help`.

- **`scripts/validate_signal.py`**: checks a bot signal (or a prediction
  payload with `--prediction`) against the published schema and redacts
  `key`. Exit `0` valid, `1` invalid, `2` usage error.

## Canonical Docs

- https://docs.sigrex.io/prediction-signal-bot-beta/connect-wallet.md
- https://docs.sigrex.io/prediction-signal-bot-beta/create-prediction-signal-bot.md
- https://docs.sigrex.io/prediction-signal-bot-beta/payload-format.md
- https://docs.sigrex.io/api-reference/reference/signal-bots/prediction-bot.md
- https://docs.sigrex.io/api-reference/reference/api-keys/prediction-api-keys.md
