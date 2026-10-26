---
name: sigrex-code-strategies
description: Write, validate, deploy and debug Sigrex Code Strategies and Code Reactions, the sandboxed JavaScript that runs on Sigrex and emits LONG/SHORT/EXIT signals. Covers the execution model (one action per run, one position per strategy, no double EXIT), API config fields (send_signal, webhook_id, symbol, use_price), the $ runtime ($.Strategy, $.Storage, $.Http, $.Env, $.Ta, $.getExchangeRate, $.Request), limits, the forbidden-identifier list that silently breaks code (close, alert, top, self, fetch, console...), the code rules checked on save (declared variables, bounded loops, read-only built-ins, size limits), a sandbox lint script, and tested templates. Use whenever creating or changing Sigrex strategy or reaction code.
compatibility: Bundled scripts require Python 3.8+ (standard library only).
metadata:
  author: sigrex
  version: "2.1"
---

# Sigrex Code Strategies And Code Reactions

| | Code Strategy | Code Reaction |
| --- | --- | --- |
| Runs | On its own, driven by the platform (docs: "on market ticks"; the exact cadence is not published and there is no interval field) | Once per request received by its Data Webhook |
| Extra input | - | `$.Request.data` (raw body string), `$.Request.headers`, `$.Request.ip` |
| API route | `/api/v2/strategy/code` | `/api/v2/strategy/reaction/code` |
| Required on create | `code` | `data_webhook_id`, `code` |

Both share the same sandbox, `$` runtime, limits and forbidden identifiers.

## Execution Model (read before writing code)

- The code is the **body of an async function**: top-level `await` and
  top-level `return` work.
- **At most one `$.Strategy.action(...)` per run.** Make branches mutually
  exclusive.
- **One position per strategy.** `$.Strategy.lastTrigger.action` is the last
  action sent (`LONG`, `SHORT`, `EXIT`, or empty when none). `LONG`/`SHORT`
  mean a position is open; open the opposite side only after an `EXIT`. A
  long-to-short flip therefore takes **two runs**.
- **Two consecutive `EXIT`s are rejected.** Only exit when a position is open.
- **Every action goes to every signal symbol.** `ActionOption` has no symbol
  field; an action is sent for each symbol in the strategy's `symbol` list to
  its Bot Webhook. Use one strategy per independently traded symbol
  (duplicate and change the symbol).
- `LONG` reaches bots as `BUY`, `SHORT` as `SELL`, `EXIT` as the side that
  closes the position (inferred; confirm in the signal log). Spot bots cannot
  short, so spot strategies use `LONG`/`EXIT` only.
- `$.Strategy.action`, `$.Strategy.signalSymbols` and `$.Strategy.lastTrigger`
  exist only when `send_signal` is enabled. Without it the strategy is a
  plain runtime (monitoring, HTTP relays, managing other resources).
- There is no `console`. Put debug values into storage.
- Breaking a limit or using a forbidden identifier can **suspend** the
  strategy temporarily.

## Configuration Fields

Code Strategy (`POST /api/v2/strategy/code`, same body for `PUT /{id}`):

| Field | Required | Notes |
| --- | --- | --- |
| `code` | yes | JavaScript source |
| `name`, `folder_id` | no | Folder also scopes `$.Env` variables |
| `send_signal` | no | `true` enables `$.Strategy.action` and signal fields |
| `webhook_id` | if `send_signal` | Bot Webhook that receives the signals |
| `symbol` | if `send_signal` | Signal symbol(s), comma separated: `"BTCUSDT"` or `"BTCUSDT,ETHUSDT"`; must equal the bot symbol(s) |
| `use_price` | no | `true` injects `$.Price` (deprecated) and gives `roi()` a current price |
| `exchange_id` | if `use_price` | Catalog exchange with `hasExchangeRate: true` |
| `price_symbol` | if `use_price` | Symbol for `$.Price`, e.g. `BTCUSDT` |

Code Reaction (`POST /api/v2/strategy/reaction/code`): the same fields plus
`data_webhook_id` (required) and `delay` (frequency limit, "10 means 10 in 1
second").

Other routes (prefix `/api/v2/strategy/code`, same under
`/strategy/reaction/code`):

```text
GET /                  GET /{id} (includes storage)     GET /total
PUT /{id}/status       {"status":"ACTIVE"|"INACTIVE"}
POST /duplicate        {"id":"<id>"}
PUT /{id}/reset        {"resetTriggers":bool,"resetStore":bool}   (both keys required)
DELETE /{id}/store     wipe storage
PUT /{id}/public       {"isPublic":bool}
GET|POST /folder, GET /folder/root, GET|PUT|DELETE /folder/{id}
```

Resetting triggers makes the strategy believe it is flat while the exchange
may still hold the position. Resetting the store erases entry prices and
state. Ask before either.

Environment variables (`$.Env`) are set in the dashboard at **global** or
**folder** scope; folder values override global ones with the same name.
There is no published API for them, so ask the user to create the variables
your code reads, and list their names.

## Runtime Summary

Full reference: `references/runtime-api.md`.

| API | Purpose |
| --- | --- |
| `$.Action.LONG / SHORT / EXIT` | Action enum |
| `await $.Strategy.action(type, {id?, size?, dilution?, forceSize?})` | Send one signal |
| `$.Strategy.lastTrigger.{action, price, at}` | Last action, its price, its time (`at` is `null` if none) |
| `$.Strategy.signalSymbols`, `$.Strategy.id`, `$.Strategy.type` | Context (`type`: `code-strategy` or `code-reaction`) |
| `$.Strategy.roi(pct?, open?, current?)` | ROI vs last trigger price; pass prices explicitly when `use_price` is off. Negative for a profitable short |
| `await $.Strategy.stop(notify?)` | Set self `INACTIVE` for future runs; follow with `return` |
| `await $.Storage.get()` / `set(obj)` | Persistent JSON, 24 KB (`$.Storage.byteLimit` = 24576); `get()` is `null` when empty; `set` overwrites |
| `await $.getExchangeRate($.Exchange.BINANCE, "btcusdt")` | Live price or `null`; exchanges: `BINANCE`, `GATEIO`, `BITGET`, `HYPERLIQUID`, `KRAKEN` |
| `$.Price.{symbol, price, exchange, service}` | Deprecated; only with `use_price` |
| `$.Env.NAME` | User environment variables (strings) |
| `await $.Http.get(url, params?, headers?)` (+ `post`, `put`, `delete`) | Returns `{status, text, cache}`; 1750 ms timeout; 5 s cache; POST/PUT default to JSON |
| `await $.Http.generateSignature(payload, secret, "HMAC"\|"ML-DSA")` | Sign requests (e.g. Sigrex API) |
| `$.Http.createApiClient({apiKey, apiSecret})` | Official Sigrex API client inside the sandbox |
| `$.Ta` | `trading-signals` indicators: `new $.Ta.RSI(14)`, `.update(v)`, `.isStable`, `.getResult()` |
| `$.Request.{data, headers, ip}` | Code Reactions only |

## Limits

| Limit | Value |
| --- | --- |
| Execution time per run | 5000 ms |
| Each HTTP request | 1750 ms timeout |
| HTTP cache | 5 s per identical request (`response.cache` tells you) |
| Storage | 24 KB JSON |
| Actions | 1 per run, 5 per second globally |
| Consecutive `EXIT` | not allowed |

Budget the 5 s: at most two or three sequential HTTP calls per run.

## Forbidden Identifiers

These words must not appear **anywhere** in the source: not as variables,
properties, function names, destructured names, aliases, **or in comments**.
Treat string literals the same way. Matching rules are not published, so
also avoid case variants and camelCase prefixes (`Close`, `closePrice`).

```text
Networking:  fetch WebSocket EventSource Worker SharedWorker XMLHttpRequest navigator
             location postMessage onmessage onmessageerror MessageChannel
             BroadcastChannel import importScripts close
Dynamic:     eval Function AsyncFunction generatorFunction constructor
Globals:     globalThis window self frames parent top document
Timers:      setTimeout setInterval setImmediate clearTimeout clearInterval
             clearImmediate queueMicrotask
Crypto/perf: crypto performance structuredClone Atomics SharedArrayBuffer
Reflection:  Reflect Proxy
Node/Deno:   process require module exports export global Deno
Encoding:    atob btoa
Interaction: alert confirm prompt console Intl FinalizationRegistry WeakRef
```

Everyday trading words that trip this list, with safe replacements:

| Avoid | Use instead |
| --- | --- |
| `close`, `closePrice`, `candle.close` | `lastPx`, `exitPx`, kline index `[4]` |
| `alert` (e.g. "price alert") | `notice`, `trigger`, `signalMsg` |
| `top`, `self`, `parent` | `highest`, `own`, `root` |
| `prompt`, `confirm` | `instruction`, `approve` |
| `global`, `module`, `process`, `location` | `shared`, `part`, `handle`, `venue` |
| `crypto`, `performance` | `coin`, `pnl` |
| `class X { constructor() {} }` | plain objects and arrow functions |
| `console.log(x)` | `S.dbg = x` then `await $.Storage.set(S)` |
| `fetch(url)` | `await $.Http.get(url)` |

Indicators that take OHLC objects (e.g. ATR) expect a `close` property; build
those values from arrays or compute the indicator by hand.

**Always lint before uploading:**

```bash
python3 scripts/check_sandbox.py strategy.js
```

It exits `1` on any forbidden identifier or broken code rule it can detect,
and warns about case variants, undeclared variables, `this` outside a class,
multiple actions, missing `await`, and `$.Price`.

## Code Rules (checked on save)

On create and update the API also checks how the code is written and answers
`400` with the reason when a rule is broken. Write code that already follows
them:

| Rule | Write this instead |
| --- | --- |
| Plain JavaScript, at most 100,000 characters | No TypeScript types, no `import` / `export` |
| Declare every variable | `let total = 0`, not `total = 0` |
| Built-ins (`Math`, `Object`, `JSON`, `Array`...) and `$.Ta` are read-only | Keep helpers in your own objects: `const fmt = { pct: (x) => x.toFixed(2) }`, never `Math.pct = ...` |
| Every loop must end by its own condition | `for (let i = 0; i < prices.length; i++)`, not `while (true) { ... break; }` or `for (;;)` |
| Loop bounds up to 10,000,000 | `i < 1e12` is rejected |
| Sizes up to 1,000,000 | Applies to `new Array(n)`, typed arrays, `Array.from({ length: n })`, `.repeat(n)`, `.padStart(n)`, `.padEnd(n)` |
| Regular expressions as literals, without nested quantifiers | `/btc/i`, not `new RegExp(text)` or `/(a+)+/` |
| `this` only inside class methods | Plain objects and functions |
| No prototype access | `Object.hasOwn(obj, key)`, not `Object.prototype.hasOwnProperty.call(obj, key)` |
| No `arguments`, `with` or `debugger` | Rest parameters: `(...args) => args.length` |

The lint script below catches most of these before you upload.

## Skeleton (copy this)

```js
// Tunables come from $.Env (set in the dashboard, account-wide or per folder).
const PAIR = ($.Env.PAIR || "BTCUSDT").toUpperCase();
const TP_PCT = Number($.Env.TP_PCT || 1.0);
const SL_PCT = Number($.Env.SL_PCT || 1.0);

// Load state once, save once at the end (also on early exits).
const S = (await $.Storage.get()) || { entry: null, runs: 0 };
S.runs += 1;
const save = async () => { await $.Storage.set(S); };

// Derive the position from the platform, not from storage alone.
const lastAction = $.Strategy.lastTrigger ? $.Strategy.lastTrigger.action : null;
const isLong = lastAction === $.Action.LONG;
const isShort = lastAction === $.Action.SHORT;
const isFlat = !isLong && !isShort;

const px = await $.getExchangeRate($.Exchange.BINANCE, PAIR.toLowerCase());
if (px === null) { S.dbg = { at: Date.now(), err: "no price" }; await save(); return; }

let action = null;
let reason = "";
if (isFlat && /* entry condition */ false) {
  action = $.Action.LONG; reason = "entry";
} else if (isLong && S.entry) {
  const movePct = ((px - S.entry) / S.entry) * 100;
  if (movePct >= TP_PCT) { action = $.Action.EXIT; reason = "take-profit"; }
  else if (movePct <= -SL_PCT) { action = $.Action.EXIT; reason = "stop-loss"; }
}

if (action) {
  const result = await $.Strategy.action(action, { id: reason });
  S.lastAction = { action, reason, px, at: Date.now(), result: JSON.stringify(result || null).slice(0, 200) };
  S.entry = action === $.Action.EXIT ? null : px;
}

await save();
```

More complete, lint-clean strategies (threshold TP/SL, RSI on candles, EMA
crossover with two-step flips, validated Code Reaction, prediction relay,
self-stopping guard, managing other strategies with the API client):
`references/examples.md`.

## Patterns

- **Load once, save once.** One `get()` at the top, one `set()` at the end.
  `set()` overwrites everything, so never write a partial object.
- **Gate on new candles.** When the platform runs faster than your timeframe,
  store the last processed candle time and `return` early on the same candle.
- **Keep storage small.** Trim arrays (`.slice(-50)`); the limit is 24 KB.
- **Parse defensively.** Check `res.status === 200`, wrap `JSON.parse` in
  `try/catch`, and treat any external field as untrusted.
- **Record why.** Store `{action, reason, px, at}` so a later debugging
  session can explain each signal.
- **Secrets in `$.Env` only.** Never hardcode keys, hook URLs or hook keys.
- **Fail closed.** Missing price, failed request or invalid input means no
  action.

## Deploy And Test Workflow

1. Write the code; run `scripts/check_sandbox.py`.
2. Create the strategy via MCP (`post_strategy_code`) or REST; the API
   validates code on create/update and returns `400` with the reason
   (forbidden identifier or code rule) for invalid code.
3. Confirm Bot Webhook, bot symbol and signal `symbol` are identical; keep
   bots `INACTIVE` or rely on `TEST` signals while observing.
4. Activate the strategy (approval required), watch storage and signal logs
   for a few runs, then activate the bot after a second approval.
5. To change live code: update with the full new `code`; status is kept.
   Report the diff. Do not reset storage unless asked.

## Debugging A Silent Strategy

1. `GET /strategy/code/{id}`: status `ACTIVE`? `send_signal` true? webhook
   and symbol set? last run time moving?
2. Read storage: your `S.dbg` / `S.lastAction` fields.
3. Run the lint script on the live code (a forbidden word in a new comment
   is a common cause of suspension).
4. Evaluate each entry condition against current data and name the one
   blocking entries.
5. Check the downstream chain: webhook `ACTIVE`, bot `ACTIVE`, symbol match,
   exchange key valid (`sigrex-strategy-flows` troubleshooting).

## Available Scripts

Run them from this skill's directory. Each prints JSON on stdout (add
`--format text` for a readable version), sends diagnostics to stderr, and
documents its options and exit codes in `--help`.

- **`scripts/check_sandbox.py`**: lints Code Strategy / Code Reaction source
  for forbidden sandbox identifiers and the code rules (loops, built-ins,
  sizes, regular expressions...), case variants, extra actions, missing
  `await` and `$.Price`. Exit `0` clean, `1` forbidden identifier or broken
  rule found, `2` usage error.

## Canonical Docs

- https://docs.sigrex.io/strategies/code.md
- https://docs.sigrex.io/reaction/code-reaction.md
- https://docs.sigrex.io/api-reference/reference/strategies/code-strategies.md
- https://docs.sigrex.io/api-reference/reference/strategies/reactions/code-reaction.md
- https://github.com/bennycode/trading-signals (library behind `$.Ta`)
