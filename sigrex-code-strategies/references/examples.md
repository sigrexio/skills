# Sigrex Code Strategy Examples

Complete strategies that pass `scripts/check_sandbox.py`. Each lists the
strategy settings and the `$.Env` variables the user must create. They are
starting points, not trading advice: Sigrex has no backtesting, so start
inactive, use `TEST` signals, then the smallest live size.

Every example follows the same contract:

- one `$.Strategy.action` per run, chosen by mutually exclusive branches
- position derived from `$.Strategy.lastTrigger.action`
- state loaded once and saved once
- fail closed on missing data

## 1. Price Threshold With Take-Profit / Stop-Loss (spot long)

Settings: `send_signal: true`, `webhook_id`, `symbol: "BTCUSDT"`.
Env: `PAIR` (`btcusdt`), `BUY_BELOW`, `TP_PCT` (e.g. `1.5`), `SL_PCT` (e.g. `1`).

```js
const PAIR = ($.Env.PAIR || "btcusdt").toLowerCase();
const BUY_BELOW = Number($.Env.BUY_BELOW || 0);
const TP_PCT = Number($.Env.TP_PCT || 1.5);
const SL_PCT = Number($.Env.SL_PCT || 1.0);

const S = (await $.Storage.get()) || { entry: null };
const save = async () => { await $.Storage.set(S); };

if (!(BUY_BELOW > 0)) { S.dbg = "set BUY_BELOW"; await save(); return; }

const px = await $.getExchangeRate($.Exchange.BINANCE, PAIR);
if (px === null) { S.dbg = "no price"; await save(); return; }

const last = $.Strategy.lastTrigger ? $.Strategy.lastTrigger.action : null;
const inLong = last === $.Action.LONG;

let action = null;
let reason = "";
if (!inLong && px < BUY_BELOW) {
  action = $.Action.LONG; reason = "dip-entry";
} else if (inLong) {
  const entry = S.entry || $.Strategy.lastTrigger.price;
  const movePct = entry ? ((px - entry) / entry) * 100 : 0;
  if (movePct >= TP_PCT) { action = $.Action.EXIT; reason = "take-profit"; }
  else if (movePct <= -SL_PCT) { action = $.Action.EXIT; reason = "stop-loss"; }
}

if (action) {
  await $.Strategy.action(action, { id: reason });
  S.entry = action === $.Action.LONG ? px : null;
  S.lastSignal = { action, reason, px, at: Date.now() };
}
S.lastPx = px;
await save();
```

## 2. RSI Mean Reversion On Hourly Candles (one decision per candle)

Settings: `send_signal: true`, `webhook_id`, `symbol: "ETHUSDT"`.
Env: `PAIR` (`ETHUSDT`), optional `RSI_LEN` (`14`), `RSI_BUY` (`30`),
`RSI_EXIT` (`55`), `SL_PCT` (`3`).

```js
const PAIR = ($.Env.PAIR || "ETHUSDT").toUpperCase();
const RSI_LEN = Number($.Env.RSI_LEN || 14);
const RSI_BUY = Number($.Env.RSI_BUY || 30);
const RSI_EXIT = Number($.Env.RSI_EXIT || 55);
const SL_PCT = Number($.Env.SL_PCT || 3);

const S = (await $.Storage.get()) || { lastBar: null, entry: null };
const save = async () => { await $.Storage.set(S); };

const res = await $.Http.get("https://data-api.binance.vision/api/v3/klines", {
  symbol: PAIR, interval: "1h", limit: 200,
});
if (res.status !== 200) { S.dbg = "klines http " + res.status; await save(); return; }

let rows = null;
try { rows = JSON.parse(res.text); } catch (e) { rows = null; }
if (!Array.isArray(rows) || rows.length < RSI_LEN + 5) { S.dbg = "bad klines"; await save(); return; }

// Ignore the still-forming candle. Row index 4 is the candle's final trade price.
const done = rows.slice(0, -1);
const barTime = done[done.length - 1][0];
if (S.lastBar === barTime) { await save(); return; }
S.lastBar = barTime;

const series = done.map((r) => Number(r[4]));
const lastPx = series[series.length - 1];

const rsi = new $.Ta.RSI(RSI_LEN);
for (const v of series) rsi.update(v);
if (!rsi.isStable) { S.dbg = "rsi warming up"; await save(); return; }
const value = Number(rsi.getResult());

const last = $.Strategy.lastTrigger ? $.Strategy.lastTrigger.action : null;
const inLong = last === $.Action.LONG;

let action = null;
let reason = "";
if (!inLong && value < RSI_BUY) {
  action = $.Action.LONG; reason = "rsi<" + RSI_BUY;
} else if (inLong && value > RSI_EXIT) {
  action = $.Action.EXIT; reason = "rsi>" + RSI_EXIT;
} else if (inLong && S.entry && lastPx <= S.entry * (1 - SL_PCT / 100)) {
  action = $.Action.EXIT; reason = "stop-loss";
}

if (action) {
  await $.Strategy.action(action, { id: reason });
  S.entry = action === $.Action.LONG ? lastPx : null;
}
S.last = { bar: barTime, rsi: Math.round(value * 100) / 100, px: lastPx, action: action || "HOLD", reason };
await save();
```

If `data-api.binance.vision` is unreachable, read the status code in
`S.dbg` and switch to another public klines source.

## 3. EMA Crossover, Long And Short (USD-M futures)

Settings: `send_signal: true`, `webhook_id` of a futures bot, `symbol`
matching it (e.g. `BTCUSDT`). Env: `PAIR`, `FAST` (`9`), `SLOW` (`21`).

A flip needs two runs: this run exits, a later run (next candle) enters the
other side if the trend still agrees.

```js
const PAIR = ($.Env.PAIR || "BTCUSDT").toUpperCase();
const FAST = Number($.Env.FAST || 9);
const SLOW = Number($.Env.SLOW || 21);

const S = (await $.Storage.get()) || { lastBar: null };
const save = async () => { await $.Storage.set(S); };

const res = await $.Http.get("https://data-api.binance.vision/api/v3/klines", {
  symbol: PAIR, interval: "15m", limit: 150,
});
let rows = null;
if (res.status === 200) { try { rows = JSON.parse(res.text); } catch (e) { rows = null; } }
if (!Array.isArray(rows) || rows.length < SLOW + 3) { S.dbg = "no candles " + res.status; await save(); return; }

const done = rows.slice(0, -1);
const barTime = done[done.length - 1][0];
if (S.lastBar === barTime) { await save(); return; }
S.lastBar = barTime;

const fast = new $.Ta.EMA(FAST);
const slow = new $.Ta.EMA(SLOW);
for (const r of done) { const v = Number(r[4]); fast.update(v); slow.update(v); }
if (!fast.isStable || !slow.isStable) { await save(); return; }
const trendUp = Number(fast.getResult()) > Number(slow.getResult());

const last = $.Strategy.lastTrigger ? $.Strategy.lastTrigger.action : null;
const isLong = last === $.Action.LONG;
const isShort = last === $.Action.SHORT;

let action = null;
if ((isLong && !trendUp) || (isShort && trendUp)) action = $.Action.EXIT;
else if (!isLong && !isShort) action = trendUp ? $.Action.LONG : $.Action.SHORT;

if (action) await $.Strategy.action(action, { id: "ema-" + FAST + "-" + SLOW });
S.last = { bar: barTime, trendUp, action: action || "HOLD" };
await save();
```

## 4. Code Reaction: Validated External Signal With De-duplication

Settings: Code Reaction with `data_webhook_id` (key-protected Data Webhook),
`send_signal: true`, `webhook_id`, `symbol: "BTCUSDT"`, `delay` set.
Env: `MIN_CONF` (`0.8`). Expected input:
`{"id":"evt-123","signal":"BUY"|"EXIT","symbol":"BTCUSDT","confidence":0.86}`.

```js
let p = null;
try { p = JSON.parse($.Request.data); } catch (e) { return; }
if (!p || typeof p !== "object") return;

const MIN_CONF = Number($.Env.MIN_CONF || 0.8);
const wanted = ($.Strategy.signalSymbols || [])[0];
const S = (await $.Storage.get()) || { seen: [] };

const evtId = typeof p.id === "string" ? p.id.slice(0, 64) : null;
const signal = String(p.signal || "").toUpperCase();
const conf = Number(p.confidence);
const valid = evtId && p.symbol === wanted && (signal === "BUY" || signal === "EXIT") && conf >= 0 && conf <= 1;

if (!valid || S.seen.includes(evtId)) {
  S.rejected = { at: Date.now(), evtId, reason: valid ? "duplicate" : "invalid" };
  await $.Storage.set(S);
  return;
}

const last = $.Strategy.lastTrigger ? $.Strategy.lastTrigger.action : null;
const inLong = last === $.Action.LONG;

let action = null;
if (!inLong && signal === "BUY" && conf >= MIN_CONF) action = $.Action.LONG;
else if (inLong && signal === "EXIT") action = $.Action.EXIT;

if (action) await $.Strategy.action(action, { id: evtId });
S.seen = S.seen.concat([evtId]).slice(-50);
S.lastEvent = { evtId, signal, conf, action: action || "NONE", at: Date.now() };
await $.Storage.set(S);
```

## 5. Relay To A Prediction Bot Webhook

Prediction bots accept only webhook signals, so post the prediction payload
directly. Settings: `send_signal: false` (no webhook needed).
Env: `PRED_HOOK_URL` (`https://hook.sigrex.io/bot/<hash>`), `PRED_HOOK_KEY`,
`PRED_SLUG`, `PRED_SIZE` (`5`), `TRIGGER_ABOVE` (BTC price).

```js
const S = (await $.Storage.get()) || { entered: false };
const px = await $.getExchangeRate($.Exchange.BINANCE, "btcusdt");
const level = Number($.Env.TRIGGER_ABOVE || 0);

if (px !== null && level > 0 && px > level && !S.entered) {
  const res = await $.Http.post($.Env.PRED_HOOK_URL, {
    key: $.Env.PRED_HOOK_KEY,
    slug: $.Env.PRED_SLUG,
    outcome: "Yes",
    side: "BUY",
    size: Number($.Env.PRED_SIZE || 5),
    id: "btc-above-" + level,
  });
  S.entered = res.status >= 200 && res.status < 300;
  S.lastPost = { status: res.status, px, at: Date.now() };
}
await $.Storage.set(S);
```

## 6. Self-Stopping Loss Guard

Stops the strategy after `MAX_LOSSES` consecutive losing exits. Combine with
your entry logic; this shows only the guard bookkeeping.

```js
const MAX_LOSSES = Number($.Env.MAX_LOSSES || 3);
const S = (await $.Storage.get()) || { entry: null, losses: 0 };
const px = await $.getExchangeRate($.Exchange.BITGET, "btcusdt");
const inLong = ($.Strategy.lastTrigger || {}).action === $.Action.LONG;

if (S.losses >= MAX_LOSSES) {
  if (inLong) {
    await $.Strategy.action($.Action.EXIT, { id: "guard-exit" });
    S.entry = null;
    await $.Storage.set(S);
    return;
  }
  S.stoppedAt = Date.now();
  await $.Storage.set(S);
  await $.Strategy.stop(true);
  return;
}

// ... entry/exit logic here; when it exits a long:
// if (px !== null && S.entry && px < S.entry) S.losses += 1; else S.losses = 0;

await $.Storage.set(S);
```

The guard exits first and stops on a later run, because only one action is
allowed per run and `stop()` does not close positions.

## 7. Manager: Pause A Strategy When Its Bot Webhook Is Disabled

Uses the Sigrex API client. Settings: `send_signal: false`.
Env: `SIGREX_API_KEY`, `SIGREX_API_SECRET`, `TARGET_STRATEGY_ID`,
`WATCH_WEBHOOK_ID`.

```js
const client = $.Http.createApiClient({
  apiKey: $.Env.SIGREX_API_KEY,
  apiSecret: $.Env.SIGREX_API_SECRET,
});
const S = (await $.Storage.get()) || {};

let hook = null;
try { hook = await client.webhooks.bot.get(Number($.Env.WATCH_WEBHOOK_ID)); } catch (e) { S.dbg = String(e).slice(0, 200); }

const hookStatus = hook && (hook.status || (hook.data && hook.data.status));
if (hookStatus === "INACTIVE" && !S.paused) {
  await client.strategies.code.status(Number($.Env.TARGET_STRATEGY_ID), { status: "INACTIVE" });
  S.paused = Date.now();
}
S.lastCheck = { at: Date.now(), hookStatus: hookStatus || "unknown" };
await $.Storage.set(S);
```

Response shapes are not published; log the object once into storage and
adjust the field access (`hook.status`) to what you see.
