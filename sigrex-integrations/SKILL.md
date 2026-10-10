---
name: sigrex-integrations
description: Connect external signal sources to Sigrex - TradingView alerts (webhook or email), custom scripts and servers, the Sigrex Chrome extension and dashboard Manual Signal, the Notiflow Android notification-to-webhook app, and email-to-webhook - with correct payload mapping, sizing pitfalls and security. Also points to LLM provider setup. Use when wiring any outside tool or alert into a Sigrex Bot or Data Webhook.
compatibility: Bundled scripts require Python 3.8+ (standard library only).
metadata:
  author: sigrex
  version: "2.0"
---

# Sigrex Integrations (signal sources)

Every external source ends up as either a **signal to a Bot Webhook**
(trades through attached bots) or **JSON to a Data Webhook** (processed by
Reactions). Capture and validate what a source actually sends before
pointing it at a live bot.

> Telegram Signals and the Pine Script Payload Builder (the
> `jsonSignalBuilderV2` library) were removed from Sigrex and its docs. Do not
> recommend them. Use a plain JSON alert message (below) or a Data Webhook.

## TradingView

TradingView alerts can call a webhook URL or send an email. Both work with
Sigrex. Webhook alerts depend on TradingView's plan and account requirements
(e.g. two-factor authentication), so check TradingView's current rules.

**Webhook alert**

1. Alert dialog > Notifications > Webhook URL:
   `https://hook.sigrex.io/bot/<hash>`.
2. Message: a JSON signal. The `symbol` must match the bot exactly. Static
   example:

```json
{"key": "<webhook-key>", "symbol": "BTCUSDT", "side": "BUY", "id": "tv-btc-breakout"}
```

Using TradingView placeholders for a strategy script (one alert handles both
sides):

```json
{"key": "<webhook-key>", "symbol": "{{ticker}}", "side": "{{strategy.order.action}}", "id": "{{strategy.order.id}}"}
```

- `{{strategy.order.action}}` yields `buy`/`sell`; Sigrex accepts lowercase
  sides.
- `{{ticker}}` must produce exactly the bot's symbol (e.g. `BTCUSDT`, not
  `BTCUSDT.P`). Hardcode the symbol when the chart ticker differs from the
  exchange symbol.
- **Sizing trap:** `{{strategy.order.contracts}}` is a base-currency
  quantity, but Sigrex opening `size` is quote currency. Either let the bot
  use its fixed `amount`, or send a quote amount you compute yourself. Never
  map contracts to `size` on entries.
- Add `"flag": "TEST"` while validating. Remove it only after approval.
- The key travels inside the alert message: anyone who can read your alerts
  can trade through the hook. Use a dedicated hook per alert set.

**Email alert:** send the same JSON as the alert message to
`<hash>@sigrex.io`. Sigrex detects valid signal payloads in emails and
triggers the bots; non-signal emails are forwarded to the account's
registered address.

**Indicator-only alerts** (no strategy script): create separate BUY and
SELL alerts with static JSON messages, or send raw data to a Data Webhook and
decide in a Code Reaction.

## Custom Scripts, Bots And Servers

Any system that can POST JSON can send signals:

```bash
curl -X POST "https://hook.sigrex.io/bot/<hash>" -H "Content-Type: application/json" \
  -d '{"key":"<webhook-key>","symbol":"BTCUSDT","side":"SELL","flag":"TEST","callback":"https://my.app/fills"}'
```

```python
import json, os, urllib.request

payload = {"key": os.environ["SIGREX_HOOK_KEY"], "symbol": "BTCUSDT", "side": "BUY", "flag": "TEST"}
req = urllib.request.Request(os.environ["SIGREX_HOOK_URL"], data=json.dumps(payload).encode(),
                             headers={"Content-Type": "application/json"}, method="POST")
print(urllib.request.urlopen(req, timeout=10).status)
```

Keep hook URLs and keys in environment variables or a secret store. Use
`callback` to receive execution results (see `sigrex-webhooks`). For raw
events that need logic first, POST to a Data Webhook with `X-Key` instead.

## Chrome Extension And Manual Signal

The Sigrex Chrome extension
(https://chromewebstore.google.com/detail/towerflow/booenncomgienhnfhjgmcbmeogfhhbmc)
sends manual BUY/SELL signals from any page, through the same pipeline as the
dashboard's Manual Signal:

1. Sign in once; the extension syncs the Bot Webhooks you own or can access
   (tokens are scoped and revocable).
2. Fields: **Webhook**, **Symbol**, **Order Side** (BUY/SELL), optional
   **Amount** (interpreted by the receiving bot's configuration; `0` means
   "use the bot default").
3. All connected bots receive the signal immediately. There is no
   confirmation step on the exchange side, so double-check the webhook.

Use it for discretionary/hybrid trading and quick webhook tests. Exactly which
extra payload fields (key, flags) it sends is not documented; inspect the
signal log if it matters.

## Notiflow (Android)

Notiflow turns notifications from other apps into webhook calls: you define
keywords, and when a notification matches, it sends a custom payload to a
webhook in the background.

- Android 7.0+, notification-access permission (iOS "coming soon").
- Source: https://github.com/Towerflow/notiflow (APK linked from the docs).
- Notification access exposes private messages, 2FA codes and banking alerts
  to the app. Verify the APK source or build it yourself.
- Safer wiring: point Notiflow at a **Data Webhook** and let a Code Reaction
  validate and de-duplicate before any trade. Point it at a Bot Webhook only
  with a fixed, fully specified payload and a small bot size.
- Keyword triggers fire on any matching notification (including spam or
  repeats). Use `delay` on bots/reactions to throttle.

## Other AI Assistants

Claude, ChatGPT, Codex, Cursor, VS Code, Hermes and OpenClaw connect through
the Sigrex MCP server (`sigrex-api-mcp`). LLM providers used **inside**
Sigrex strategies (OpenAI, Anthropic, Gemini, OpenRouter, ... 23 IDs) are
configured as LLM API keys (`sigrex-llm-trading`).

## Source Checklist

1. Decide Bot Webhook (direct execution) vs Data Webhook (logic first).
2. Make the source emit exactly the payload you validated with
   `scripts/validate_signal.py`.
3. Send `TEST` signals; confirm symbol matching in the signal log.
4. Protect the hook with a key; keep URLs and keys out of shared screenshots,
   repos and chat logs.
5. Go live only with approval and minimum sizes.

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
- https://docs.sigrex.io/more/browser-extension.md
- https://docs.sigrex.io/more/notiflow-app.md
- https://docs.sigrex.io/more/mcp-server.md
