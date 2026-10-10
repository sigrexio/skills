# Sigrex `$` Runtime Reference

Everything a Code Strategy or Code Reaction can use. Source:
https://docs.sigrex.io/startegies/code.md, https://docs.sigrex.io/reaction/code-reaction.md
and the changelog. Code runs as the body of an async function in a strict
sandbox; nothing outside `$` and standard JavaScript built-ins (`Math`,
`JSON`, `Date`, `Number`, `String`, `Array`, `Object`, ...) is available,
and the forbidden identifiers listed in `SKILL.md` must not appear anywhere.

## `$.Action`

Enum of trade actions: `$.Action.LONG` (open long), `$.Action.SHORT` (open
short), `$.Action.EXIT` (close the current position). Compare against these
members, not against string literals.

## `$.Strategy`

Always available:

| Member | Description |
| --- | --- |
| `id` | Numeric ID of this strategy/reaction |
| `type` | `"code-strategy"` or `"code-reaction"` |
| `roi(percentage?: boolean, openPrice?: number, currentPrice?: number): number \| null` | ROI between open and current price. Defaults: open = last trigger price, current = system price (needs `use_price`). Returns a decimal, or a percentage when `percentage` is `true`; `null` without valid prices. Profitable shorts give a negative value. Example: `$.Strategy.roi(true, S.entry, px)` |
| `async stop(notify?: boolean): boolean` | Sets status `INACTIVE` so the code will not run again; `notify: true` emails the owner. The current run continues, so write `await $.Strategy.stop(true); return;` |

Only when `send_signal` is enabled:

| Member | Description |
| --- | --- |
| `signalSymbols` | Array of symbols that actions are sent to, e.g. `["BTCUSDT","ETHUSDT"]` |
| `lastTrigger.action` | Last action sent: `LONG`, `SHORT`, `EXIT` (empty/null before the first) |
| `lastTrigger.price` | Price when the last action executed |
| `lastTrigger.at` | Timestamp of the last action, or `null` |
| `async action(type: $.Action, options?: ActionOption)` | Sends the action to the Bot Webhook for every signal symbol and returns the execution result; returns an error for invalid options |

```ts
type ActionOption = {
  id?: string;         // label shown in logs
  dilution?: boolean;  // stack onto an existing same-direction position
  size?: number;       // open: quote currency, close: base currency
  forceSize?: boolean; // let size override bots with a fixed amount
}
```

Rules: one action per run; at most five actions per second across the
platform; never two `EXIT`s in a row; open the opposite side only after an
`EXIT`.

## `$.Storage`

Persistent JSON per strategy, kept between runs.

| Member | Description |
| --- | --- |
| `byteLimit` | `24576` (24 KB) |
| `async get()` | Stored object, or `null` when empty |
| `async set(obj)` | Replaces the whole stored object |

Wiped by `PUT /{id}/reset` with `resetStore: true` or `DELETE /{id}/store`.
The API `GET /{id}` returns the strategy with its storage, which is useful
for debugging.

## `$.Env`

Read-only map of user environment variables, defined in the dashboard at
global or folder scope (folder wins on name clashes). Values should be
treated as strings: convert with `Number(...)` and validate. Use it for
tunables, API keys, webhook URLs and keys.

## Prices

`$.getExchangeRate(exchange, symbol): Promise<number | null>`

```js
const px = await $.getExchangeRate($.Exchange.HYPERLIQUID, "btcusdc");
```

`$.Exchange` members: `BINANCE`, `GATEIO`, `BITGET`, `HYPERLIQUID`, `KRAKEN`.
Docs examples use lowercase symbols (`"btcusdt"`). Returns `null` when no
rate is available, so always check.

`$.Price` (deprecated, to be removed): only present when the strategy has
`use_price: true` with `exchange_id` and `price_symbol`. Properties: `symbol`
(e.g. `"BTCUSDT"`), `price`, `exchange` (e.g. `"binance"`), `service`
(`"spot"`/`"futures"`). Prefer `$.getExchangeRate`.

## `$.Http`

| Member | Description |
| --- | --- |
| `timeout` | `1750` (ms) per request |
| `async get(url, params?, headers?)` | GET; `params` object becomes the query string |
| `async post(url, data, headers?)` | POST; defaults to `Content-Type: application/json` |
| `async put(url, data, headers?)` | PUT; defaults to `Content-Type: application/json` |
| `async delete(url, params?, headers?)` | DELETE |
| `async generateSignature(payload, secret, algo?)` | HMAC (default) or `"ML-DSA"` signature string |
| `createApiClient({ apiKey, apiSecret })` | Official Sigrex API client instance (not async) |

Every method resolves to `{ status: number, text: string, cache: boolean }`.
`text` is the raw body, so `JSON.parse` it yourself inside `try/catch`.
Identical requests within 5 seconds return the cached response
(`cache: true`); add a changing query parameter only if freshness truly
matters and the API allows it.

```js
const res = await $.Http.get("https://data-api.binance.vision/api/v3/ticker/price", { symbol: "BTCUSDT" });
let data = null;
if (res.status === 200) {
  try { data = JSON.parse(res.text); } catch (e) { data = null; }
}
```

When sending objects with `post`/`put`, verify the received body once
against an endpoint you control (for example your own Data Webhook) before
pointing at a live hook.

### Sigrex API from inside a strategy

```js
const client = $.Http.createApiClient({
  apiKey: $.Env.SIGREX_API_KEY,
  apiSecret: $.Env.SIGREX_API_SECRET,
});
const exchanges = await client.exchanges.list({ enabled: true });
await client.strategies.code.status(Number($.Env.TARGET_STRATEGY_ID), { status: "INACTIVE" });
```

Client method map (the same client as `@sigrex/client`):

```text
client.exchanges.{list(query?), listCex(), getDex(chain), listPrediction(), listWithExchangeRate()}
client.apiKeys.{exchange,llm,prediction}.{list, create, delete, ...}
client.webhooks.bot.{list, create, get, update, delete, status, shares, deleteShare,
                     listShared, listBotSignalCex(id, {page, limit}), listBotSignalDex(...), ...}
client.webhooks.data.{list, create, get, update, delete, status, codeReactions(id, {page, limit}), ...}
client.bots.{cex,dex,prediction}.{list, create, get, update, delete, status, getTotal, ...}
client.strategies.code.{list, create, get, update, delete, status, duplicate, reset, store, ...}
client.strategies.llmSessions.{list, create, get, update, delete, status, duplicate, reset, ...}
client.strategies.reactions.{code,llm}.{list, create, get, update, delete, status, ...}
client.request({ method, path: "/api/v2/...", body })   // any route, signed for you
```

`status(id, body)` takes `{ status: "ACTIVE" | "INACTIVE" }`. The full route
and field reference is in the `sigrex-api-mcp` skill. A Sigrex API key has
full account access, so store it only in `$.Env` and keep these strategies
minimal. Each API call is an HTTP request inside the 5 s budget.

Manual signing (same contract as the REST API):

```js
const method = "GET";
const path = "/api/v2/strategy/code";
const ts = Math.floor(Date.now() / 1000).toString();
const signature = await $.Http.generateSignature(method + path + ts, $.Env.SIGREX_API_SECRET);
const res = await $.Http.get("https://api.sigrex.io" + path, {}, {
  "api-key": $.Env.SIGREX_API_KEY, "timestamp": ts, "signature": signature,
});
```

## `$.Ta`

The `trading-signals` library (https://github.com/bennycode/trading-signals).
Sigrex documents this usage:

```js
const rsi = new $.Ta.RSI(14);
for (const v of series) rsi.update(v);
if (rsi.isStable) {
  const value = Number(rsi.getResult());
}
```

- Feed values oldest to newest with `update(value)`; read with `getResult()`
  only once `isStable` is true.
- Wrap results in `Number(...)`: older library versions return Big.js objects.
- Common classes: `RSI`, `SMA`, `EMA`, `MACD`, `ATR`, Bollinger Bands, and
  many more. The bundled library version is not published, so verify class
  names and option shapes in an inactive strategy before relying on less
  common indicators.
- Indicators fed with candle objects need a `close` property, which is a
  forbidden identifier. Prefer single-value indicators, or compute the value
  yourself.
- No historical data is built in. Get candles with `$.Http.get`, e.g.
  `https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=200`
  (each row: `[openTime, open, high, low, lastTradePrice, volume, ...]`;
  index `4` is the candle's final price; drop the last, still-forming row).

## `$.Request` (Code Reactions only)

| Member | Description |
| --- | --- |
| `$.Request.data` | Full request body as a string |
| `$.Request.headers` | All incoming HTTP headers |
| `$.Request.ip` | Sender IP, if available |

```js
let payload = null;
try { payload = JSON.parse($.Request.data); } catch (e) { return; }
```

The Data Webhook enforces no schema. Validate every field, and remember that
anyone with the URL (and key), including friends on a shared hook, can send
data.
