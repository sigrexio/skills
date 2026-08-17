---
name: sigrex-api-mcp
description: Integrate with Sigrex through its signed API or MCP server, including request signing, endpoint discovery, and secure credential handling. Use when calling the Sigrex API, configuring an MCP client, or troubleshooting authentication.
metadata:
  author: sigrex
  version: "1.0"
---

# Sigrex API And MCP

Prefer the Sigrex MCP server when the client supports MCP discovery. The
documented endpoint is `https://mcp.sigrex.io`. Otherwise use the REST API at
`https://api.sigrex.io/api/v2`.

## REST Authentication

Every API request uses the public `api-key`, current Unix `timestamp`, and a
`signature`. Sigrex supports HMAC-SHA256 and ML-DSA44. The signing message is:

- `METHOD + PATH + TIMESTAMP` for GET and DELETE
- `METHOD + PATH + BODY + TIMESTAMP` for POST and PUT

Use the exact serialized request body for signing. Generate signatures on a
trusted backend, never in browser/frontend code, and never print API secrets,
private keys, or signatures in logs.

The official TypeScript client is available at
https://github.com/sigrexio/sigrex-client-ts. Prefer it when the runtime can
keep credentials server-side; otherwise follow the signing contract exactly.

## Resource Map

The API reference is grouped into these resource families:

```text
GET /exchange
GET /exchange/cex
GET /exchange/dex/{chain}
GET /exchange/prediction
GET /exchange/with-exchange-rate

/api/llm       LLM provider connections and models
/api/exchange  CEX API-key connections
/api/prediction Prediction API-key connections

/strategy/code
/strategy/llm-session
/strategy/reaction/code
/strategy/reaction/llm

/bot/signal/cex
/bot/signal/dex
/bot/signal/prediction

/webhook/bot
/webhook/data
```

Read `references/api-surface.md` for operation and field matrices before
constructing a request. The API docs use `ACTIVE` and `INACTIVE` statuses;
resource or plan limits commonly return `402`, and deleting a referenced
resource commonly returns `409`.

## MCP Configuration

Use the host client's native remote HTTP MCP configuration for:

```text
https://mcp.sigrex.io
```

Do not invent tool names or request schemas. Discover the server tools first,
then inspect each tool's input schema before calling it.

## API Workflow

1. Identify the documented resource and endpoint.
2. Read the matching page in the Sigrex API reference when parameters matter.
3. Build and display a dry-run request with secrets redacted.
4. Ask for confirmation before mutating, activating, sharing, deleting, or
   trading.
5. Sign and send only after approval; report status and a redacted response.

If local references conflict with live docs, prefer the live canonical page
and mention the discrepancy.

## Credential Lifecycle

Discover provider, exchange, or prediction IDs before creating connections.
Exchange credentials cannot be edited; detach dependent bots, delete the old
connection, and create a replacement. Use separate spot and futures
connections. Treat `funderAddress` as a string address even though one
prediction test schema documents it incorrectly as a number.

## Canonical Docs

- https://docs.sigrex.io/more/mcp-server.md
- https://docs.sigrex.io/api-reference/reference/sigrex-api.md
- https://docs.sigrex.io/api-reference/reference/hooks/bot-hooks.md
- https://docs.sigrex.io/api-reference/reference/hooks/data-hooks.md
- https://docs.sigrex.io/api-reference/reference/exchanges.md
- https://docs.sigrex.io/api-reference/reference/strategies.md
- https://docs.sigrex.io/api-reference/reference/signal-bots.md
- https://docs.sigrex.io/api-reference/reference/api-keys.md
