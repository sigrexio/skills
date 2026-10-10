# Sigrex Agent Skills

[Agent Skills](https://agentskills.io/) that teach AI agents how
[Sigrex](https://docs.sigrex.io/) works and how to build, test, run and fix
complete trading automation on it: webhooks, Code and LLM strategies,
reactions, and CEX, DEX and prediction-market Signal Bots.

## Install

```
npx skills add sigrexio/skills
```

## Skills

Start with `sigrex-overview`, then load the skill for the task.

| Skill | Use it for |
| --- | --- |
| [`sigrex-overview`](sigrex-overview/SKILL.md) | How Sigrex works end to end, the execution checklist, venue IDs, global safety rules, which skill to load next |
| [`sigrex-strategy-flows`](sigrex-strategy-flows/SKILL.md) | Step-by-step playbooks for complete working flows, test ladder, go-live order, kill switch, troubleshooting |
| [`sigrex-webhooks`](sigrex-webhooks/SKILL.md) | Bot and Data Webhooks, the signal payload (incl. `callback`), sending and testing signals |
| [`sigrex-cex-bots`](sigrex-cex-bots/SKILL.md) | Exchange API keys and CEX Signal Bots: symbols, sizing, lifecycle |
| [`sigrex-dex-bots`](sigrex-dex-bots/SKILL.md) | Uniswap DEX bots on Polygon/Arbitrum, GasTank, contract addresses and ABIs |
| [`sigrex-prediction-bots`](sigrex-prediction-bots/SKILL.md) | Polymarket / Outcome.xyz prediction bots (beta, currently disabled), session keys, payloads |
| [`sigrex-code-strategies`](sigrex-code-strategies/SKILL.md) | Sandboxed JavaScript strategies and Code Reactions, runtime API, forbidden identifiers, tested examples |
| [`sigrex-llm-trading`](sigrex-llm-trading/SKILL.md) | LLM provider connections, LLM Sessions, prompt design, template variables, AI trading tools, charts |
| [`sigrex-reactions`](sigrex-reactions/SKILL.md) | Event-driven Data Webhook pipelines with Code or LLM Reactions |
| [`sigrex-api-mcp`](sigrex-api-mcp/SKILL.md) | MCP server (OAuth), signed REST API, TypeScript client, full endpoint reference |
| [`sigrex-social`](sigrex-social/SKILL.md) | Friends, sharing webhooks, copy-trading, public strategies |
| [`sigrex-integrations`](sigrex-integrations/SKILL.md) | TradingView, custom scripts, email, Chrome extension, Notiflow |

## Bundled Scripts

Python 3.8+ scripts, standard library only. They follow the spec's
[guidance for agent scripts](https://agentskills.io/skill-creation/using-scripts):
non-interactive, `--help`, JSON on stdout (`--format text` for humans),
diagnostics on stderr, documented exit codes, and dry-run by default where
something could change.

| Script | Purpose | Bundled in |
| --- | --- | --- |
| `check_sandbox.py` | Lints strategy/reaction code for forbidden sandbox identifiers and common mistakes | `sigrex-code-strategies` (source), `sigrex-reactions`, `sigrex-strategy-flows` |
| `validate_signal.py` | Validates bot and prediction signal payloads before sending | `sigrex-webhooks` (source), `sigrex-prediction-bots`, `sigrex-integrations`, `sigrex-strategy-flows` |
| `sigrex_api.py` | Signs REST requests exactly like the official client; sends only with `--send` | `sigrex-api-mcp` |

Each skill must work when installed alone, so a skill that needs a script
carries its own copy. The copies are identical: edit the source copy, then
copy it over and confirm with `cmp`.

## Structure

Each skill is self-contained and follows the
[Agent Skills specification](https://agentskills.io/specification): a
`SKILL.md` with `name`, `description` and (where scripts are bundled)
`compatibility` frontmatter, plus optional `references/` (detail loaded on
demand) and `scripts/`. File paths inside a skill are relative to that
skill's directory; skills mention each other by name only. Validate with the
spec's reference tool:

```bash
skills-ref validate ./sigrex-webhooks
```

```text
sigrex-code-strategies/
├── SKILL.md
├── references/
│   ├── runtime-api.md
│   └── examples.md
└── scripts/
    └── check_sandbox.py
```

Install or copy the skill directories into the skill directory your agent
supports. Keep them separate so agents load only the workflow they need.

## Sources And Accuracy

Content is checked against the live documentation index
([`docs.sigrex.io/llms.txt`](https://docs.sigrex.io/llms.txt)), the OpenAPI
blocks of the API reference, the official
[TypeScript client](https://github.com/sigrexio/sigrex-client-ts), the
[contract ABIs](https://github.com/sigrexio/ABI), and the official
[agent plugin](https://github.com/sigrexio/agent-plugin). Where the docs are
silent (idempotency, slippage, response schemas, run cadence), the skills say
so instead of guessing.

Version 2.0 removes features that no longer exist in Sigrex (Telegram
Signals, the Pine Script Payload Builder) and documents current platform
state, such as prediction bots being temporarily disabled.

Trading actions are live and potentially irreversible. Every skill instructs
agents to create resources inactive, test with `TEST` signals, and ask for
explicit confirmation before activation, live signals, sharing, deletion or
funding. Sigrex does not offer backtesting.
