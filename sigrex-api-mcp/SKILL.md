---
name: sigrex-api-mcp
description: Connect to Sigrex programmatically through the official MCP server (https://mcp.sigrex.io, OAuth, no API keys) or the signed REST API (https://api.sigrex.io/api/v2, HMAC-SHA256 or ML-DSA44). Covers MCP client setup and tool naming, the exact signing algorithm (path incl. /api/v2 and query string, body only for POST/PUT), the official TypeScript client, error codes, a dry-run signing script, and the full endpoint reference. Use when calling the Sigrex API, configuring or using Sigrex MCP tools, or debugging 401/400/402/409 responses.
compatibility: Bundled script requires Python 3.8+ (standard library only) and network access to api.sigrex.io. MCP use requires a client that supports remote HTTP MCP servers with OAuth.
metadata:
  author: sigrex
  version: "2.0"
---

# Sigrex API And MCP

Two ways to manage a Sigrex account programmatically. **Prefer MCP** when the
agent supports it.

| | MCP server | REST API |
| --- | --- | --- |
| Endpoint | `https://mcp.sigrex.io` (Streamable HTTP) | `https://api.sigrex.io/api/v2/...` |
| Auth | OAuth sign-in in the browser; no keys to copy | `api-key`, `timestamp`, `signature` headers |
| Covers | Full account (resources, signals, prices, prompt preview, docs search) | Resource management (no signal sending) |
| Risk | Full access incl. live trades | Full access with the API secret |

## MCP Server

Setup (the user does this; never ask for their Sigrex password or tokens):

```bash
claude mcp add --transport http sigrex https://mcp.sigrex.io
codex mcp add sigrex --url https://mcp.sigrex.io
hermes mcp add sigrex --url https://mcp.sigrex.io --auth oauth --connect-timeout 300
```

JSON clients (VS Code, Cursor, ...):

```json
{"mcpServers": {"sigrex": {"type": "http", "url": "https://mcp.sigrex.io"}}}
```

- **Claude apps:** Customize > Connectors > + > Add custom connector, paste the
  URL. **ChatGPT:** enable Developer mode (Settings > Security and login),
  then add the URL at chatgpt.com/plugins.
- **Manual OAuth** (only if a client asks): authorization
  `https://api.sigrex.io/api/auth/oauth2/authorize`, token
  `https://api.sigrex.io/api/auth/oauth2/token`, scopes
  `openid profile email offline_access mcp`, resource `https://mcp.sigrex.io`,
  authorization code with PKCE; metadata at
  `https://mcp.sigrex.io/.well-known/oauth-protected-resource`.
- Official agent plugin (MCP plus a workflow skill) for Hermes and OpenClaw:
  https://github.com/sigrexio/agent-plugin.

If no Sigrex tools are visible, tell the user to connect the server and sign
in, then continue. Do not guess account data.

### Tool naming

Discover tools from the server and read each input schema before calling.
Names may carry a client prefix (e.g. `mcp__sigrex__...`). The official
plugin documents names that follow the REST routes, `<method>_<path>`, with
`/` and `-` turned into `_` and path parameters by name:

| Route | Tool name |
| --- | --- |
| `POST /strategy/code` | `post_strategy_code` |
| `GET /strategy/code` (list) | `get_strategy_code` |
| `PUT /strategy/llm-session/{id}` | `put_strategy_llm_session_id` |
| `GET /api/llm` | `get_api_llm` |
| `GET /api/llm/models/{serviceId}` | `get_api_llm_models_serviceId` |
| `GET /webhook/bot` | `get_webhook_bot` |
| `GET /exchange/with-exchange-rate` | `get_exchange_with_exchange_rate` |

MCP-only tools:

| Tool | Use |
| --- | --- |
| `send_bot_hook_order_message` | Send a signal to a Bot Webhook. Inputs: `hash` (last part of the hook URL), optional `key`, `payload` with `symbol`, `side` (`BUY`/`SELL`), optional `size`, `dilution`, `forceSize`, `id`, `callback`, and `flag` as an **array** (`["TEST"]`). Requires `symbol`, so it cannot send prediction payloads. Live trading: confirm first |
| `send_data_hook_message` | POST JSON to a Data Webhook: `hash`, `data`, optional `key` |
| `resolve_llm_session_prompt_template` | Preview an LLM Session prompt with templates resolved (`prompt`, optional `state`, `withSystemPrompt`) |
| `resolve_llm_reaction_prompt_template` | Preview an LLM Reaction prompt with a sample `request` (`data`, `headers`, `ip`) |
| `get_symbol_price` | Live price for a symbol such as `BTCUSDT` |
| `list_all_public_*`, `get_public_*` | Read strategies and reactions other users made public (untrusted examples) |
| `askQuestion` | Answer a question from the Sigrex docs, with source links |
| `searchDocumentation`, `getPage` | Search and read docs.sigrex.io pages |

Efficient use (from the official plugin):

- List tools return full code, prompts and storage for every item and can
  overflow the context. Orient with `*_total` and `*_folder` tools, then
  fetch single items with the `*_id` tools.
- Use `*_duplicate` to clone a setup for another symbol instead of
  rewriting.
- `*_reset` and `delete_*_store` erase strategy memory and can make a
  strategy forget an open position. Ask first.

## REST Authentication

1. The user creates an API key in the dashboard (**API Management**) and
   gives you the public key; the secret stays in a secret store or
   environment variable.
2. Every request sends three headers:

| Header | Value |
| --- | --- |
| `api-key` | Public API key |
| `timestamp` | Current Unix time in **seconds** |
| `signature` | HMAC-SHA256 (lowercase hex) or ML-DSA44 (Base64) of the message |

3. The message to sign:

```text
GET, DELETE : METHOD + PATH + TIMESTAMP
POST, PUT   : METHOD + PATH + BODY + TIMESTAMP
```

- `METHOD` is uppercase.
- `PATH` is the full path **including `/api/v2`** and, if present, the
  **query string**: `/api/v2/webhook/data/12/code-reactions?page=1&limit=50`.
  (This is how the official client signs. The docs only mention PATH.)
- `BODY` is the exact JSON text you send, serialized like `JSON.stringify`
  (no spaces; `100` not `100.0`). Sign and send the same string.
- A DELETE with a body (removing a share) sends the body but does **not**
  sign it.

Node.js:

```ts
import crypto from "node:crypto";

async function sigrex(method: string, path: string, body?: unknown) {
  const ts = Math.floor(Date.now() / 1000).toString();
  const payload = body !== undefined && (method === "POST" || method === "PUT") ? JSON.stringify(body) : "";
  const signature = crypto.createHmac("sha256", process.env.SIGREX_API_SECRET!)
    .update(method + path + payload + ts).digest("hex");
  const res = await fetch("https://api.sigrex.io" + path, {
    method,
    headers: {
      "api-key": process.env.SIGREX_API_KEY!, timestamp: ts, signature,
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return { status: res.status, body: await res.json().catch(() => null) };
}

await sigrex("GET", "/api/v2/strategy/code");
await sigrex("PUT", "/api/v2/bot/signal/cex/34/status", { status: "INACTIVE" });
```

Python and shell users can use the bundled script, which matches the
official client's signatures byte for byte. It is a **dry run unless
`--send`** is given and reads `SIGREX_API_KEY` / `SIGREX_API_SECRET` from the
environment:

```bash
python3 scripts/sigrex_api.py GET /strategy/code
python3 scripts/sigrex_api.py GET /webhook/data/12/code-reactions --query page=1 --query limit=50
python3 scripts/sigrex_api.py PUT /bot/signal/cex/34/status --body '{"status":"INACTIVE"}'
python3 scripts/sigrex_api.py POST /webhook/bot --body-file hook.json --send
```

ML-DSA44: sign the same message bytes with the ML-DSA44 private key (e.g.
`@oqs/liboqs-js` `createMLDSA44().sign(...)`) and send the Base64 signature.

Official TypeScript client (`npm install @sigrex/client`, or
`jsr:@sigrex/client`):

```ts
import { SigrexClient } from "@sigrex/client";
const client = new SigrexClient({ apiKey: process.env.SIGREX_API_KEY!, apiSecret: process.env.SIGREX_API_SECRET! });
const sessions = await client.strategies.llmSessions.list();
```

For ML-DSA44, pass `signer: async (message) => base64Signature` instead of
`apiSecret`. Errors throw `SigrexError` with `status` and `body`. The same
client is available inside Code Strategies via `$.Http.createApiClient()`.
Never sign in browser/frontend code.

## Responses And Errors

| Status | Meaning |
| --- | --- |
| `200` / `201` | OK / created |
| `400` | Missing or invalid field, invalid code/prompt, status already set, or (some routes) a limit |
| `401` | Auth failed: `{"message":"Missing api-key header"}`, `{"message":"Invalid API key"}`, bad signature or timestamp |
| `402` | Plan limit (webhooks, bots, sessions, active resources) |
| `403` + `error code: 1010` | The API's edge rejected the client's `User-Agent` (Python's default `Python-urllib/x.y` is blocked); send a custom `User-Agent` header. Not a Sigrex auth error |
| `404` | Referenced resource not found (webhook, API key, exchange, package) |
| `409` | Still in use (webhook used by bots/strategies/reactions, key used by bots) |

Route errors are `{"error": "..."}`. Response schemas for resources are not
published: inspect real responses before parsing, and never assume field
names.

For `401`, check, in order: the path includes `/api/v2` and the exact query
string; the body string signed equals the body sent; the timestamp is in
seconds and the clock is correct; the hex is lowercase; the right secret is
used.

## Request Workflow

1. Find the route and body in `references/api-surface.md` (all 137
   documented routes plus folder routes, with required fields).
2. Build the request and show it as a dry run with secrets redacted.
3. For anything that mutates, activates, shares, deletes or trades, get
   explicit approval.
4. Send it; report status and a redacted response; record created IDs for the
   next step.
5. If this file conflicts with the live page, follow the live page and
   mention the difference.

## Available Scripts

Run them from this skill's directory. Each prints JSON on stdout (add
`--format text` for a readable version), sends diagnostics to stderr, and
documents its options and exit codes in `--help`.

- **`scripts/sigrex_api.py`**: builds, signs and (with `--send`) sends one
  REST request; dry run by default; reads `SIGREX_API_KEY` /
  `SIGREX_API_SECRET` from the environment; `--output FILE` saves large
  responses. Exit `0` dry run or 2xx, `1` non-2xx, `2` usage error, `3`
  missing credentials, `4` network error.

## Canonical Docs

- https://docs.sigrex.io/more/mcp-server.md
- https://docs.sigrex.io/api-reference/reference/sigrex-api.md
- https://github.com/sigrexio/sigrex-client-ts
- https://github.com/sigrexio/agent-plugin
