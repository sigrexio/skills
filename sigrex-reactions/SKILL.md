---
name: sigrex-reactions
description: Build Sigrex event-driven Data Webhook pipelines with Code Reactions or LLM Reactions. Use when ingesting external JSON, validating webhook events, filtering signals, classifying data, or connecting reactions to trading bots.
metadata:
  author: sigrex
  version: "1.0"
---

# Sigrex Reactions

Use the pipeline `external POST -> Data Webhook -> Reaction -> optional
signal/bot`. A Data Webhook stores and forwards JSON; it does not execute a
trade by itself.

## Select A Reaction

- Choose **Code Reaction** for deterministic validation, normalization,
  filtering, stateful logic, or a safety gate.
- Choose **LLM Reaction** for interpretation or classification of incoming
  data. Make its action rules explicit and fail closed on uncertainty.

## Data Webhook Contract

Data Webhooks accept JSON only. A protected webhook requires:

```http
POST <data-webhook-url>
Content-Type: application/json
X-Key: <secret>

{"event":"price_alert","symbol":"BTCUSDT","price":67250}
```

The platform currently does not enforce a user-defined schema, so reactions
must validate fields themselves. Treat URL, key, headers, and sender IP as
sensitive input.

## Code Reaction Pattern

```js
let payload;
try {
  payload = JSON.parse($.Request.data);
} catch (error) {
  return;
}

if (payload.signal === "BUY" && payload.confidence > 0.8) {
  await $.Strategy.action($.Action.LONG);
}
```

Code Reactions share the Code Strategy sandbox and limits. They receive
`$.Request.data`, `$.Request.headers`, and optionally `$.Request.ip`. Never
trust a field merely because it came through a webhook.

## LLM Reaction Prompt

Use `{{data}}`, `{{headers}}`, and `{{ip}}` explicitly. State when to act, when
to exit, how to handle conflicting data, and that uncertain input means no
action. LLM Reactions are event-driven, not scheduled, and support no chart or
image input.

## Lifecycle And Sharing

Before deleting a Data Webhook, check attached reactions; the API can return
`409` while it is in use. Use key protection when sharing. Confirm activation,
sharing, deletion, or any connection to a live Signal Bot with the user.

## Canonical Docs

- https://docs.sigrex.io/reaction/data-webhook.md
- https://docs.sigrex.io/reaction/code-reaction.md
- https://docs.sigrex.io/reaction/llm-reaction.md
- https://docs.sigrex.io/api-reference/reference/hooks/data-hooks.md
