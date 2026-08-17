---
name: sigrex-code-strategies
description: Write and review Sigrex sandboxed JavaScript Code Strategies and Code Reactions using $.Price, $.Strategy, $.Storage, $.Http, and $.Ta. Use when creating Sigrex strategy code, event reactions, indicators, trade actions, or sandbox debugging.
metadata:
  author: sigrex
  version: "1.0"
---

# Sigrex Code Strategies

Write deterministic sandbox code using the injected `$` APIs. A Code Strategy
runs on its configured schedule/trigger; a Code Reaction runs when a Data
Webhook receives an event and additionally exposes `$.Request`.

## Safe Implementation Order

1. Parse and validate all external input before making decisions.
2. Read current state from `$.Strategy.lastTrigger` and persistent state from
   `$.Storage.get()`.
3. Compute the decision with `$.Price`, `$.getExchangeRate()`, or `$.Ta`.
4. Execute at most one action with `await $.Strategy.action(...)`.
5. Persist only the minimal state needed by the next run.
6. Test with `TEST` payloads or an inactive bot before enabling live execution.

## Core API

```js
const state = await $.Storage.get() || { runs: 0 };
state.runs += 1;

if ($.Price.price > 25000 && $.Strategy.lastTrigger.action !== $.Action.LONG) {
  await $.Strategy.action($.Action.LONG, { dilution: false });
}

await $.Storage.set(state);
```

Use `LONG`, `SHORT`, or `EXIT`. Only one action is allowed per run, globally
there can be at most five actions per second, and consecutive `EXIT` actions
are not permitted. `stop()` changes future status but does not terminate the
current process; use `return` after it when termination is intended.

## HTTP And State Limits

- Use `$.Http.get/post/put/delete`, never browser or runtime networking APIs.
- HTTP requests time out after 1750 ms and responses may be cached for 5
  seconds; inspect `status`, `text`, and `cache`.
- Strategy execution is limited to 5000 ms.
- Strategy JSON storage is limited to 24 KB.
- Never place API secrets in source; read user-configured values through
  `$.Env`.

## Sandbox Restrictions

Do not use blocked globals or identifiers, including browser APIs, Node/Deno
APIs, dynamic code execution, timers, `console`, or `fetch`. These identifiers
can fail validation even inside comments. Use only the documented `$` APIs.

## Code Reactions

For a Code Reaction, parse the incoming body as `JSON.parse($.Request.data)`.
Validate its shape and fail closed when fields are missing or untrusted. The
reaction is event-driven, has no chart/image input, and should not assume a
webhook payload is schema-validated by Sigrex.

## Canonical Docs

- https://docs.sigrex.io/startegies/code.md
- https://docs.sigrex.io/reaction/code-reaction.md
- https://docs.sigrex.io/getting-started/signal-payload-format.md
