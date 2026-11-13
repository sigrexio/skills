---
name: sigrex-prediction-bots
description: Configure Sigrex Prediction Signal Bots (beta) for Polymarket, Outcome.xyz and Kalshi, including account connection (Polymarket session keys, Outcome.xyz API wallets, Kalshi API keys), fixed-market vs slug-from-signal mode, picking one market of an event, sizing (buys in USDC, sells close the position), the prediction payload (slug, outcome, side, size; no symbol, no TEST flag), market preflight, and triggering prediction bots from Code Strategies via HTTP. Use for any Sigrex prediction-market, Polymarket, Outcome.xyz or Kalshi automation question.
compatibility: Bundled scripts require Python 3.8+ (standard library only).
metadata:
  author: sigrex
  version: "2.1"
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
| Outcome.xyz | PREDICTION | `17` | Main Hyperliquid wallet address + a **Hyperliquid API wallet** private key (API wallets can trade, not withdraw) |
| Kalshi | PREDICTION | see `GET /api/v2/exchange/prediction` | A **Kalshi API key**: API key ID + private key (PEM, RSA or Ed25519), read and trade scopes |

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

Outcome.xyz connections use the user's **main Hyperliquid wallet address**
(not the API wallet's address) and the private key of a **Hyperliquid API
wallet**. The API wallet key is stored encrypted; it can trade but not
withdraw. Trades use the main wallet's balance.

Kalshi connections need no wallet: the user creates an API key on Kalshi
(Account & security → API keys) with the read and trade scopes only, and
enters the **API Key ID** and the **private key** (PEM) Kalshi shows once at
creation. The private key is stored encrypted because every Kalshi request is
signed with it. Kalshi needs a verified Kalshi account and is not available in
every country. The connection list shows the API key ID in `funderAddress`.

API (prefix `/api/v2`):

```text
POST /api/prediction/test     {"exchangeId":15,"funderAddress":"0x...","walletPrivateKey":"<redacted>"}
POST /api/prediction          {"exchangeId":15,"name":"Polymarket main","funderAddress":"0x...","walletPrivateKey":"<redacted>"}
POST /api/prediction          {"exchangeId":<kalshi id>,"name":"Kalshi main","publicKey":"<api key id>","privateKey":"<redacted PEM>"}
GET  /api/prediction          GET /api/prediction/bot/signal/{id}?page=1&limit=50
PUT  /api/prediction/{id}/status {"status":"ACTIVE"|"INACTIVE"}
DELETE /api/prediction/{id}   (409 while bots use it)
```

Polymarket and Outcome.xyz send `funderAddress` + `walletPrivateKey`; Kalshi
sends `publicKey` (API key ID) + `privateKey` (PEM) instead. Send
`funderAddress` as a string. Never log, echo or store a private key; collect
it only through the dashboard or a secure channel, and prefer the user doing
this step in the dashboard themselves. The two `POST` routes are REST only;
over MCP, the user connects the account in the dashboard under
**API connection** → **Prediction Market**.

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
| `url` | if `slug_from_signal` is false | Market URL. An event URL with several markets must point to one of them (see below) |
| `amount_from_signal` | yes | `true`: use the signal `size` (signals without `size` are ignored); `false`: use `amount` |
| `amount` | if `amount_from_signal` is false | Buy size per order in USDC (USD on Kalshi). Not used by sells |
| `delay` | no | Frequency limit ("1 in every 1 second" in the UI); extra signals inside the window are dropped, which helps against duplicates |
| `name`, `folder_id` | no | Without a name the bot is shown by its market slug; slug-from-signal bots get a generated name |

Picking the market of an event:

- **Polymarket:** `https://polymarket.com/event/<event-slug>/<market-slug>`.
  An event URL with only one market resolves to that market.
- **Kalshi:** the event URL plus `?market=<TICKER>`, e.g.
  `https://kalshi.com/markets/kxnato/next-nato-secretary/kxnato-99?market=KXNATO-99-KKAL`.
- **Outcome.xyz:** the event URL plus `?outcome=<market id>`, e.g.
  `https://outcome.xyz/markets/sports/q199?outcome=1481`. Events with one
  market (e.g. `o30154`) need no parameter.

An event URL that still has several markets is rejected ("Select one market
of the ... event"). Bots cannot be created or edited on closed or settled
markets.

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

Preflight every market with `/market/{exchange}/{slug}` before activation.
`{exchange}` is the name: `polymarket`, `outcome` or `kalshi`. `{slug}` is a
Polymarket market or event slug, a Kalshi market or event ticker, or an
Outcome.xyz event id (`q199`, `o30154`) or market id (`1481`). An event with
several markets comes back with its `markets` to choose from and no single
market chosen; check the outcome names of the chosen market.

## Prediction Payload

```ts
{
  id?: string,          // tracking label
  key?: string,         // required if the webhook is key-protected
  slug: string,         // REQUIRED, the bot's market slug (see table below)
  outcome: string,      // REQUIRED, must match one of the bot's outcomes exactly, e.g. "Yes" / "No"
  side: "BUY" | "SELL", // BUY buys the outcome, SELL closes the position (see Buying And Selling)
  size?: number,        // BUY: USDC (USD on Kalshi); SELL: shares. Used with amount_from_signal or forceSize
  forceSize?: boolean,  // use the signal size even when the bot has a fixed amount
  dilution?: boolean,   // true: allow consecutive BUYs (stacking); false: one entry until a SELL
  debug?: any,          // metadata, not used for execution
  callback?: string     // receives the execution result (POST)
}
```

| Market | `slug` to send |
| --- | --- |
| Polymarket | Market slug, the last segment of the market URL: for `https://polymarket.com/event/elon-musk-of-tweets-april-2026/elon-musk-of-tweets-april-2026-840-879` it is `elon-musk-of-tweets-april-2026-840-879` |
| Kalshi | Market ticker, e.g. `KXNATO-99-KKAL` |
| Outcome.xyz | Event id for single-market events (`o30154`); market id for events with several markets (`1481`, the `?outcome=` number) |

The bot detail page and `GET /bot/signal/prediction/{id}` show the bot's
`slug` and `outcomes`; copy them instead of guessing. Outcome names are not
always Yes / No (some Outcome.xyz markets use names like `IND` / `MIA`).

Differences from CEX/DEX payloads:

- **No `symbol`**: the market is the `slug` and the side of the bet is the
  `outcome`.
- **No `flag` field**, so **no documented `TEST` mode**. Testing means a
  real order: use the minimum size, a fixed `amount`, and explicit user
  approval.
- Copy the exact outcome label; matching is exact.

```bash
python3 scripts/validate_signal.py --prediction \
  '{"slug":"elon-musk-of-tweets-april-2026-840-879","outcome":"Yes","side":"BUY","size":5}'
```

## Buying And Selling

- **BUY** spends the bot `amount`, or the signal `size` when the bot takes
  the size from the signal (`amount_from_signal`) or the signal sets
  `forceSize`. On Polymarket and Kalshi a buy fills completely or not at all;
  if it cannot fill, the bot is suspended and the user is notified.
- **SELL** closes the **whole position** of the outcome. When the size comes
  from the signal (`amount_from_signal` or `forceSize`), it sells that many
  **shares** instead, capped at what is held. Nothing held: nothing happens.
- What a sell does not fill is retried at up to 5%, 15% and 30% below the
  best bid, never lower. Shares left unsold produce a **warning
  notification** and the bot **keeps running** (no suspension), so the next
  SELL tries again.
- With a `callback`, a sell that needed retries sends **one callback per
  order**.

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
raw HTTP posts. `size: 5` only applies when the bot takes the amount from the
signal (or with `forceSize: true`).

## Safe Test Sequence

1. User connects the account in the dashboard; confirm the connection
   tests successfully. On Polymarket, note the session-key expiry date
   (180 days).
2. Preflight the market and outcome names.
3. Create the bot `INACTIVE` with a fixed `url` (one market) and a small
   fixed `amount`.
4. With approval: activate, send one minimum-size BUY, verify on the
   market, then the matching SELL (it closes the whole position).
5. Monitor logs and notifications; on Polymarket reconnect before the session
   key expires.

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
