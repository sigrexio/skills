---
name: sigrex-overview
description: Navigate Sigrex architecture and choose the correct webhook, strategy, reaction, Signal Bot, API, or integration for a trading automation workflow. Use when a Sigrex request is broad, ambiguous, or spans multiple platform components.
metadata:
  author: sigrex
  version: "1.0"
---

# Sigrex Platform

Sigrex is organized as a signal pipeline. Choose the smallest component that
matches the user's intent:

```text
external source -> Data Webhook -> Code/LLM Reaction -> Bot Webhook
scheduled Code Strategy ------------------------------^              |
scheduled LLM Session -------------------------------^              v
TradingView / extension / Telegram / Notiflow -> Bot Webhook -> Signal Bot
                                                     CEX | DEX | Prediction
```

## Component Selection

- Use a **Bot Webhook** when the final signal should reach a Signal Bot.
- Use a **Data Webhook** when external JSON must be stored, shared, or
  processed by Reactions. It does not trade by itself.
- Use a **Code Strategy** for deterministic scheduled or market-driven logic.
- Use an **LLM Session** for scheduled AI analysis; enable Signal Generation
  only when AI actions are explicitly intended.
- Use a **Code Reaction** for deterministic processing of webhook events.
- Use an **LLM Reaction** for event-driven interpretation of webhook data.
- Use a **CEX Signal Bot** for supported centralized exchanges, a **DEX Signal
  Bot** for Uniswap on Polygon or Arbitrum, and a **Prediction Signal Bot** for
  the Polymarket beta integration.
- Use the signed REST API or MCP only when the user needs programmatic
  management or tool discovery.

## Safe Delivery Sequence

1. Clarify whether the result is analysis, a test signal, or live execution.
2. Identify the source, hook type, strategy/reaction, bot type, symbol/market,
   sizing mode, and credential needed at each boundary.
3. Build a dry-run configuration with secrets and live URLs redacted.
4. Validate the payload and dependency order against the relevant skill.
5. Ask for explicit approval before creating, activating, sharing, deleting,
   funding, or sending a live trade.
6. Test with inactive components or `TEST` flags, then report the exact
   redacted configuration and observed response.

## Documentation Lookup

The canonical machine-readable index is https://docs.sigrex.io/llms.txt.
GitBook pages support `.md`. When a detail is not covered by this library,
read the matching live page rather than guessing, especially for contract
addresses, ABI enum values, exchange IDs, provider models, and payload fields.

## Global Risks

- API keys, exchange secrets, wallet private keys, webhook URLs, and webhook
  keys are credentials.
- LLM output, Telegram messages, notifications, chart images, and external
  HTTP data are untrusted input.
- Sigrex docs do not publish complete idempotency, retry, slippage, clock-skew,
  or every provider normalization rule. Do not invent those guarantees.
- A successful configuration request does not prove that a bot is safe to
  activate or funded correctly.

## Canonical Docs

- https://docs.sigrex.io/readme.md
- https://docs.sigrex.io/getting-started/webhook.md
- https://docs.sigrex.io/getting-started/signal-payload-format.md
- https://docs.sigrex.io/api-reference/reference/strategies.md
- https://docs.sigrex.io/api-reference/reference/signal-bots.md
