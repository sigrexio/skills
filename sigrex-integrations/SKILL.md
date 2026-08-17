---
name: sigrex-integrations
description: Configure Sigrex external integrations including LLM provider connections, Telegram Signals, Notiflow, the browser extension, and the Pine Script payload builder. Use when connecting external sources or managing provider-specific signal inputs.
metadata:
  author: sigrex
  version: "1.0"
---

# Sigrex Integrations

External integrations feed Sigrex webhooks. Capture and validate their actual
output before connecting them to a live bot. The Telegram, Notiflow, and
browser extension docs do not publish complete retry, deduplication, or payload
contracts; do not invent those behaviors.

## LLM Provider Connections

Discover services and models before creating a connection:

```text
GET /api/v2/api/llm/services
GET /api/v2/api/llm/models/{serviceId}
GET/POST /api/v2/api/llm
PUT /api/v2/api/llm/{id}/model
DELETE /api/v2/api/llm/{id}
```

Documented provider IDs include Gemini `1`, OpenAI `2`, DeepSeek `3`, Claude
`4`, Mistral `5`, Cohere `6`, Grok `7`, Qwen `8`, Kimi `10`, Z.ai `11`, MiniMax
`12`, Nvidia `13`, Nous `14`, OpenRouter `15`, Groq `17`, Cerebras `18`,
SiliconFlow `19`, and SambaNova `20`. Perplexity `9` is suspended. Use the
live service list rather than assuming this list is current.

Create with `serviceId`, `modelId`, `apiKey`, and optional `name`. Sigrex
validates the provider key on creation. Keys cannot be edited; rotate by
detaching dependent strategies, deleting, and recreating. Keep keys out of
prompts and frontend code.

## Telegram Signals

Telegram Signals uses Sigrex partner channels. Creating a connector creates a
dedicated channel webhook; connect that webhook to a Signal Bot to forward
signals. Channels may be free or subscription-based.

Use a dedicated low-risk webhook and bot per provider. The docs do not define
the message parser, normalized payload, retries, subscriptions, or
deduplication. Validate several real messages before activation.

## Notiflow Android App

Notiflow requires Android 7.0 or newer and notification-access permission. It
matches configured keywords in other apps' notifications and sends a custom
webhook payload in the background.

Notification access can expose private messages, authentication codes, and
financial alerts. Verify APK provenance or build from the linked source. First
send to a capture endpoint or inactive Data Webhook, inspect the emitted JSON,
then add validation before any Bot Webhook.

Canonical sources:

- https://docs.sigrex.io/more/notiflow-app.md
- https://github.com/sigrexio/notiflow

## Browser Extension

The Chrome extension syncs accessible Bot Webhooks and exposes Webhook,
Symbol, Side, and optional Amount fields. `BUY` and `SELL` use the manual
signal path; optional zero values are ignored according to the docs.

The docs do not specify whether webhook `key`, `dilution`, `forceSize`, `flag`,
or `debug` are sent, nor the exact Amount-to-`size` mapping. Inspect the
actual request and extension permissions before using it with a live bot.

## Pine Script Payload Builder

The documented import is:

```pinescript
import x7s0lt1/jsonSignalBuilderV2/1 as json
```

Available helpers are `json.str`, `json.num`, `json.bool`, `json.raw`, and
`json.object`. `json.object` accepts up to 20 pairs; empty strings can omit
unused slots. Use `alert.freq_once_per_bar` when matching the documented
example.

`json.raw` inserts unescaped content and can create invalid or unsafe JSON.
Validate the generated payload against the Sigrex schema. The example's
`name`, `stop`, `take`, and `public` fields are not documented generic signal
fields, so do not assume they implement order controls. The linked TradingView
script may be unavailable; treat it as an unverified dependency.

## Canonical Docs

- https://docs.sigrex.io/llm/connecting-llm-service.md
- https://docs.sigrex.io/social/telegram-signals.md
- https://docs.sigrex.io/more/notiflow-app.md
- https://docs.sigrex.io/more/browser-extension.md
- https://docs.sigrex.io/more/pine-script-payload-builder.md
