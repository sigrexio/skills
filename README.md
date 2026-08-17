# Sigrex Agent Skills

Reusable [Agent Skills](https://agentskills.io/) for building, operating, and
integrating with [Sigrex](https://docs.sigrex.io/), a trading automation
platform.

## Skills

| Skill | Use it for |
| --- | --- |
| [`sigrex-overview`](sigrex-overview/SKILL.md) | Platform architecture and choosing the right Sigrex component |
| [`sigrex-webhooks`](sigrex-webhooks/SKILL.md) | Bot and data webhooks, signal payloads, security, and testing |
| [`sigrex-cex-bots`](sigrex-cex-bots/SKILL.md) | CEX credentials, exchange catalog, sizing, and Signal Bots |
| [`sigrex-dex-bots`](sigrex-dex-bots/SKILL.md) | Uniswap bots, Polygon/Arbitrum deployment, GasTank, and ABIs |
| [`sigrex-prediction-bots`](sigrex-prediction-bots/SKILL.md) | Polymarket wallet setup, markets, outcomes, and prediction payloads |
| [`sigrex-code-strategies`](sigrex-code-strategies/SKILL.md) | Sandboxed JavaScript strategies and Code Reactions |
| [`sigrex-llm-trading`](sigrex-llm-trading/SKILL.md) | LLM Sessions, prompts, signal generation, and trading tools |
| [`sigrex-reactions`](sigrex-reactions/SKILL.md) | Event-driven Data Webhook pipelines and Reactions |
| [`sigrex-api-mcp`](sigrex-api-mcp/SKILL.md) | Signed REST API requests, resource operations, and MCP integration |
| [`sigrex-social`](sigrex-social/SKILL.md) | Friends, sharing, and multi-user access |
| [`sigrex-integrations`](sigrex-integrations/SKILL.md) | LLM providers, Telegram, Notiflow, browser, and Pine Script inputs |

## Structure

Each skill is self-contained and follows the Agent Skills format:

```text
sigrex-webhooks/
└── SKILL.md
```

Install or copy the individual skill directories into the skill directory
supported by your agent. Do not merge the files into one large skill: separate
packages allow agents to load only the workflow they need. The API skill keeps
its detailed endpoint map in `sigrex-api-mcp/references/api-surface.md` for
progressive disclosure.

## Documentation

The skills cover the platform and API domains listed in the canonical Sigrex
documentation at
[`docs.sigrex.io`](https://docs.sigrex.io/llms.txt). Trading actions are treated
as live and potentially irreversible: each skill requires confirmation before
activation, mutation, sharing, deletion, or execution against real capital.
